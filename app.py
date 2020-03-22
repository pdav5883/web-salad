from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
	return render_template("index.html")

@app.route("/mdn2/")
def mdn():
    return render_template("mdn_index.html")

@app.route("/ok/")
@app.route("/ok/<name>")
def ok(name="Kelly"):
	return render_template("ok.html", name=name)


@app.route("/apple/")
def apple():
	return render_template("apple.html")