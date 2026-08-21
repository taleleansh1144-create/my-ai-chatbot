import os
import sqlite3
import uuid

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# =========================================================
# GEMINI
# =========================================================

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found")

client = genai.Client(api_key=api_key)


# =========================================================
# FLASK
# =========================================================

app = Flask(__name__)


# =========================================================
# DATABASE
# =========================================================

# On Render, we will use /var/data for the persistent disk.
# Locally, this falls back to chat_history.db.

if os.path.exists("/var/data"):
    DATABASE = "/var/data/chat_history.db"
else:
    DATABASE = "chat_history.db"


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


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template("index.html")


# =========================================================
# GET CHAT HISTORY
# =========================================================

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


# =========================================================
# CREATE NEW CHAT
# =========================================================

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


# =========================================================
# LOAD ONE CHAT
# =========================================================

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


# =========================================================
# SEND MESSAGE
# =========================================================

@app.route("/chat", methods=["POST"])
def chat_message():

    data = request.get_json()

    user_message = data.get("message", "").strip()
    chat_id = data.get("chat_id")

    if not user_message:
        return jsonify({
            "reply": "Please type a message."
        }), 400

    # Create chat if none exists
    if not chat_id:

        chat_id = str(uuid.uuid4())

        db = get_db()

        db.execute(
            "INSERT INTO chats (id, title) VALUES (?, ?)",
            (chat_id, user_message[:40])
        )

        db.commit()
        db.close()

    # Save user message
    db = get_db()

    db.execute("""
        INSERT INTO messages
        (chat_id, role, content)
        VALUES (?, ?, ?)
    """, (
        chat_id,
        "user",
        user_message
    ))

    # Get previous conversation
    previous_messages = db.execute("""
        SELECT role, content
        FROM messages
        WHERE chat_id = ?
        ORDER BY id ASC
    """, (chat_id,)).fetchall()

    db.close()


    # =====================================================
    # BUILD GEMINI HISTORY
    # =====================================================

    history = []

    for message in previous_messages[:-1]:

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


    try:

        # New Gemini chat for this request
        gemini_chat = client.chats.create(
            model="gemini-3.6-flash",
            history=history
        )

        response = gemini_chat.send_message(
            message=user_message,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=700
            )
        )

        reply = response.text


        # =================================================
        # SAVE AI RESPONSE
        # =================================================

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

        # Update title from first message
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
            "reply": "Sorry, something went wrong.",
            "chat_id": chat_id
        }), 500


# =========================================================
# DELETE CHAT
# =========================================================

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


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
