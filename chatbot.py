import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

client = genai.Client(api_key=api_key)

app = Flask(
    __name__,
    template_folder=".",
    static_folder="static"
)

chat = client.chats.create(
    model="gemini-3.6-flash"
)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat_message():

    try:
        data = request.get_json()

        user_message = data.get("message", "").strip()

        if not user_message:
            return jsonify({
                "reply": "Please type a message."
            })

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

        print("Gemini Error:", e)

        return jsonify({
            "reply": "Sorry, HM AI could not process your message."
        }), 500


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
