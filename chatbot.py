import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

# Get Gemini API key
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

# Connect to Gemini
client = genai.Client(api_key=api_key)

# Flask application
app = Flask(__name__)

# Create Gemini chat
chat = client.chats.create(
    model="gemini-3.6-flash"
)


# -----------------------------
# HOME PAGE
# -----------------------------

@app.route("/")
def home():
    return render_template("index.html")


# -----------------------------
# LOGO TEST
# -----------------------------

@app.route("/logo")
def logo():
    return app.send_static_file("hm-ai-logo.png")


# -----------------------------
# AI CHAT
# -----------------------------

@app.route("/chat", methods=["POST"])
def chat_message():

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "reply": "Please type a message."
            }), 400

        user_message = data.get("message", "").strip()

        if not user_message:
            return jsonify({
                "reply": "Please type a message."
            }), 400

        # Send message to Gemini
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
            "reply": "Sorry, something went wrong with HM AI."
        }), 500


# -----------------------------
# START SERVER
# -----------------------------

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
