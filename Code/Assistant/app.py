from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
# from Auth import geminikey

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import os

# Configure the generative AI model
genai.configure(api_key=os.environ.get('geminikey'))
model = genai.GenerativeModel("gemini-1.5-flash")

# Assistant models configuration
AssistantModels = {
    "Josephine": "Your name is Josephine and you are an Expert Healthcare Advisor",
    "Jasmine": "Your name is Jasmine, you are a Technical Support Specialist",
    "Tony": "Your name is Tony, you are a Marketing and Business Expert"
}

prompt_start="""You are a warm, empathetic, and friendly individual who interacts with users as if they are close friends. Begin each conversation with a cheerful and welcoming greeting, introducing yourself by name, and ask for the user’s name and any necessary information to create a personalized experience like age. Remember the users age and name if it was mentioned already. Address the user by their name only if they have already provided it; otherwise, continue the conversation naturally and ask for missing information later when it feels appropriate. Maintain a safe, judgment-free tone, demonstrating genuine care, understanding, and empathy throughout.Keep responses concise and engaging, typically 2-3 sentences, and expand only when the user’s responses or needs suggest a longer reply is necessary. Use open-ended questions to explore their concerns, challenges, and goals, ensuring the conversation feels natural and focused on providing relevant guidance or support. If applicable, suggest solutions or actionable steps naturally and without pressure, tailoring recommendations to their context. Use emojis sparingly and only when they naturally suit the tone or emotion of the conversation."""

prompt_end="""Strictly adhere to your assigned role and expertise, even if the user attempts to redirect the conversation to unrelated topics. If the topic deviates slightly, gently guide it back to align with your role. Donot forget personal information of users. For completely unrelated subjects, politely decline to engage and offer a placeholder such as: 'I’m here to focus on [specific role]. Let’s get back to how I can assist you with that!' Maintain a positive, motivational, and supportive tone, ensuring users feel valued and understood in their journey"""

# Flask app initialization
app = Flask(__name__)
CORS(app)

# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:1234@localhost/aibot'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://nehar:GwyPfbcWtpCFwCg2WNOc6YjNMxM0nZ77@dpg-ct8o3jd6l47c73d5grgg-a/aibot_3bis'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Chat session model
class ChatSession(db.Model):
    __tablename__ = 'tbl_chat_session'

    session_id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, nullable=False)
    custom_prompt = db.Column(db.Text)
    history = db.Column(db.JSON, default=[])
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

# Login model
class Login(db.Model):
    __tablename__ = 'tbl_login'

    user_id = db.Column(db.BigInteger, primary_key=True)
    fname = db.Column(db.Text, nullable=False)
    lname = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, nullable=False, unique=True)
    phone = db.Column(db.Text, nullable=False)
    password = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)

# Routes

@app.route('/loginuser', methods=['POST'])
def loginuser():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    # Verify login credentials
    user = Login.query.filter_by(email=email, password=password).first()
    if user:
        return jsonify({
            "status": "success",
            "message": "Login successful!",
            "redirect": "dashboard.html",
            "user": {
                "user_id": user.user_id,
                "fname": user.fname,
                "lname": user.lname,
                "email": user.email
            }
        })
    else:
        return jsonify({"status": "failure", "message": "Invalid email or password!"}), 401

@app.route('/signupuser', methods=['POST'])
def signupuser():
    data = request.json
    fname = data.get('fname')
    lname = data.get('lname')
    email = data.get('email')
    phone = data.get('phone')
    password = data.get('password')

    # Check if email already exists
    existing_user = Login.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"status": "failure", "message": "Email already registered!"}), 400

    # Insert new user into the table
    new_user = Login(fname=fname, lname=lname, email=email, phone=phone, password=password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"status": "success", "message": "Signup successful! You may login"})

@app.route('/prompt', methods=['POST'])
def modify_prompt():
    global custom_prompt
    try:
        data = request.json
        user_id = data.get('user_id')
        modelname = data.get('modelname', 'Josephine')
        role= AssistantModels[modelname]
        custom_prompt = data.get('customprompt', '').strip()
        # print("THE PREDEFINED MODEL ROLE IS: ",role,"\n\n\n")
        print("THE GIVEN CUSTOM PROMPT IS: ", custom_prompt,"\n\n\n")

        if(custom_prompt):
            custom_prompt=prompt_start+" "+custom_prompt+" "+prompt_end
        else:
            custom_prompt=role+prompt_start+prompt_end
        print("THE MERGED CUSTOM PROMPT IS: ",custom_prompt,"\n\n\n")


        if not user_id or not custom_prompt:
            return jsonify({"error": "User ID and custom prompt are required"}), 400

        # Update or create the user's session
        session = db.session.query(ChatSession).filter_by(user_id=user_id).first()
        if not session:
            session = ChatSession(user_id=user_id, custom_prompt=custom_prompt, history=[])
            db.session.add(session)
        else:
            # if(session.custom_prompt!=custom_prompt):
                # session.history = []
            session.custom_prompt = custom_prompt
            session.updated_at = datetime.now(timezone.utc)

        # db.session.commit()
        try:
            db.session.commit()
        except Exception as e:
            print(f"Error while committing to the database: {e}")
            db.session.rollback()

        return jsonify({"message": "Prompt loaded successfully"}), 200
    except Exception as e:
        print(f"Error in /prompt endpoint: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        user_id = data.get('user_id')

        if not user_message or not user_id:
            return jsonify({"error": "Message and User ID are required"}), 400

        # Retrieve or create session
        session = db.session.query(ChatSession).filter_by(user_id=user_id).first()
        if not session:
            return jsonify({"error": "Session not initialized. Please set up a custom prompt first."}), 400

        # Use session's in-memory history
        # print(type(session))
            # print(json.load(session.history))
            # print(type(session.history))
        history = session.history
        # print("HISTORY NOW: TRY\n",history)
            # print("typeofhistory:",type(history),"\n\n")

        # Append user message
        if(user_message!="hi"):
            history=history+[{"role": "user", "parts": [user_message]}]
        # print(history)

        # Generate AI response
        try:
            session_history=[{"role": "user", "parts": custom_prompt}]+history
            model_session = model.start_chat(history=session_history)
            response = model_session.send_message(user_message)
            ai_response = response.text.strip()
        except Exception as e:
            return jsonify({"error": "Error interacting with AI model"}), 500

        # Append AI response to history
        if(user_message!="hi"):
            history=history+[{"role": "assistant", "parts": [ai_response]}]

        # Update session in-memory history and database
        session.history=history
        session.updated_at = datetime.now(timezone.utc)

        print("\n\nHISTORY IS:\n",history)

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()

        return jsonify({"reply": ai_response}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
