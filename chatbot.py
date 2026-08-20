import os
from flask import Flask, render_template, request, jsonify
from google import genai

app = Flask(__name__)

# Get API key from Render Environment Variables
API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY environment variable is missing.")

client = genai.Client(api_key=API_KEY)

MODEL = "gemini-3.7-flash"


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()

        messages = data.get("messages", [])

        if not messages:
            return jsonify({
                "error": "No message received."
            }), 400

        # Build conversation for Gemini
        conversation = []

        for message in messages[-30:]:
            role = message.get("role")
            content = message.get("content", "").strip()

            if not content:
                continue

            if role == "user":
                conversation.append(
                    f"User: {content}"
                )

            elif role == "assistant":
                conversation.append(
                    f"Assistant: {content}"
                )

        prompt = "\n\n".join(conversation)

        prompt += """

Assistant:
"""

        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )

        answer = response.text

        return jsonify({
            "answer": answer
        })

    except Exception as e:

        print("Gemini error:", e)

        return jsonify({
            "error": str(e)
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
