import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

client = genai.Client(api_key=api_key)

app = Flask(__name__)

chat = client.chats.create(
    model="gemini-3.6-flash"
)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>My AI</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #212121;
            color: white;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }

        .header {
            padding: 18px;
            font-size: 20px;
            font-weight: bold;
            border-bottom: 1px solid #333;
        }

        .chat {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
        }

        .message {
            max-width: 800px;
            margin: 15px auto;
            padding: 14px 18px;
            border-radius: 12px;
            line-height: 1.5;
            white-space: pre-wrap;
        }

        .user {
            background: #343541;
        }

        .ai {
            background: #2b2b2b;
        }

        .input-area {
            padding: 15px;
            border-top: 1px solid #333;
        }

        .input-box {
            max-width: 800px;
            margin: auto;
            display: flex;
            gap: 10px;
        }

        input {
            flex: 1;
            padding: 15px;
            border-radius: 10px;
            border: none;
            outline: none;
            font-size: 16px;
        }

        button {
            padding: 0 20px;
            border: none;
            border-radius: 10px;
            background: #10a37f;
            color: white;
            font-size: 16px;
            cursor: pointer;
        }
    </style>
</head>

<body>

<div class="header">
    🤖 My AI
</div>

<div class="chat" id="chat">
    <div class="message ai">
        Hello! 👋 I'm your AI assistant. How can I help you?
    </div>
</div>

<div class="input-area">
    <div class="input-box">
        <input
            id="message"
            type="text"
            placeholder="Message My AI..."
            onkeydown="if(event.key === 'Enter') sendMessage()"
        >
        <button onclick="sendMessage()">Send</button>
    </div>
</div>

<script>
async function sendMessage() {

    const input = document.getElementById("message");
    const message = input.value.trim();

    if (!message) return;

    const chat = document.getElementById("chat");

    chat.innerHTML += `
        <div class="message user">${message}</div>
    `;

    input.value = "";

    const thinking = document.createElement("div");
    thinking.className = "message ai";
    thinking.innerText = "Thinking...";
    chat.appendChild(thinking);

    chat.scrollTop = chat.scrollHeight;

    try {

        const response = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: message
            })
        });

        const data = await response.json();

        thinking.innerText = data.reply;

    } catch (error) {

        thinking.innerText =
            "❌ Could not connect to the AI server.";

    }

    chat.scrollTop = chat.scrollHeight;
}
</script>

</body>
</html>
"""


@app.route("/")
def home():
    return HTML


@app.route("/chat", methods=["POST"])
def chat_message():

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "reply": "Please send a message."
            }), 400

        user_message = data.get("message", "").strip()

        if not user_message:
            return jsonify({
                "reply": "Please type a message."
            }), 400

        response = chat.send_message(
            message=user_message,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=500
            )
        )

        return jsonify({
            "reply": response.text
        })

    except Exception as e:

        print("Gemini error:", e)

        return jsonify({
            "reply": "Sorry, something went wrong with the AI."
        }), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
