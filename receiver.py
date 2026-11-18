import json
from flask import Flask, request

app = Flask(__name__)

@app.post("/report")
def report():
    data = request.get_json(force=True)
    with open("testreport.json", "w") as f:
        json.dump(data, f, indent=2)
    print("Report saved:", data["overall_status"], data["commit_sha"])
    return {"status": "saved"}, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)