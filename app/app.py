"""A tiny Flask web app. It is the thing Jenkins builds, tests and deploys."""
import os
import socket

from flask import Flask, jsonify

app = Flask(__name__)

VERSION = os.getenv("APP_VERSION", "local")


@app.route("/")
def index():
    return (
        "<h1>Hello from Jenkins CI/CD!first change</h1>"
        f"<p>Build version: <b>{VERSION}</b></p>"
        f"<p>Container ID: <b>{socket.gethostname()}</b></p>"
    )


@app.route("/health")
def health():
    # Jenkins (and Docker) call this to check the app is alive.
    return jsonify(status="ok"), 200


@app.route("/api/info")
def info():
    return jsonify(app="jenkins-demo-app", version=VERSION)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
