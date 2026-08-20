import os
from flask import Flask, render_template, request, jsonify
from google import genai

app = Flask(__name__)

# Gemini API key from Render Environment Variables
API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is not set in Render Environment Variables."
    )

# Gemini client
client = genai.Client(api_key=API_KEY)

# Gemini model
MODEL = "gemini-3.7-flash"


# ---------------- HOME PAGE ----------------

@app.route("/")
def home():
    return render_template("index.html")


# ---------------- CHAT API ----------------

@app.route("/chat", methods=["POST"])
def chat():

    try:

        data = request.get_json()

        messages = data.get("messages", [])

        if not messages:
            return jsonify({
                "error": "No message received."
            }), 400


        # Keep the latest 30 messages
        messages = messages[-30:]


        # Convert chat history to Gemini prompt
        conversation = []

        for message in messages:

            role = message.get("role")
            content = message.get("content", "").strip()

            if not content:
                continue

            if role == "user":

                conversation.append(
                    "User: " + content
                )

            elif role == "assistant":

                conversation.append(
                    "Assistant: " + content
                )


        prompt = "\n\n".join(conversation)

        prompt += "\n\nAssistant:"


        # Ask Gemini
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )


        answer = response.text


        return jsonify({
            "answer": answer
        })


    except Exception as e:

        print("Gemini Error:", e)

        return jsonify({
            "error": str(e)
        }), 500


# ---------------- RUN SERVER ----------------

if __name__ == "__main__":

    port = int(
        os.environ.get("PORT", 5000)
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
