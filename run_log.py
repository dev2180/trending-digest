"""Dated history of every run, committed back to the repo by the workflow.

logs/runs.csv                              one line per run (date, time, status, mode, model, top repo, note)
logs/history/YYYY/MM/YYYY-MM-DD.md         the day's digest, readable on GitHub
logs/history/YYYY/MM/YYYY-MM-DD.json       the same data, machine-readable
logs/state.json                            last successful send date (stops backup cron slots double-sending)
errors/YYYY/MM/YYYY-MM-DD_HHMMSS.log       traceback and context for any failed run
"""
import csv
import json
import os
import traceback
from datetime import datetime, timezone

LOG_DIR = os.getenv("LOG_DIR", "logs")
ERROR_DIR = os.getenv("ERROR_DIR", "errors")
CSV_FIELDS = ["date", "time_utc", "status", "mode", "model", "repos", "top_repo", "note"]


def _now():
    return datetime.now(timezone.utc)


def _month_dir(base, now):
    path = os.path.join(base, f"{now:%Y}", f"{now:%m}")
    os.makedirs(path, exist_ok=True)
    return path


def append_run(status, mode, model="", repos=None, note=""):
    now = _now()
    os.makedirs(LOG_DIR, exist_ok=True)
    path = os.path.join(LOG_DIR, "runs.csv")
    new = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if new:
            w.writeheader()
        w.writerow({"date": f"{now:%Y-%m-%d}", "time_utc": f"{now:%H:%M:%S}", "status": status, "mode": mode,
                    "model": model, "repos": len(repos or []),
                    "top_repo": repos[0]["name"] if repos else "", "note": note[:200]})


def write_history(repos, since, mode, model):
    now = _now()
    folder = _month_dir(os.path.join(LOG_DIR, "history"), now)
    stem = os.path.join(folder, f"{now:%Y-%m-%d}")
    clean = [{k: v for k, v in r.items() if k != "readme"} for r in repos]
    with open(stem + ".json", "w", encoding="utf-8") as f:
        json.dump({"date": f"{now:%Y-%m-%d}", "since": since, "mode": mode, "model": model, "repos": clean},
                  f, indent=2, ensure_ascii=False)
    lines = [f"# GitHub Trending · {now:%A %d %B %Y}", "",
             f"_{since} · {mode} · explained by {model or 'repo descriptions'}_", "",
             "| # | Repo | Language | Stars | Gained | Category |", "|---|---|---|---|---|---|"]
    lines += [f"| {i} | [{r['name']}]({r['url']}) | {r['language']} | {r['stars']:,} | {r['gained_n']:,} | {r.get('category', '')} |"
              for i, r in enumerate(repos, 1)]
    lines += [""] + [f"**{i}. {r['name']}** — {r['eli5']}\n" for i, r in enumerate(repos, 1)]
    with open(stem + ".md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return stem + ".md"


def write_error(exc, mode, stage):
    now = _now()
    path = os.path.join(_month_dir(ERROR_DIR, now), f"{now:%Y-%m-%d_%H%M%S}.log")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"time_utc: {now.isoformat()}\nmode: {mode}\nstage: {stage}\n"
                f"error: {type(exc).__name__}: {exc}\n")
        if os.getenv("GITHUB_RUN_URL"):
            f.write(f"run: {os.environ['GITHUB_RUN_URL']}\n")
        f.write("\n" + "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))
    return path


def mark_sent():
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(os.path.join(LOG_DIR, "state.json"), "w", encoding="utf-8") as f:
        json.dump({"last_sent": f"{_now():%Y-%m-%d}", "at": _now().isoformat()}, f, indent=2)
