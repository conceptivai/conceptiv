from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import stripe
import openai
from flask_sqlalchemy import SQLAlchemy
from celery import Celery
from flask_apscheduler import APScheduler
from datetime import datetime, timezone, timedelta
from sqlalchemy.sql import text
import smtplib, ssl, random
from email.message import EmailMessage
import os

# Configure API Keys
openai.api_key = os.environ.get('openaikey')
stripe.api_key = os.environ.get('stripeprivatekey')
stripepublickkey = os.environ.get('stripepublickey')
zeptokey = os.environ.get('zeptomailkey')

print(zeptokey)


# Flask app initialization
app = Flask(__name__)
CORS(app)

# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://nehar:GwyPfbcWtpCFwCg2WNOc6YjNMxM0nZ77@dpg-ct8o3jd6l47c73d5grgg-a/aibot_3bis'  ##Onrender
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:1234@localhost/aibot'  ##Local
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Celery configuration
app.config['broker_url'] = 'rediss://red-ctckvrrtq21c73frunm0:wO6u9NWJfOoGud3X9jCoRKw2nB5n1kZc@oregon-redis.render.com:6379'
app.config['result_backend'] = 'rediss://red-ctckvrrtq21c73frunm0:wO6u9NWJfOoGud3X9jCoRKw2nB5n1kZc@oregon-redis.render.com:6379'

db = SQLAlchemy(app)


def sendfollowmail(mailid):
    port = 587
    smtp_server = "smtp.zeptomail.com"
    username="emailapikey"
    password = zeptokey
    message = "test mail for retention function"
    msg = EmailMessage()
    msg['Subject'] = "Conceptiv AI - Callback"
    msg['From'] = "noreply@conceptiv.ai"
    msg['To'] = mailid
    msg.set_content(message)
    try:
        if port == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
                server.login(username, password)
                server.send_message(msg)
        elif port == 587:
            with smtplib.SMTP(smtp_server, port) as server:
                server.starttls()
                server.login(username, password)
                server.send_message(msg)
        else:
            print ("use 465 / 587 as port value")
            return False
        print ("successfully sent")
        return True
    except Exception as e:
        print (e)
        return False

app.config.update(
    broker_url='rediss://red-ctckvrrtq21c73frunm0:wO6u9NWJfOoGud3X9jCoRKw2nB5n1kZc@oregon-redis.render.com:6379',
    result_backend='rediss://red-ctckvrrtq21c73frunm0:wO6u9NWJfOoGud3X9jCoRKw2nB5n1kZc@oregon-redis.render.com:6379',
    broker_transport_options={
        'ssl': {
            'ssl_cert_reqs': ssl.CERT_REQUIRED  # Change to ssl.CERT_REQUIRED if you have a valid certificate
        }
    },
    redis_backend_transport_options={
        'ssl': {
            'ssl_cert_reqs': ssl.CERT_REQUIRED  # Same here
        }
    }
)

# Celery setup
def make_celery(app):
    celery = Celery(
        app.import_name,
        broker=app.config['broker_url'],
        backend=app.config['result_backend']
    )
    celery.conf.update(app.config)
    celery.conf.update(
        broker_use_ssl={
            'ssl_cert_reqs': 'CERT_REQUIRED'
        },
        redis_backend_use_ssl={
            'ssl_cert_reqs': 'CERT_REQUIRED'
        }
    )
    return celery

celery = make_celery(app)

# Celery task
@celery.task
def check_and_send_email():
    sendfollowmail("neharshinz@gmail.com")

# Flask-APScheduler setup for periodic tasks
scheduler = APScheduler()

@scheduler.task('interval', id='check_and_send_email', seconds=60)
def periodic_task():
    check_and_send_email.delay()  # Trigger the Celery task

scheduler.init_app(app)
scheduler.start()

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

class tbl_prompt(db.Model):
    __tablename__ = 'tbl_prompt'

    prompt_id = db.Column(db.BigInteger, primary_key=True)
    role = db.Column(db.String(255), nullable=True)
    prompt = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    user_id = db.Column(db.BigInteger, nullable=True)
    company_id = db.Column(db.BigInteger, nullable=True)

# # Routes
# UI_DIRECTORY = os.path.join(os.getcwd(), 'Code', 'UI')


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
    return render_template('index.html', key=os.environ.get('stripepublickkey'))

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

@app.route('/UserLogin', methods=['GET'])
def serve_userlogin_page():
    return render_template('UserLogin.html')


def sendOTP(OTP,mailid):
    port = 587
    smtp_server = "smtp.zeptomail.com"
    username="emailapikey"
    password = zeptokey
    message = "Your OTP for Concceptive AI is "+ OTP +" . This is only for your private. Never share your OTP to unknown people over the phone or internet."
    msg = EmailMessage()
    msg['Subject'] = "Conceptiv AI - OTP"
    msg['From'] = "noreply@conceptiv.ai"
    msg['To'] = mailid
    msg.set_content(message)
    try:
        if port == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
                server.login(username, password)
                server.send_message(msg)
        elif port == 587:
            with smtplib.SMTP(smtp_server, port) as server:
                server.starttls()
                server.login(username, password)
                server.send_message(msg)
        else:
            print ("use 465 / 587 as port value")
            return False
        print ("successfully sent")
        return True
    except Exception as e:
        print (e)
        return False

@app.route('/generateotp', methods=['POST'])
def generateotp():
    data = request.json
    email = data.get('email')
    otp = str(random.randint(100000, 999999))  # OTP must be a string to include in the email

    # Send the OTP email
    otp_sent = sendOTP(otp, email)  # Use a different variable name to avoid conflict

    if otp_sent:

        return jsonify({
            "status": "success",
            "message": "OTP sent successfully!",
            "user": {
                "otp": otp,
            }
        })
    else:
        return jsonify({"status": "failure", "message": "Failed to generate OTP"}), 401

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'Conceptiv AI - 30 minute Premium',
                    },
                    'unit_amount': 999,  # Amount in cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url='http://127.0.0.1:8000/UserLogin',
            cancel_url='http://127.0.0.1:8000/home',
            # success_url='https://conceptiv.onrender.com/UserLogin',
            # cancel_url='https://conceptiv.onrender.com/home',
        )
        print(checkout_session.id)
        print()
        return jsonify({'id': checkout_session.id})
    except Exception as e:
        return jsonify(error=str(e)), 403


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
        company_id = data.get('company_id', None)

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

        prompt_entry = db.session.query(tbl_prompt).filter_by(user_id=user_id).first()
        if not prompt_entry:
            new_prompt = tbl_prompt(
                role='admin',  # Assuming role is 'user'
                prompt=custom_prompt,
                user_id=user_id,
                company_id=company_id,
            )
            db.session.add(new_prompt)
        else:
            prompt_entry.prompt = custom_prompt
            prompt_entry.updated_at = datetime.now(timezone.utc)

        
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
        constraints=" Whenever responding to user saying hi, introduce yourself and speak. Keep your responses consize unless it is demanded by the situation of conversation for it to be long, else try to keep it within the amount how a person might in a clear text based conversation. Keep your conversations interactive by asking questions when required instead of just answering with a statement always."
        constrained_prompt=[{"role": "user", "content": constraints}]
        history = session.history + [{"role": "user", "content": user_message}]
        session_history = [{"role": "system", "content": session.custom_prompt}] + history + constrained_prompt
        print("Session history:", session_history)

        # Correct usage of openai.chat.completions.create
        response =  openai.chat.completions.create(
            model="gpt-4o-mini",  # Use the desired model
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