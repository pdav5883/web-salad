from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
	return render_template("index.html")

@app.route("/ok/")
@app.route("/ok/<name>")
def ok(name="Jose"):
	return render_template("index.html", name=name)