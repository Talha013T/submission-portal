import json, os, smtplib, sys, urllib.request
from datetime import datetime, timezone
from email.message import EmailMessage

mode = sys.argv[1] if len(sys.argv) > 1 else "all"

raw = json.load(open("raw.json"))
summary = raw["summary"]

tests = []
for t in raw["tests"]:
    msg = None
    if t["outcome"] == "failed":
        msg = t.get("call", {}).get("crash", {}).get("message") or "Test failed"
    tests.append({"name": t["nodeid"], "result": t["outcome"], "failure_message": msg})

total = summary.get("total", 0)
passed = summary.get("passed", 0)
failed = summary.get("failed", 0)

report = {
    "repository": os.environ.get("GITHUB_REPOSITORY"),
    "branch": os.environ.get("GITHUB_REF_NAME"),
    "commit_sha": os.environ.get("GITHUB_SHA"),
    "pipeline_run_id": os.environ.get("GITHUB_RUN_ID"),
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "tests": tests,
    "total": total,
    "passed": passed,
    "failed": failed,
    "overall_status": "PASSED" if failed == 0 and total > 0 else "FAILED",
}

def send_receiver(r):
    req = urllib.request.Request(
        os.environ["REPORT_URL"],
        data=json.dumps(r).encode(),
        headers={"Content-Type": "application/json"},
    )
    print("Receiver:", urllib.request.urlopen(req, timeout=20).read().decode())

def send_email(r):
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASS")
    to = os.environ.get("MAIL_TO")
    if not (user and password and to):
        raise RuntimeError("SMTP_USER / SMTP_PASS / MAIL_TO not set")

    lines = [
        f"Overall result : {r['overall_status']}",
        f"Repository     : {r['repository']}",
        f"Branch         : {r['branch']}",
        f"Commit         : {r['commit_sha']}",
        f"Run ID         : {r['pipeline_run_id']}",
        f"Time (UTC)     : {r['timestamp']}",
        f"Total / Passed / Failed : {r['total']} / {r['passed']} / {r['failed']}",
        "",
        "Individual results:",
    ]
    for t in r["tests"]:
        line = f" - {t['name']}: {t['result'].upper()}"
        if t["failure_message"]:
            line += f"\n     Failure: {t['failure_message']}"
        lines.append(line)

    m = EmailMessage()
    m["Subject"] = f"[{r['overall_status']}] {r['repository']} @ {str(r['commit_sha'])[:7]}"
    m["From"] = user
    m["To"] = to
    m.set_content("\n".join(lines))
    m.add_attachment(json.dumps(r, indent=2).encode(),
                     maintype="application", subtype="json", filename="testreport.json")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as s:
        s.login(user, password)
        s.send_message(m)
    print("Email sent to", to)

errors = []
if mode in ("receiver", "all"):
    try:
        send_receiver(report)
    except Exception as e:
        print("Receiver failed:", e)
        errors.append("receiver")
if mode in ("email", "all"):
    try:
        send_email(report)
    except Exception as e:
        print("Email failed:", e)
        errors.append("email")

if errors:
    sys.exit(1)