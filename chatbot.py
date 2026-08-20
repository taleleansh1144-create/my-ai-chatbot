from flask import Flask, render_template, request, jsonify
import sqlite3
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=API_KEY)

DB_NAME = "chats.db"


# ---------------- DATABASE ----------------

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(chat_id) REFERENCES chats(id)
        )
    """)

    conn.commit()
    conn.close()


# ---------------- HOME ----------------

@app.route("/")
def home():
    return render_template("index.html")


# ---------------- GET CHATS ----------------

@app.route("/api/chats")
def get_chats():

    conn = get_db()

    chats = conn.execute("""
        SELECT * FROM chats
        ORDER BY created_at DESC
    """).fetchall()

    conn.close()

    return jsonify([
        {
            "id": chat["id"],
            "title": chat["title"]
        }
        for chat in chats
    ])


# ---------------- CREATE CHAT ----------------

@app.route("/api/chats", methods=["POST"])
def create_chat():

    data = request.json

    title = data.get("title", "New Chat")

    conn = get_db()

    cursor = conn.execute(
        "INSERT INTO chats (title) VALUES (?)",
        (title,)
    )

    chat_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return jsonify({
        "id": chat_id,
        "title": title
    })


# ---------------- GET MESSAGES ----------------

@app.route("/api/chats/<int:chat_id>")
def get_messages(chat_id):

    conn = get_db()

    messages = conn.execute("""
        SELECT role, content
        FROM messages
        WHERE chat_id = ?
        ORDER BY id ASC
    """, (chat_id,)).fetchall()

    conn.close()

    return jsonify([
        {
            "role": message["role"],
            "content": message["content"]
        }
        for message in messages
    ])


# ---------------- SEND MESSAGE ----------------

@app.route("/api/chat", methods=["POST"])
def chat():

    data = request.json

    chat_id = data.get("chat_id")
    message = data.get("message")

    if not chat_id or not message:
        return jsonify({"error": "Missing chat ID or message"}), 400

    conn = get_db()

    # Save user message
    conn.execute("""
        INSERT INTO messages (chat_id, role, content)
        VALUES (?, ?, ?)
    """, (chat_id, "user", message))

    # Get previous conversation
    history = conn.execute("""
        SELECT role, content
        FROM messages
        WHERE chat_id = ?
        ORDER BY id ASC
    """, (chat_id,)).fetchall()

    conn.commit()

    # Create Gemini conversation text
    prompt = ""

    for item in history:
        if item["role"] == "user":
            prompt += f"User: {item['content']}\n"
        else:
            prompt += f"Assistant: {item['content']}\n"

    prompt += "Assistant:"

    try:

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        answer = response.text

    except Exception as e:

        conn.close()

        return jsonify({
            "error": str(e)
        }), 500

    # Save AI response
    conn.execute("""
        INSERT INTO messages (chat_id, role, content)
        VALUES (?, ?, ?)
    """, (chat_id, "assistant", answer))

    # Automatically change title from first message
    first_message = conn.execute("""
        SELECT content
        FROM messages
        WHERE chat_id = ?
        ORDER BY id ASC
        LIMIT 1
    """, (chat_id,)).fetchone()

    if first_message:

        title = first_message["content"][:35]

        conn.execute("""
            UPDATE chats
            SET title = ?
            WHERE id = ?
        """, (title, chat_id))

    conn.commit()
    conn.close()

    return jsonify({
        "answer": answer
    })


# ---------------- DELETE CHAT ----------------

@app.route("/api/chats/<int:chat_id>", methods=["DELETE"])
def delete_chat(chat_id):

    conn = get_db()

    conn.execute(
        "DELETE FROM messages WHERE chat_id = ?",
        (chat_id,)
    )

    conn.execute(
        "DELETE FROM chats WHERE id = ?",
        (chat_id,)
    )

    conn.commit()
    conn.close()

    return jsonify({"success": True})


# ---------------- RUN ----------------

if __name__ == "__main__":

    init_db()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
