import subprocess
import platform
import time
import threading
import json
import os

from datetime import datetime
from collections import defaultdict, deque


class Monitor:

    CONFIG_FILE = "ips.json"

    def __init__(self):

        self.lock = threading.Lock()

        self.history = defaultdict(lambda: deque(maxlen=10))
        self.status = {}

        self.targets = []

        self.IS_WINDOWS = platform.system().lower() == "windows"
        self.PARAM = "-n" if self.IS_WINDOWS else "-c"

        self.load_config()

    # ---------------- CONFIG ----------------

    def load_config(self):

        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, "r") as f:
                    self.targets = json.load(f)
            except Exception:
                self.targets = []

        if not self.targets:
            self.targets = [
                {"ip": "8.8.8.8", "label": "Google DNS"},
                {"ip": "1.1.1.1", "label": "Cloudflare DNS"}
            ]
            self.save_config()

    def save_config(self):

        with open(self.CONFIG_FILE, "w") as f:
            json.dump(self.targets, f, indent=2)

    # ---------------- IP MANAGEMENT ----------------

    def add_ip(self, ip):

        if not ip:
            return

        with self.lock:

            for item in self.targets:
                if item["ip"] == ip:
                    return

            self.targets.append({
                "ip": ip,
                "label": ""
            })

            self.save_config()

    def remove_ip(self, ip):

        with self.lock:

            self.targets = [
                x for x in self.targets
                if x["ip"] != ip
            ]

            self.status.pop(ip, None)
            self.history.pop(ip, None)

            self.save_config()

    def update_label(self, ip, label):

        with self.lock:

            for item in self.targets:
                if item["ip"] == ip:
                    item["label"] = label
                    break

            self.save_config()

    # ---------------- PING ----------------

    def ping(self, ip):

        try:

            if self.IS_WINDOWS:
                cmd = ["ping", "-n", "1", "-w", "1000", ip]
            else:
                cmd = ["ping", "-c", "1", "-W", "1", ip]

            result = subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=3
            )

            return result.returncode == 0

        except:
            return False

    # ---------------- LOOP ----------------

    def run(self):

        while True:

            with self.lock:
                targets_copy = list(self.targets)

            for target in targets_copy:

                ip = target["ip"]
                label = target.get("label", "")

                ok = self.ping(ip)

                with self.lock:

                    self.history[ip].append(
                        1 if ok else 0
                    )

                    data = list(self.history[ip])

                    consecutive_failures = (
                        len(data) >= 3 and
                        data[-3:] == [0, 0, 0]
                    )

                    is_down = consecutive_failures

                    previous_ok = self.status.get(
                        ip,
                        {}
                    ).get(
                        "ok",
                        True
                    )

                    self.status[ip] = {
                        "ip": ip,
                        "label": label,
                        "ok": not is_down,
                        "time": datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        "samples": len(data),
                        "recent_failures": data.count(0),
                        "alert": is_down
                    }

                    if previous_ok != (not is_down):
                        print(
                            f"{ip} -> "
                            f"{'DOWN' if is_down else 'UP'}"
                        )

            time.sleep(5)

    # ---------------- API ----------------

    def get_status(self):

        with self.lock:
            return {
                "ips": self.status
            }