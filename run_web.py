import asyncio
from flask import Flask, jsonify, render_template, request
from app.agent.manus import Manus

app = Flask(__name__)
agent = None

def init_agent():
    global agent
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    agent = loop.run_until_complete(Manus.create())
    return loop

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/process", methods=["POST"])
def process():
    prompt = request.json.get("prompt", "")
    if not prompt.strip():
        return jsonify({"error": "Empty prompt provided"})

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    response = loop.run_until_complete(agent.run(prompt))
    return jsonify({"response": response})

if __name__ == "__main__":
    init_agent()
    app.run(host="0.0.0.0", port=8080)
