from flask import Flask, jsonify
import requests
import os
import json
import base64
from datetime import datetime

app = Flask(__name__)

GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
REPO = 'hechser/Time'
FILE_PATH = 'memory.json'
GITHUB_API_URL = f'https://api.github.com/repos/{REPO}/contents/{FILE_PATH}'
BRANCH = 'main'

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
    data = json.loads(content)
    tick = data['tick'] + 1
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    # Add your evolving logic here
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

@app.route('/update', methods=['POST'])
def tick():
    memory = get_current_memory()
    new_state, old_state = generate_next_tick(memory)
    commit = commit_new_memory(new_state, memory['sha'])
    return jsonify({'status': 'success', 'tick': new_state['tick'], 'commit': commit['commit']['html_url']})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
