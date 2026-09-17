"""
ScoreBot -- the heart of the netkoth.org-style scoring model.

Every POLL_INTERVAL seconds, GETs /tag from each machine's always-on
reporter (koth_reporter.py, port 9001 by default). Whatever token comes
back gets forwarded to the scoreboard, which resolves it to a team and
credits that team's points for this interval -- continuous, automatic,
no action required from any team beyond actually holding the machine.
"""
import time
import json
import os

import requests

MACHINES_FILE = os.environ.get('MACHINES_FILE', '/config/machines.json')
SCOREBOARD_URL = os.environ.get('SCOREBOARD_URL', 'http://scoreboard:8000')
SCOREBOT_SECRET = os.environ.get('SCOREBOT_SECRET', 'change-me-scorebot-secret')
POLL_INTERVAL = int(os.environ.get('POLL_INTERVAL', '30'))


def load_machines():
    with open(MACHINES_FILE) as f:
        return json.load(f)


def poll_once(machines):
    results = {}
    for m in machines:
        token = None
        try:
            r = requests.get(f"http://{m['ip']}:{m.get('port', 9001)}/tag", timeout=3)
            tag = r.text.strip()
            if tag and tag != 'unclaimed':
                token = tag
        except requests.RequestException:
            token = None  # machine unreachable this poll -- treat as unclaimed, don't crash the loop

        results[m['name']] = {'token': token, 'points': m.get('points', 1)}
        print(f"[scorebot] {m['name']} ({m['ip']}) -> {token or 'unclaimed'}", flush=True)

    try:
        resp = requests.post(
            f"{SCOREBOARD_URL}/internal/poll_result",
            json={'results': results},
            headers={'X-Scorebot-Secret': SCOREBOT_SECRET},
            timeout=5,
        )
        if resp.status_code != 200:
            print(f"[scorebot] scoreboard rejected report: {resp.status_code} {resp.text}", flush=True)
    except requests.RequestException as e:
        print(f"[scorebot] failed to reach scoreboard: {e}", flush=True)


if __name__ == '__main__':
    machines = load_machines()
    print(f"[scorebot] polling {len(machines)} machines every {POLL_INTERVAL}s", flush=True)
    while True:
        poll_once(machines)
        time.sleep(POLL_INTERVAL)
