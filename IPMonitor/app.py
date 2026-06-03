from flask import Flask, jsonify, request, render_template
import threading
import socket

from monitor import Monitor

app = Flask(__name__)

monitor = Monitor()

HOST_IP = socket.gethostbyname(socket.gethostname())


def is_host():
    return request.remote_addr in (
        "127.0.0.1",
        "::1",
        HOST_IP
    )


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/me")
def me():
    return jsonify({
        "is_host": is_host()
    })


@app.route("/api/ips")
def get_ips():
    return jsonify(
        monitor.get_status()
    )


@app.route("/api/add", methods=["POST"])
def add_ip():

    ip = request.json.get("ip")

    monitor.add_ip(ip)

    return jsonify({
        "ok": True
    })


@app.route("/api/remove", methods=["POST"])
def remove_ip():

    if not is_host():
        return jsonify({
            "ok": False,
            "error": "Only the host machine can remove IPs"
        }), 403

    ip = request.json.get("ip")

    monitor.remove_ip(ip)

    return jsonify({
        "ok": True
    })


@app.route("/api/label", methods=["POST"])
def update_label():

    ip = request.json.get("ip")
    label = request.json.get("label")

    monitor.update_label(
        ip,
        label
    )

    return jsonify({
        "ok": True
    })


if __name__ == "__main__":

    threading.Thread(
        target=monitor.run,
        daemon=True
    ).start()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )