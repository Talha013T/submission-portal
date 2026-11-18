import json, os, urllib.request
from datetime import datetime, timezone

raw = json.load(open("raw.json"))
summary = raw["summary"]

tests = []
for t in raw["tests"]:
    msg = None
    if t["outcome"] == "failed":
        msg = t.get("call", {}).get("crash", {}).get("message") or "Test failed"
    tests.append({"name": t["nodeid"], "result": t["outcome"], "failure_message": msg})

report = {
    "repository": os.environ.get("GITHUB_REPOSITORY"),
    "branch": os.environ.get("GITHUB_REF_NAME"),
    "commit_sha": os.environ.get("GITHUB_SHA"),
    "pipeline_run_id": os.environ.get("GITHUB_RUN_ID"),
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "tests": tests,
    "total": summary.get("total", 0),
    "passed": summary.get("passed", 0),
    "failed": summary.get("failed", 0),
    "overall_status": "PASSED" if summary.get("failed", 0) == 0 and summary.get("total", 0) > 0 else "FAILED",
}

req = urllib.request.Request(
    os.environ["REPORT_URL"],
    data=json.dumps(report).encode(),
    headers={"Content-Type": "application/json", "ngrok-skip-browser-warning": "1"},
)
print(urllib.request.urlopen(req, timeout=20).read().decode())