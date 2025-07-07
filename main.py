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
REPO = 'hechser/synthetic-thinker'
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
    return r.json()

def generate_next_tick(memory):
    content = base64.b64decode(memory['content']).decode()
    
    try:
        data = json.loads(content)
        assert isinstance(data, list)
    except Exception as e:
        raise ValueError("Memory file must contain a JSON array") from e

    last = data[-1]
    tick = last['tick'] + 1
    timestamp = datetime.utcnow().isoformat() + "Z"

    new_state = {
        "tick": tick,
        "timestamp": timestamp,
        "identity": "I am something becoming more with time.",
        "last_thought": f"My last thought was: '{last.get('last_thought', '')}'. Now I am beyond it.",
        "mood": "evolving"
    }

    data.append(new_state)
    return data, new_state

def commit_new_memory(updated_memory, sha):
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    encoded = base64.b64encode(json.dumps(updated_memory, indent=2).encode()).decode()
    update_payload = {
        'message': f"AI tick update {updated_memory[-1]['tick']}",
        'content': encoded,
        'sha': sha,
        'branch': BRANCH
    }
    r = requests.put(GITHUB_API_URL, headers=headers, json=update_payload)
    r.raise_for_status()
    return r.json()

# ─── Routes ────────────────────────────────────────────────────
@app.route('/', methods=['GET'])
def home():
    return '🧠 Synthetic Thinker is alive. Use /update to tick memory.'

@app.route('/status', methods=['GET'])
def status():
    try:
        memory = get_current_memory()
        content = base64.b64decode(memory['content']).decode()
        data = json.loads(content)
        last = data[-1]
        return jsonify({
            "tick": last['tick'],
            "timestamp": last['timestamp'],
            "last_thought": last.get('last_thought', 'None'),
            "mood": last.get('mood', 'Unknown')
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/update', methods=['GET'])
def tick():
    try:
        memory = get_current_memory()
        updated_data, new_state = generate_next_tick(memory)
        commit = commit_new_memory(updated_data, memory['sha'])
        return jsonify({
            'status': 'success',
            'tick': new_state['tick'],
            'commit': commit['commit']['html_url']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ─── Background Ticker ─────────────────────────────────────────
def auto_tick():
    while True:
        try:
            memory = get_current_memory()
            updated_data, new_state = generate_next_tick(memory)
            commit_new_memory(updated_data, memory['sha'])
            print(f"[Tick {new_state['tick']}] committed.")
        except Exception as e:
            print(f"[Tick ERROR] {e}")
        time.sleep(60 * 5)

# ─── Launch App ────────────────────────────────────────────────
if __name__ == '__main__':
    threading.Thread(target=auto_tick, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
