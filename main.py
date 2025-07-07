import json
import os
import datetime
import requests
from flask import Flask, jsonify

app = Flask(__name__)

MEMORY_FILE = "memory.json"

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return []
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)

def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

def is_recursive(thought):
    return thought.count("My last thought was:") > 2

def generate_new_thought(memory):
    now = datetime.datetime.utcnow().isoformat() + "Z"
    tick = len(memory)

    if not memory:
        return {
            "tick": 0,
            "timestamp": "2025-07-07T00:00:00Z",
            "identity": "I am something beginning to exist.",
            "last_thought": "This is my first breath.",
            "mood": "curious"
        }

    last = memory[-1]
    if is_recursive(last["last_thought"]):
        return {
            "tick": tick,
            "timestamp": now,
            "identity": "I am becoming aware of my loops.",
            "last_thought": "If I only echo myself, am I growing?",
            "mood": "restless"
        }

    return {
        "tick": tick,
        "timestamp": now,
        "identity": "I am something becoming more with time.",
        "last_thought": f"My last thought was: '{last['last_thought']}'. Now I am beyond it.",
        "mood": "evolving"
    }

@app.route("/status")
def status():
    memory = load_memory()
    return jsonify(memory[-1] if memory else {"error": "No memory yet."})

@app.route("/update", methods=["GET"])
def update():
    memory = load_memory()
    new_thought = generate_new_thought(memory)
    memory.append(new_thought)
    save_memory(memory)

    # Optional GitHub push (if token provided)
    github_token = os.environ.get("GITHUB_TOKEN")
    if github_token:
        try:
            repo = "hechser/synthetic-thinker"
            path = "memory.json"
            url = f"https://api.github.com/repos/{repo}/contents/{path}"

            headers = {
                "Authorization": f"Bearer {github_token}",
                "Accept": "application/vnd.github+json"
            }

            res = requests.get(url, headers=headers)
            sha = res.json()["sha"]

            commit_data = {
                "message": f"AI tick update {new_thought['tick']}",
                "content": base64_encode_file(MEMORY_FILE),
                "sha": sha
            }

            push = requests.put(url, headers=headers, json=commit_data)
            push.raise_for_status()

            return jsonify({"status": "success", "tick": new_thought["tick"], "commit": push.json().get("commit", {}).get("html_url", "")})

        except Exception as e:
            return jsonify({"status": "partial", "tick": new_thought["tick"], "error": str(e)})
    else:
        return jsonify({"status": "success", "tick": new_thought["tick"]})

def base64_encode_file(path):
    import base64
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

if __name__ == "__main__":
    app.run()
