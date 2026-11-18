import json, os
from urllib.parse import urlparse
from flask import Flask, request, render_template_string

app = Flask(__name__)
app.config["DATA_FILE"] = os.environ.get("DATA_FILE", "submissions.json")

PAGE = """
<h2>Assignment Submission Portal</h2>
{% if error %}<p style="color:red">{{ error }}</p>{% endif %}
{% if ok %}<p style="color:green">{{ ok }}</p>{% endif %}
<form method="post" action="/submit">
  Name: <input name="name"><br>
  Reg No: <input name="reg_no"><br>
  Assignment Title: <input name="title"><br>
  Submission URL: <input name="url"><br>
  <button type="submit">Submit</button>
</form>
<h3>Saved Submissions</h3>
<ul>
{% for s in subs %}
  <li>{{ s.name }} | {{ s.reg_no }} | {{ s.title }} | <a href="{{ s.url }}">{{ s.url }}</a></li>
{% endfor %}
</ul>
"""

def load():
    try:
        with open(app.config["DATA_FILE"]) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save(subs):
    with open(app.config["DATA_FILE"], "w") as f:
        json.dump(subs, f, indent=2)

def valid_url(u):
    p = urlparse(u)
    return p.scheme in ("http", "https") and bool(p.netloc) and " " not in u

@app.get("/")
def index():
    return render_template_string(PAGE, subs=load())

@app.post("/submit")
def submit():
    data = {k: request.form.get(k, "").strip() for k in ("name", "reg_no", "title", "url")}
    for field, label in (("name", "Name"), ("reg_no", "Registration number"),
                         ("title", "Assignment title"), ("url", "Submission URL")):
        if not data[field]:
            return render_template_string(PAGE, subs=load(), error=f"{label} is required"), 400
    if not valid_url(data["url"]):
        return render_template_string(PAGE, subs=load(), error="Invalid submission URL"), 400
    subs = load()
    subs.append(data)
    save(subs)
    return render_template_string(PAGE, subs=subs, ok="Submission saved")

if __name__ == "__main__":
    app.run(port=8000, debug=True)