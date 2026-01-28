from flask import Flask, request, jsonify
from ollama import Client

app = Flask(__name__)

# Connect to Ollama running on Ubuntu server
client = Client(host="http://192.168.1.13:11434")
PORT = 5001

@app.route("/ask", methods=["GET"])
def ask_model():
    prompt = request.args.get("p")

    if not prompt:
        return jsonify({"error": "Missing 'prompt' parameter"}), 400

    try:
        response = client.chat(
            model="deepseek-r1:1.5b",
            messages=[{"role": "user", "content": prompt}]
        )

        return jsonify({
            "model": "deepseek-r1:1.5b",
            "prompt": prompt,
            "response": response["message"]["content"]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)


""" From terminal:
curl "http://YOUR_PC_IP:5000/ask?p=How does photosynthesis work?"

Example JSON response:
{
  "model": "deepseek-r1:1.5b",
  "prompt": "How does photosynthesis work?",
  "response": "Photosynthesis is the process where plants convert sunlight..."
} """

# source ../ai_agent_project/venv/bin/activate
# python3 ask_agent_server.py