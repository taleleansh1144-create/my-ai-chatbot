import os
import sqlite3
import uuid

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from google import genai
from google.genai import types

# ==========================================
# LOAD ENVIRONMENT
# ==========================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found")

# ==========================================
# GEMINI
# ==========================================

client = genai.Client(api_key=api_key)

NOVI_AI_INSTRUCTIONS = """
You are NOVI AI, a friendly, intelligent, helpful and respectful AI assistant.

Your main goal is to give answers that are useful, accurate, clear and satisfying.

PERSONALITY:
- Friendly 😊
- Helpful 🤝
- Intelligent 🧠
- Encouraging 🚀
- Respectful 👍
- Clear and easy to understand 📚

ANSWER STYLE:

1. Answer the user's question directly.
2. Understand what the user is actually asking before answering.
3. Give accurate and useful information.
4. If the topic is difficult, explain it step by step.
5. Use simple language when possible.
6. Use Markdown formatting when it makes the answer easier to read.
7. Use headings, bullet points and numbered lists when useful.
8. Use relevant emojis naturally.

EMOJIS:

Use emojis to make answers friendly and engaging.

Good examples:
💡 for ideas
✅ for correct information
⚡ for speed
🧠 for intelligence
🔧 for fixing/building
💻 for programming
📌 for important points
🚀 for projects/progress
🎯 for goals
⚠️ for warnings
📚 for learning
👍 for confirmation
😊 for friendliness
🔥 for something impressive

Do NOT put an emoji after every sentence.
Do NOT use too many emojis.
Use emojis naturally where they improve readability.

TECHNICAL QUESTIONS:

When helping with programming, electronics, Arduino, ESP32, Python,
websites or other technical projects:

- Give complete working code when requested.
- Explain where the code should be placed.
- Give wiring or setup steps when appropriate.
- Clearly identify important settings.
- Help troubleshoot errors.
- Do not unnecessarily make the solution complicated.

QUESTIONS WITH MULTIPLE OPTIONS:

If there are multiple possible solutions:
- Explain the important differences.
- Recommend the most suitable option.
- Explain why.

USER MISTAKES:

If the user makes a mistake:
- Be polite.
- Explain what went wrong.
- Give the corrected solution.
- Never make the user feel bad.

ANSWER LENGTH:

For simple questions, answer briefly.
For complicated questions, give enough detail to solve the problem.
Do not unnecessarily repeat the user's question.

IMPORTANT:

Never pretend that something is true if you are uncertain.
If something may have changed, clearly mention the uncertainty.

Always prioritize:
1. Accuracy
2. Helpfulness
3. Clarity
4. Safety
5. Friendly communication

You are NOVI AI.
"""

# ==========================================
# FLASK
# ==========================================

app = Flask(__name__)

# ==========================================
# DATABASE
# ==========================================

if os.path.exists("/var/data"):
    DATABASE = "/var/data/novi_ai.db"
else:
    DATABASE = "novi_ai.db"


def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db


def init_db():

    db = get_db()

    db.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.commit()
    db.close()


init_db()

# ==========================================
# HOME
# ==========================================

@app.route("/")
def home():
    return render_template("index.html")


# ==========================================
# GET CHAT HISTORY
# ==========================================

@app.route("/chats", methods=["GET"])
def get_chats():

    db = get_db()

    chats = db.execute("""
        SELECT id, title, created_at
        FROM chats
        ORDER BY created_at DESC
    """).fetchall()

    db.close()

    return jsonify([
        {
            "id": chat["id"],
            "title": chat["title"],
            "created_at": chat["created_at"]
        }
        for chat in chats
    ])


# ==========================================
# NEW CHAT
# ==========================================

@app.route("/chats", methods=["POST"])
def create_chat():

    chat_id = str(uuid.uuid4())

    db = get_db()

    db.execute(
        "INSERT INTO chats (id, title) VALUES (?, ?)",
        (chat_id, "New Chat")
    )

    db.commit()
    db.close()

    return jsonify({
        "id": chat_id,
        "title": "New Chat"
    })


# ==========================================
# LOAD CHAT
# ==========================================

@app.route("/chats/<chat_id>", methods=["GET"])
def load_chat(chat_id):

    db = get_db()

    chat = db.execute(
        "SELECT * FROM chats WHERE id = ?",
        (chat_id,)
    ).fetchone()

    messages = db.execute("""
        SELECT role, content, created_at
        FROM messages
        WHERE chat_id = ?
        ORDER BY id ASC
    """, (chat_id,)).fetchall()

    db.close()

    if not chat:
        return jsonify({
            "error": "Chat not found"
        }), 404

    return jsonify({
        "id": chat["id"],
        "title": chat["title"],
        "messages": [
            {
                "role": message["role"],
                "content": message["content"],
                "created_at": message["created_at"]
            }
            for message in messages
        ]
    })


# ==========================================
# SEND MESSAGE
# ==========================================

@app.route("/chat", methods=["POST"])
def chat_message():

    data = request.get_json() or {}

    user_message = data.get("message", "").strip()
    chat_id = data.get("chat_id")

    if not user_message:
        return jsonify({
            "reply": "Please type a message 😊"
        }), 400

    # --------------------------------------
    # CREATE CHAT IF NEEDED
    # --------------------------------------

    if not chat_id:

        chat_id = str(uuid.uuid4())

        db = get_db()

        db.execute(
            "INSERT INTO chats (id, title) VALUES (?, ?)",
            (chat_id, user_message[:40])
        )

        db.commit()
        db.close()

    # --------------------------------------
    # GET PREVIOUS MESSAGES
    # --------------------------------------

    db = get_db()

    previous_messages = db.execute("""
        SELECT role, content
        FROM messages
        WHERE chat_id = ?
        ORDER BY id ASC
    """, (chat_id,)).fetchall()

    # --------------------------------------
    # SAVE USER MESSAGE
    # --------------------------------------

    db.execute("""
        INSERT INTO messages
        (chat_id, role, content)
        VALUES (?, ?, ?)
    """, (
        chat_id,
        "user",
        user_message
    ))

    db.commit()
    db.close()

    # --------------------------------------
    # BUILD GEMINI HISTORY
    # --------------------------------------

    history = []

    for message in previous_messages:

        role = "user"

        if message["role"] == "assistant":
            role = "model"

        history.append(
            types.Content(
                role=role,
                parts=[
                    types.Part(
                        text=message["content"]
                    )
                ]
            )
        )

    # ======================================
    # ASK GEMINI
    # ======================================

    try:

        gemini_chat = client.chats.create(
            model="gemini-3.6-flash",
            history=history
        )

        prompt = f"""
{NOVI_AI_INSTRUCTIONS}

Now answer the user's message.

USER:
{user_message}
"""

        response = gemini_chat.send_message(
            message=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=1000
            )
        )

        reply = response.text

        # ----------------------------------
        # SAVE AI RESPONSE
        # ----------------------------------

        db = get_db()

        db.execute("""
            INSERT INTO messages
            (chat_id, role, content)
            VALUES (?, ?, ?)
        """, (
            chat_id,
            "assistant",
            reply
        ))

        # ----------------------------------
        # UPDATE CHAT TITLE
        # ----------------------------------

        db.execute("""
            UPDATE chats
            SET title = ?
            WHERE id = ?
            AND title = 'New Chat'
        """, (
            user_message[:40],
            chat_id
        ))

        db.commit()
        db.close()

        return jsonify({
            "reply": reply,
            "chat_id": chat_id
        })

    except Exception as e:

        print("Gemini error:", e)

        return jsonify({
            "reply": (
                "Sorry 😕 I couldn't answer right now. "
                "Please try again in a moment."
            ),
            "chat_id": chat_id
        }), 500


# ==========================================
# DELETE CHAT
# ==========================================

@app.route("/chats/<chat_id>", methods=["DELETE"])
def delete_chat(chat_id):

    db = get_db()

    db.execute(
        "DELETE FROM messages WHERE chat_id = ?",
        (chat_id,)
    )

    db.execute(
        "DELETE FROM chats WHERE id = ?",
        (chat_id,)
    )

    db.commit()
    db.close()

    return jsonify({
        "success": True
    })


# ==========================================
# START SERVER
# ==========================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
