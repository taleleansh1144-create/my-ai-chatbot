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
<html lang="en">

<head>

    <meta charset="UTF-8">

    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

    <title>🤖 HM AI</title>

    <style>

        * {
            box-sizing: border-box;
        }

        html,
        body {
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
        }

        body {
            font-family: Arial, Helvetica, sans-serif;
            background:
                radial-gradient(
                    circle at top,
                    #101b3d 0%,
                    #050814 45%,
                    #02030a 100%
                );
            color: white;
            overflow: hidden;
        }

        /* MAIN APP */

        .app {
            width: 100%;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }

        /* HEADER */

        .header {
            height: 125px;
            border-bottom: 1px solid rgba(80, 140, 255, 0.45);

            background:
                linear-gradient(
                    90deg,
                    rgba(0, 180, 255, 0.08),
                    rgba(130, 60, 255, 0.10)
                );

            display: flex;
            align-items: center;
            padding: 15px 35px;

            box-shadow:
                0 0 25px rgba(0, 120, 255, 0.12);
        }

        .logo {
            width: 90px;
            height: 90px;
            border-radius: 50%;
            object-fit: cover;

            box-shadow:
                0 0 20px rgba(0, 200, 255, 0.5),
                0 0 35px rgba(150, 50, 255, 0.3);
        }

        .brand {
            margin-left: 25px;
        }

        .brand-name {
            font-size: 42px;
            font-weight: bold;

            background:
                linear-gradient(
                    90deg,
                    #00d9ff,
                    #4169ff,
                    #bd4dff
                );

            -webkit-background-clip: text;
            color: transparent;
        }

        .brand-title {
            font-size: 16px;
            letter-spacing: 6px;
            margin-top: 5px;
            color: white;
        }

        .brand-subtitle {
            margin-top: 10px;
            color: #aeb7ce;
            letter-spacing: 2px;
            font-size: 13px;
        }

        /* CHAT */

        .chat {
            flex: 1;
            overflow-y: auto;
            padding: 35px 5%;
            scroll-behavior: smooth;
        }

        .message-row {
            display: flex;
            margin-bottom: 28px;
            width: 100%;
        }

        .message-row.user {
            justify-content: flex-end;
        }

        .avatar {
            width: 45px;
            height: 45px;
            border-radius: 50%;
            object-fit: cover;
            margin-right: 14px;

            box-shadow:
                0 0 15px rgba(0, 180, 255, 0.4);
        }

        .message-content {
            max-width: 75%;
        }

        .message {
            padding: 18px 22px;
            border-radius: 18px;

            font-size: 16px;
            line-height: 1.7;

            white-space: pre-wrap;

            border: 1px solid rgba(100, 130, 180, 0.3);
        }

        .ai-message {
            background:
                linear-gradient(
                    135deg,
                    rgba(25, 35, 55, 0.95),
                    rgba(13, 20, 35, 0.95)
                );

            box-shadow:
                0 5px 25px rgba(0, 0, 0, 0.3);
        }

        .user-message {
            background:
                linear-gradient(
                    135deg,
                    #4040a8,
                    #7138b8
                );

            border-color: rgba(140, 110, 255, 0.7);

            box-shadow:
                0 0 20px rgba(100, 60, 255, 0.2);
        }

        .time {
            color: #8992aa;
            font-size: 12px;
            margin-top: 7px;
            margin-left: 12px;
        }

        .user .time {
            text-align: right;
            margin-right: 12px;
        }

        /* INPUT */

        .bottom {
            padding: 15px 4% 20px;

            background:
                linear-gradient(
                    transparent,
                    rgba(3, 7, 20, 0.95)
                );
        }

        .input-container {
            max-width: 1100px;
            margin: auto;

            display: flex;
            align-items: center;

            border: 1px solid rgba(80, 140, 255, 0.65);

            border-radius: 22px;

            background:
                rgba(13, 22, 43, 0.95);

            box-shadow:
                0 0 25px rgba(0, 120, 255, 0.12);

            padding: 8px 10px 8px 20px;
        }

        #message {
            flex: 1;

            background: transparent;

            border: none;
            outline: none;

            color: white;

            font-size: 16px;

            padding: 15px;
        }

        #message::placeholder {
            color: #7d879d;
        }

        .send {
            width: 58px;
            height: 52px;

            border: none;
            border-radius: 15px;

            cursor: pointer;

            font-size: 25px;

            color: white;

            background:
                linear-gradient(
                    135deg,
                    #3658ff,
                    #8b38ff
                );

            box-shadow:
                0 0 20px rgba(90, 70, 255, 0.4);

            transition: 0.2s;
        }

        .send:hover {
            transform: scale(1.05);
        }

        .send:active {
            transform: scale(0.95);
        }

        .footer {
            text-align: center;
            color: #69738a;
            font-size: 12px;
            padding-top: 12px;
        }

        /* MOBILE */

        @media (max-width: 700px) {

            .header {
                height: 90px;
                padding: 10px 15px;
            }

            .logo {
                width: 65px;
                height: 65px;
            }

            .brand {
                margin-left: 12px;
            }

            .brand-name {
                font-size: 27px;
            }

            .brand-title {
                font-size: 9px;
                letter-spacing: 3px;
            }

            .brand-subtitle {
                display: none;
            }

            .chat {
                padding: 20px 12px;
            }

            .message-content {
                max-width: 85%;
            }

            .message {
                font-size: 15px;
                padding: 14px 16px;
            }

            .avatar {
                width: 38px;
                height: 38px;
            }

            .bottom {
                padding: 10px;
            }

            .input-container {
                border-radius: 17px;
            }

            #message {
                font-size: 15px;
                padding: 10px;
            }

            .send {
                width: 48px;
                height: 45px;
                font-size: 20px;
            }
        }

    </style>

</head>


<body>

<div class="app">

    <!-- HEADER -->

    <div class="header">

        <img
            class="logo"
            src="/static/hm-ai-logo.png"
            alt="HM AI Logo"
        >

        <div class="brand">

            <div class="brand-name">
                HM AI
            </div>

            <div class="brand-title">
                HUMAN MADE AI
            </div>

            <div class="brand-subtitle">
                MADE BY HUMAN, DESIGNED FOR FUTURE
            </div>

        </div>

    </div>


    <!-- CHAT -->

    <div class="chat" id="chat">

        <div class="message-row">

            <img
                class="avatar"
                src="/static/hm-ai-logo.png"
            >

            <div class="message-content">

                <div class="message ai-message">
                    Hello! 👋
                    <br>
                    I'm HM AI. How can I help you today?
                </div>

                <div class="time">
                    HM AI
                </div>

            </div>

        </div>

    </div>


    <!-- INPUT -->

    <div class="bottom">

        <div class="input-container">

            <input
                id="message"
                type="text"
                placeholder="Message HM AI..."
                autocomplete="off"
            >

            <button
                class="send"
                onclick="sendMessage()"
            >
                ➤
            </button>

        </div>

        <div class="footer">
            © 2026 HM AI. All rights reserved.
        </div>

    </div>

</div>


<script>

const input = document.getElementById("message");

const chatBox = document.getElementById("chat");


input.addEventListener("keydown", function(event) {

    if (event.key === "Enter") {

        event.preventDefault();

        sendMessage();

    }

});


function getTime() {

    const now = new Date();

    return now.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit"
    });

}


function escapeHTML(text) {

    const div = document.createElement("div");

    div.textContent = text;

    return div.innerHTML;

}


async function sendMessage() {

    const message = input.value.trim();

    if (!message) {
        return;
    }


    /* USER MESSAGE */

    const userRow = document.createElement("div");

    userRow.className = "message-row user";


    userRow.innerHTML = `

        <div class="message-content">

            <div class="message user-message">
                ${escapeHTML(message)}
            </div>

            <div class="time">
                ${getTime()}
            </div>

        </div>

    `;


    chatBox.appendChild(userRow);


    input.value = "";

    chatBox.scrollTop = chatBox.scrollHeight;


    /* THINKING */

    const aiRow = document.createElement("div");

    aiRow.className = "message-row";


    aiRow.innerHTML = `

        <img
            class="avatar"
            src="/static/hm-ai-logo.png"
        >

        <div class="message-content">

            <div class="message ai-message">
                Thinking... 🤖
            </div>

        </div>

    `;


    chatBox.appendChild(aiRow);

    chatBox.scrollTop = chatBox.scrollHeight;


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


        aiRow.querySelector(".ai-message").textContent =
            data.reply;


        const time = document.createElement("div");

        time.className = "time";

        time.textContent = getTime();

        aiRow.querySelector(".message-content")
            .appendChild(time);


    }

    catch (error) {

        aiRow.querySelector(".ai-message").textContent =
            "❌ Sorry, I couldn't connect to HM AI.";

    }


    chatBox.scrollTop = chatBox.scrollHeight;

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


        user_message = data.get(
            "message",
            ""
        ).strip()


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

            "reply":
            "Sorry, something went wrong with HM AI."

        }), 500


if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        ),

        debug=False

    )
