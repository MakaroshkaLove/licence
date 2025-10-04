#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify
import hashlib
import time
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# Конфигурация лицензий (замените на свои данные)
LICENSES = {
    # Замените на ваш реальный HWID
    "YOUR_HWID_HERE": {
        "user_name": "Makaron",
        "subscription_duration": 3600,  # 1 час в секундах
        "max_uses": 1000,  # Максимум использований
        "created_at": int(time.time()),
        "last_used": 0,
        "use_count": 0
    }
}

# Секретный ключ для подписи (замените на свой)
SECRET_KEY = "FloraVisuals2024SecretKey"

def generate_signature(data):
    """Генерация подписи для проверки целостности"""
    message = f"{data}{SECRET_KEY}"
    return hashlib.sha256(message.encode()).hexdigest()

def validate_license(hwid):
    """Проверка валидности лицензии"""
    if hwid not in LICENSES:
        return False, "Лицензия не найдена"
    
    license_data = LICENSES[hwid]
    
    # Проверяем количество использований
    if license_data["use_count"] >= license_data["max_uses"]:
        return False, "Превышено максимальное количество использований"
    
    # Проверяем время истечения
    current_time = int(time.time())
    license_created = license_data["created_at"]
    duration = license_data["subscription_duration"]
    
    if current_time > license_created + duration:
        return False, "Лицензия истекла"
    
    return True, "Лицензия действительна"

@app.route('/')
def home():
    railway_url = os.environ.get('RAILWAY_PUBLIC_DOMAIN')
    base_url = f"https://{railway_url}" if railway_url else f"http://localhost:{os.environ.get('PORT', 5000)}"
    
    return jsonify({
        "message": "FloraVisuals License Server",
        "version": "1.0",
        "status": "online",
        "base_url": base_url,
        "endpoints": {
            "check_license": f"{base_url}/check_license",
            "admin_panel": f"{base_url}/admin/licenses?key=admin123",
            "license_info": f"{base_url}/get_license_info?hwid=YOUR_HWID"
        }
    })

@app.route('/check_license', methods=['POST'])
def check_license():
    """Проверка лицензии"""
    try:
        data = request.get_json()
        
        if not data or 'hwid' not in data:
            return jsonify({
                "valid": False,
                "message": "Неверный запрос"
            }), 400
        
        hwid = data['hwid']
        is_valid, message = validate_license(hwid)
        
        if is_valid:
            # Обновляем статистику использования
            LICENSES[hwid]["last_used"] = int(time.time())
            LICENSES[hwid]["use_count"] += 1
            
            # Вычисляем оставшееся время
            current_time = int(time.time())
            license_created = LICENSES[hwid]["created_at"]
            duration = LICENSES[hwid]["subscription_duration"]
            expiration_time = license_created + duration
            remaining_time = max(0, expiration_time - current_time)
            
            response_data = {
                "valid": True,
                "message": message,
                "user_name": LICENSES[hwid]["user_name"],
                "expiration_time": expiration_time,
                "remaining_time": remaining_time,
                "use_count": LICENSES[hwid]["use_count"],
                "max_uses": LICENSES[hwid]["max_uses"]
            }
            
            # Добавляем подпись
            signature = generate_signature(json.dumps(response_data, sort_keys=True))
            response_data["signature"] = signature
            
            return jsonify(response_data)
        else:
            return jsonify({
                "valid": False,
                "message": message
            }), 403
            
    except Exception as e:
        return jsonify({
            "valid": False,
            "message": f"Ошибка сервера: {str(e)}"
        }), 500

@app.route('/get_license_info', methods=['GET'])
def get_license_info():
    """Получение информации о лицензии (для отладки)"""
    hwid = request.args.get('hwid')
    
    if not hwid or hwid not in LICENSES:
        return jsonify({
            "error": "Лицензия не найдена"
        }), 404
    
    license_data = LICENSES[hwid].copy()
    
    # Добавляем читаемые даты
    license_data["created_at_readable"] = datetime.fromtimestamp(license_data["created_at"]).strftime("%Y-%m-%d %H:%M:%S")
    license_data["last_used_readable"] = datetime.fromtimestamp(license_data["last_used"]).strftime("%Y-%m-%d %H:%M:%S") if license_data["last_used"] > 0 else "Никогда"
    
    return jsonify(license_data)

@app.route('/admin/licenses', methods=['GET'])
def admin_licenses():
    """Админ панель для просмотра всех лицензий"""
    admin_key = request.args.get('key')
    
    if admin_key != "admin123":  # Замените на свой пароль
        return jsonify({"error": "Неверный ключ администратора"}), 403
    
    result = {}
    for hwid, data in LICENSES.items():
        result[hwid] = {
            "user_name": data["user_name"],
            "created_at": datetime.fromtimestamp(data["created_at"]).strftime("%Y-%m-%d %H:%M:%S"),
            "last_used": datetime.fromtimestamp(data["last_used"]).strftime("%Y-%m-%d %H:%M:%S") if data["last_used"] > 0 else "Никогда",
            "use_count": data["use_count"],
            "max_uses": data["max_uses"],
            "status": "Активна" if data["use_count"] < data["max_uses"] and int(time.time()) <= data["created_at"] + data["subscription_duration"] else "Истекла"
        }
    
    return jsonify(result)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting FloraVisuals License Server on port {port}")
    
    # Получаем внешний URL Railway
    railway_url = os.environ.get('RAILWAY_PUBLIC_DOMAIN')
    railway_project_id = os.environ.get('RAILWAY_PROJECT_ID')
    
    # Проверяем все возможные переменные Railway
    print("🔍 Railway Environment Variables:")
    for key, value in os.environ.items():
        if 'RAILWAY' in key.upper():
            print(f"   {key} = {value}")
    
    if railway_url:
        print(f"🌐 External URL: https://{railway_url}")
        print(f"🔗 License check endpoint: https://{railway_url}/check_license")
        print(f"📊 Admin panel: https://{railway_url}/admin/licenses?key=admin123")
    elif railway_project_id:
        # Если есть project ID, но нет domain
        print(f"🌐 Railway Project ID: {railway_project_id}")
        print(f"🔗 Try this URL: https://{railway_project_id}.up.railway.app")
        print(f"🔗 License check endpoint: https://{railway_project_id}.up.railway.app/check_license")
        print(f"📊 Admin panel: https://{railway_project_id}.up.railway.app/admin/licenses?key=admin123")
    else:
        print("🌐 Local development mode")
        print(f"🔗 License check endpoint: http://localhost:{port}/check_license")
        print(f"📊 Admin panel: http://localhost:{port}/admin/licenses?key=admin123")
        print("💡 To get Railway URL: Go to Railway Dashboard → Settings → Networking → Generate Domain")
    
    print("=" * 50)
    app.run(host='0.0.0.0', port=port, debug=False)
