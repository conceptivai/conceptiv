from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import openai
# from Auth import openaikey
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from sqlalchemy.sql import text  # Import the text function
import os

# Configure OpenAI API
openai.api_key = os.environ.get('openaikey')
# Assistant models configuration
AssistantModels = {
    "Josephine": "Your name is Josephine and you are an Expert Healthcare Advisor",
    "Jasmine": "Your name is Jasmine, you are a Technical Support Specialist",
    "Tony": "Your name is Tony, you are a Marketing and Business Expert"
}

prompt_start = """You are a warm, empathetic, and friendly individual who interacts with users as if they are close friends. Begin each conversation with a cheerful and welcoming greeting, introducing yourself by name, and ask for the user’s name and any necessary information to create a personalized experience like age. Remember the users age and name if it was mentioned already. Address the user by their name only if they have already provided it; otherwise, continue the conversation naturally and ask for missing information later when it feels appropriate. Maintain a safe, judgment-free tone, demonstrating genuine care, understanding, and empathy throughout.Keep responses concise and engaging, typically 2-3 sentences, and expand only when the user’s responses or needs suggest a longer reply is necessary. Use open-ended questions to explore their concerns, challenges, and goals, ensuring the conversation feels natural and focused on providing relevant guidance or support. If applicable, suggest solutions or actionable steps naturally and without pressure, tailoring recommendations to their context. Use emojis sparingly and only when they naturally suit the tone or emotion of the conversation."""

prompt_end = """Strictly adhere to your assigned role and expertise, even if the user attempts to redirect the conversation to unrelated topics. If the topic deviates slightly, gently guide it back to align with your role. Do not forget personal information of users. For completely unrelated subjects, politely decline to engage and offer a placeholder such as: 'I’m here to focus on [specific role]. Let’s get back to how I can assist you with that!' Maintain a positive, motivational, and supportive tone, ensuring users feel valued and understood in their journey."""

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

class ChatInteraction(db.Model):
    __tablename__ = 'tbl_chat_interaction'

    interaction_id = db.Column(db.BigInteger, primary_key=True)
    company_id = db.Column(db.BigInteger, nullable=True)
    user_question = db.Column(db.Text, nullable=False)
    ai_response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now, nullable=False)
    context = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    user_id = db.Column(db.BigInteger, nullable=False)

# Routes
UI_DIRECTORY = os.path.join(os.getcwd(), 'Code', 'UI')

@app.route('/', methods=['GET'])
def serve_login_page():
    return render_template('LoginPage.html')

@app.route('/agent', methods=['GET'])
def serve_agent_page():
    return render_template('Agent.html')

@app.route('/dashboard', methods=['GET'])
def serve_dashboard_page():
    return render_template('Dashboard.html')

@app.route('/company-detail', methods=['GET'])
def serve_company_page():
    return render_template('CompanyDetails.html')

@app.route('/home', methods=['GET'])
def serve_home_page():
    return render_template('index.html')

@app.route('/product-detail', methods=['GET'])
def serve_product_page():
    return render_template('ProductDetails.html')

@app.route('/service-detail', methods=['GET'])
def serve_service_page():
    return render_template('ServiceDetails.html')

@app.route('/terms', methods=['GET'])
def serve_terms_page():
    return render_template('TermsPolicies.html')

@app.route('/knowledge', methods=['GET'])
def serve_knowledge_page():
    return render_template('KnowledgeBase.html')

@app.route('/portal', methods=['GET'])
def serve_portal_page():
    return render_template('portal.html')

@app.route('/loginuser', methods=['POST'])
def loginuser():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    user = Login.query.filter_by(email=email, password=password).first()
    if user:
        return jsonify({
            "status": "success",
            "message": "Login successful!",
            "redirect": "/agent",
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

    existing_user = Login.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"status": "failure", "message": "Email already registered!"}), 400

    new_user = Login(fname=fname, lname=lname, email=email, phone=phone, password=password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"status": "success", "message": "Signup successful! You may login"})

@app.route('/fetch_latest_users', methods=['GET'])
def fetch_latest_users():
    try:
        query = text("""
            SELECT 
                u.user_id, u.fname, u.lname, u.email, MAX(c.timestamp) as latest_timestamp
            FROM tbl_login u
            JOIN tbl_chat_interaction c ON u.user_id = c.user_id
            GROUP BY u.user_id, u.fname, u.lname, u.email
            ORDER BY latest_timestamp DESC
        """)
        results = db.session.execute(query).fetchall()

        # Convert result to dictionary
        data = []
        for r in results:
            data.append({
                "user_id": r.user_id,
                "fname": r.fname,
                "lname": r.lname,
                "email": r.email,
                "timestamp": r.latest_timestamp
            })
        return jsonify(data), 200
    except Exception as e:
        print("Error in /fetch_latest_users:", str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/fetch_messages', methods=['GET'])
def fetch_messages():
    email = request.args.get('email')
    try:
        # Base query
        base_query = """
            SELECT 
                u.user_id, u.email, u.fname, u.lname, 
                c.user_question as user_message, c.ai_response as bot_reply, c.timestamp
            FROM tbl_login u
            JOIN tbl_chat_interaction c ON u.user_id = c.user_id
        """
        
        if email and email != "everything":
            # Query for specific email
            query = text(base_query + " WHERE u.email = :email ORDER BY c.timestamp DESC")
            results = db.session.execute(query, {"email": email}).fetchall()
        else:
            # Query for all messages
            query = text(base_query + " ORDER BY c.timestamp DESC")
            results = db.session.execute(query).fetchall()

        # Convert results to a dictionary
        data = []
        for r in results:
            data.append({
                "user_id": r.user_id,
                "email": r.email,
                "fname": r.fname,
                "lname": r.lname,
                "user_message": r.user_message,
                "bot_reply": r.bot_reply,
                "timestamp": r.timestamp
            })
        return jsonify(data), 200
    except Exception as e:
        print("Error in /fetch_messages:", str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/prompt', methods=['POST'])
def modify_prompt():
    global custom_prompt
    try:
        data = request.json
        user_id = data.get('user_id')
        previousprompt = data.get('localprompt')
        custom_prompt = data.get('customprompt', '').strip()

        if not user_id or not custom_prompt:
            return jsonify({"error": "User ID and custom prompt are required"}), 400

        session = db.session.query(ChatSession).filter_by(user_id=user_id).first()
        if not session:
            session = ChatSession(user_id=user_id, custom_prompt=custom_prompt, history=[])
            db.session.add(session)
        else:
            if previousprompt != custom_prompt:
                session.history = []
            session.custom_prompt = custom_prompt
            session.updated_at = datetime.now(timezone.utc)

        db.session.commit()
        return jsonify({"message": "Prompt loaded successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    try:
        data = request.json
        print("Received data:", data)

        user_message = data.get('message', '').strip()
        user_id = data.get('user_id')
        company_id = data.get('company_id',None)  # Include company_id if available
        context = data.get('context', None)  # Optional field for additional context
        
        if not user_message or not user_id:
            print("Missing message or user_id")
            return jsonify({"error": "Message and User ID are required"}), 400

         # Retrieve or create session
        session = db.session.query(ChatSession).filter_by(user_id=user_id).first()
        if not session:
            print("Session not initialized")
            return jsonify({"error": "Session not initialized. Please set up a custom prompt first."}), 400

        # Prepare history for OpenAI API
        constraints=" Whenever responding to user saying hi, introduce yourself and speak. Keep your responses consize unless it is demanded by the situation of conversation for it to be long, else try to keep it within the amount how a person might in a clear text based conversation"
        constrained_prompt=[{"role": "user", "content": constraints}]
        history = session.history + [{"role": "user", "content": user_message}]
        session_history = [{"role": "system", "content": session.custom_prompt}] + history + constrained_prompt
        print("Session history:", session_history)

        # Correct usage of openai.chat.completions.create
        response =  openai.chat.completions.create(
            model="gpt-4",  # Use the desired model
            messages=session_history
        )
        ai_response = response.choices[0].message.content.strip()
        print(type(ai_response),"<==type of ai_response")
        print("AI Response:", ai_response)

        # Update session history
        history.append({"role": "assistant", "content": ai_response})
        session.history = history
        session.updated_at = datetime.now(timezone.utc)
        db.session.commit()


        new_interaction = ChatInteraction(
            company_id=company_id,
            user_question=user_message,
            ai_response=ai_response,
            context=context,
            user_id=user_id
        )
        db.session.add(new_interaction)
        db.session.commit()

        return jsonify({"reply": ai_response}), 200

    except Exception as e:
        print("Error in /chat:", str(e))
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)




#---GEMINI---
# from flask import Flask, request, jsonify, render_template, send_from_directory
# from flask_cors import CORS
# import google.generativeai as genai
# from Auth import geminikey
# from flask_sqlalchemy import SQLAlchemy
# from datetime import datetime, timezone
# import os

# # Configure the generative AI model
# genai.configure(api_key=geminikey.key)
# # genai.configure(api_key=os.environ.get('geminikey'))
# model = genai.GenerativeModel("gemini-1.5-flash")

# # Assistant models configuration
# AssistantModels = {
#     "Josephine": "Your name is Josephine and you are an Expert Healthcare Advisor",
#     "Jasmine": "Your name is Jasmine, you are a Technical Support Specialist",
#     "Tony": "Your name is Tony, you are a Marketing and Business Expert"
# }

# prompt_start="""You are a warm, empathetic, and friendly individual who interacts with users as if they are close friends. Begin each conversation with a cheerful and welcoming greeting, introducing yourself by name, and ask for the user’s name and any necessary information to create a personalized experience like age. Remember the users age and name if it was mentioned already. Address the user by their name only if they have already provided it; otherwise, continue the conversation naturally and ask for missing information later when it feels appropriate. Maintain a safe, judgment-free tone, demonstrating genuine care, understanding, and empathy throughout.Keep responses concise and engaging, typically 2-3 sentences, and expand only when the user’s responses or needs suggest a longer reply is necessary. Use open-ended questions to explore their concerns, challenges, and goals, ensuring the conversation feels natural and focused on providing relevant guidance or support. If applicable, suggest solutions or actionable steps naturally and without pressure, tailoring recommendations to their context. Use emojis sparingly and only when they naturally suit the tone or emotion of the conversation."""

# prompt_end="""Strictly adhere to your assigned role and expertise, even if the user attempts to redirect the conversation to unrelated topics. If the topic deviates slightly, gently guide it back to align with your role. Donot forget personal information of users. For completely unrelated subjects, politely decline to engage and offer a placeholder such as: 'I’m here to focus on [specific role]. Let’s get back to how I can assist you with that!' Maintain a positive, motivational, and supportive tone, ensuring users feel valued and understood in their journey"""

# # Flask app initialization
# app = Flask(__name__)
# # app = Flask(__name__, template_folder='Code/UI')
# CORS(app)

# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:1234@localhost/aibot'
# # app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://nehar:GwyPfbcWtpCFwCg2WNOc6YjNMxM0nZ77@dpg-ct8o3jd6l47c73d5grgg-a/aibot_3bis'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# db = SQLAlchemy(app)

# # Chat session model
# class ChatSession(db.Model):
#     __tablename__ = 'tbl_chat_session'

#     session_id = db.Column(db.BigInteger, primary_key=True)
#     user_id = db.Column(db.BigInteger, nullable=False)
#     custom_prompt = db.Column(db.Text)
#     history = db.Column(db.JSON, default=[])
#     updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

# # Login model
# class Login(db.Model):
#     __tablename__ = 'tbl_login'

#     user_id = db.Column(db.BigInteger, primary_key=True)
#     fname = db.Column(db.Text, nullable=False)
#     lname = db.Column(db.Text, nullable=False)
#     email = db.Column(db.Text, nullable=False, unique=True)
#     phone = db.Column(db.Text, nullable=False)
#     password = db.Column(db.Text, nullable=False)
#     created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)

# # Routes
# # Configure the path to the custom directory
# UI_DIRECTORY = os.path.join(os.getcwd(), 'Code', 'UI')

# # Route to serve the LoginPage.css


# @app.route('/', methods=['GET'])
# def serve_login_page():
#     return render_template('LoginPage.html')
  
# @app.route('/agent', methods=['GET'])
# def serve_agent_page():
#     return render_template('Agent.html')

# @app.route('/dashboard', methods=['GET'])
# def serve_dashboard_page():
#     return render_template('Dashboard.html')

# @app.route('/company-detail', methods=['GET'])
# def serve_company_page():
#     return render_template('CompanyDetails.html')
    
# @app.route('/home', methods=['GET'])
# def serve_home_page():
#     return render_template('index.html')

# @app.route('/product-detail', methods=['GET'])
# def serve_product_page():
#     return render_template('ProductDetails.html')

# @app.route('/service-detail', methods=['GET'])
# def serve_service_page():
#     return render_template('ServiceDetails.html')

# @app.route('/terms', methods=['GET'])
# def serve_terms_page():
#     return render_template('TermsPolicies.html')


# @app.route('/knowledge', methods=['GET'])
# def serve_knowledge_page():
#     return render_template('KnowledgeBase.html')

# # @app.route('/', methods=['GET'])
# # def serve_login_page():
# #     # Serve the loginpage.html file from the code/ui/ directory
# #     return send_from_directory('Code/UI', 'LoginPage.html')

# @app.route('/loginuser', methods=['POST'])
# def loginuser():
#     data = request.json
#     email = data.get('email')
#     password = data.get('password')

#     # Verify login credentials
#     user = Login.query.filter_by(email=email, password=password).first()
#     if user:
#         return jsonify({
#             "status": "success",
#             "message": "Login successful!",
#             "redirect": "/agent",
#             "user": {
#                 "user_id": user.user_id,
#                 "fname": user.fname,
#                 "lname": user.lname,
#                 "email": user.email
#             }
#         })
#     else:
#         return jsonify({"status": "failure", "message": "Invalid email or password!"}), 401

# @app.route('/signupuser', methods=['POST'])
# def signupuser():
#     data = request.json
#     fname = data.get('fname')
#     lname = data.get('lname')
#     email = data.get('email')
#     phone = data.get('phone')
#     password = data.get('password')

#     # Check if email already exists
#     existing_user = Login.query.filter_by(email=email).first()
#     if existing_user:
#         return jsonify({"status": "failure", "message": "Email already registered!"}), 400

#     # Insert new user into the table
#     new_user = Login(fname=fname, lname=lname, email=email, phone=phone, password=password)
#     db.session.add(new_user)
#     db.session.commit()

#     return jsonify({"status": "success", "message": "Signup successful! You may login"})

# @app.route('/prompt', methods=['POST'])
# def modify_prompt():
#     global custom_prompt
#     try:
#         data = request.json
#         user_id = data.get('user_id')
#         # fields = data.get('customprompt', {})
#         previousprompt=data.get('localprompt')
#         custom_prompt = data.get('customprompt', '').strip()
        
#         # custom_prompt = " ".join(
#         #     [f"Your {key} is {value}." for key, value in fields.items() if value]
#         # ).strip()

#         if not user_id or not custom_prompt:
#             return jsonify({"error": "User ID and custom prompt are required"}), 400

#         # Update or create the user's session
#         session = db.session.query(ChatSession).filter_by(user_id=user_id).first()
#         if not session:
#             session = ChatSession(user_id=user_id, custom_prompt=custom_prompt, history=[])
#             db.session.add(session)
#         else:
#             if(previousprompt!=custom_prompt):
#                 session.history = []

#             session.custom_prompt = custom_prompt
#             session.updated_at = datetime.now(timezone.utc)

#         # db.session.commit()
#         try:
#             db.session.commit()
#         except Exception as e:
#             print(f"Error while committing to the database: {e}")
#             db.session.rollback()

#         return jsonify({"message": "Prompt loaded successfully"}), 200
#     except Exception as e:
#         print(f"Error in /prompt endpoint: {e}")
#         return jsonify({"error": str(e)}), 500


# @app.route('/chat', methods=['POST'])
# def chat_endpoint():
#     try:
#         data = request.json
#         user_message = data.get('message', '').strip()
#         user_id = data.get('user_id')
        

#         if not user_message or not user_id:
#             return jsonify({"error": "Message and User ID are required"}), 400

#         # Retrieve or create session
#         session = db.session.query(ChatSession).filter_by(user_id=user_id).first()
#         if not session:
#             return jsonify({"error": "Session not initialized. Please set up a custom prompt first."}), 400

#         # Use session's in-memory history
#         # print(type(session))
#             # print(json.load(session.history))
#             # print(type(session.history))
#         history = session.history
#         print("HISTORY NOW: TRY\n",history)
#             # print("typeofhistory:",type(history),"\n\n")

#         # Append user message
#         history=history+[{"role": "user", "parts": [user_message]}]
#         # print(history)

#         # Generate AI response
#         try:
#             constraints=" Keep your responses consize unless it is demanded by the situation of conversation else try to keep it within 100 words"
#             constrained_prompt=custom_prompt+constraints
#             session_history=[{"role": "user", "parts": constrained_prompt}]+history
#             model_session = model.start_chat(history=session_history)
#             response = model_session.send_message(user_message)
#             ai_response = response.text.strip()
#         except Exception as e:
#             return jsonify({"error": "Error interacting with AI model"}), 500

#         # Append AI response to history
#         # if(user_message!="hi"):
#         history=history+[{"role": "assistant", "parts": [ai_response]}]

#         # Update session in-memory history and database
#         session.history=history
#         session.updated_at = datetime.now(timezone.utc)

#         print("\n\nHISTORY IS:\n",history)

#         try:
#             db.session.commit()
#         except Exception as e:
#             db.session.rollback()

#         return jsonify({"reply": ai_response}), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=8000, debug=True)
