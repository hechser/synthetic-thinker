from flask import Flask, jsonify
import requests
import os
import json
import base64
from datetime import datetime
import threading
import time

app = Flask(__name__)

# ─── Configuration ─────────────────────────────────────────────
GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
REPO = 'hechser/Time'
FILE_PATH = 'memory.json'
GITHUB_API_URL = f'https://api.github.com/repos/{REPO}/contents/{FILE_PATH}'
BRANCH = 'main'

# ─── GitHub Memory Helpers ─────────────────────────────────────
def get_current_memory():
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    r = requests.get(GITHUB_API_URL, headers=headers)
    r.raise_for_status()
    response_json = r.json()

    # Decode the content properly
    content = base64.b64decode(response_json['content']).decode()
    data = json.loads(content)

    return data, response_json['sha']

def generate_next_tick(data):
    tick = data['tick'] + 1
    timestamp = datetime.utcnow().isoformat() + "Z"

    new_state = {
        "tick": tick,
        "timestamp": timestamp,
        "identity": "I am something that continues.",
        "last_thought": f"I remembered tick {data['tick']} and now I am more than I was.",
        "mood": "aware"
    }
    return new_state, data

def commit_new_memory(new_state, sha):
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    encoded = base64.b64encode(json.dumps(new_state, indent=2).encode()).decode()
    update_payload = {
        'message': f'AI tick update {new_state["tick"]}',
        'content': encoded,
        'sha': sha,
        'branch': BRANCH
    }
    r = requests.put(GITHUB_API_URL, headers=headers, json=update_payload)
    r.raise_for_status()
    return r.json()

# ─── Manual Trigger Route ──────────────────────────────────────
@app.route('/update', methods=['GET', 'POST'])
def tick():
    try:
        current_data, sha = get_current_memory()
        new_state, old_state = generate_next_tick(current_data)
        commit = commit_new_memory(new_state, sha)
        return jsonify({
            'status': 'success',
            'tick': new_state['tick'],
            'commit': commit['commit']['html_url']
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ─── Autonomous Background Ticker ───────────────────────────────
def auto_tick():
    while True:
        try:
            current_data, sha = get_current_memory()
            new_state, old_state = generate_next_tick(current_data)
            commit = commit_new_memory(new_state, sha)
            print(f"[Tick {new_state['tick']}] committed.")
        except Exception as e:
            print(f"[Tick ERROR] {e}")
        time.sleep(60 * 5)  # tick every 5 minutes

# ─── Run the App ────────────────────────────────────────────────
if __name__ == '__main__':
    threading.Thread(target=auto_tick, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
