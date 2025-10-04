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
    "4553BEC6D63967B1": {
        "user_name": "Makaron",
        "subscription_duration": 300,  # 5 минут в секундах
        "max_uses": 1,  # Максимум использований
        "created_at": 0,  # Будет установлено при первом использовании
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

    # Если лицензия еще не была использована, устанавливаем время создания
    if license_data["created_at"] == 0:
        license_data["created_at"] = int(time.time())
        return True, "Лицензия активирована"

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
            "admin_panel": f"{base_url}/admin/licenses?key=FloraVisuals2024_Admin_Key_7x9K2mP8qR5",
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
    license_data["created_at_readable"] = datetime.fromtimestamp(license_data["created_at"]).strftime("%Y-%m-%d %H:%M:%S") if license_data["created_at"] > 0 else "Не активирована"
    license_data["last_used_readable"] = datetime.fromtimestamp(license_data["last_used"]).strftime("%Y-%m-%d %H:%M:%S") if license_data["last_used"] > 0 else "Никогда"
    
    # Добавляем время истечения
    expiration_time = license_data["created_at"] + license_data["subscription_duration"]
    license_data["expires_at_readable"] = datetime.fromtimestamp(expiration_time).strftime("%Y-%m-%d %H:%M:%S") if license_data["created_at"] > 0 else "Не активирована"
    
    return jsonify(license_data)

@app.route('/admin/licenses', methods=['GET'])
def admin_licenses():
    """Админ панель для просмотра всех лицензий"""
    admin_key = request.args.get('key')

    if admin_key != "FloraVisuals2024_Admin_Key_7x9K2mP8qR5":  # Сложный пароль админки
        return jsonify({"error": "Неверный ключ администратора"}), 403

    # Возвращаем HTML страницу с кнопками
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>FloraVisuals License Admin</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; text-align: center; margin-bottom: 30px; }
            .add-license { background: #e8f5e8; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
            .add-license h3 { margin-top: 0; color: #2e7d32; }
            .form-group { margin: 10px 0; }
            .form-group label { display: inline-block; width: 120px; font-weight: bold; }
            .form-group input, .form-group select { padding: 5px; border: 1px solid #ddd; border-radius: 3px; width: 200px; }
            table { border-collapse: collapse; width: 100%; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #4CAF50; color: white; }
            tr:nth-child(even) { background-color: #f2f2f2; }
            button { padding: 5px 10px; border: none; cursor: pointer; border-radius: 3px; margin: 2px; }
            .btn-reset { background-color: #ff9800; color: white; }
            .btn-reset:hover { background-color: #f57c00; }
            .btn-delete { background-color: #f44336; color: white; }
            .btn-delete:hover { background-color: #d32f2f; }
            .btn-add { background-color: #4CAF50; color: white; padding: 10px 20px; }
            .btn-add:hover { background-color: #45a049; }
            .btn-extend { background-color: #2196F3; color: white; }
            .btn-extend:hover { background-color: #1976D2; }
            .status-active { color: #4CAF50; font-weight: bold; }
            .status-expired { color: #f44336; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔐 FloraVisuals License Admin Panel</h1>
            
            <div class="add-license">
                <h3>➕ Add New License</h3>
                <div class="form-group">
                    <label>HWID:</label>
                    <input type="text" id="new_hwid" placeholder="Enter HWID">
                </div>
                <div class="form-group">
                    <label>User Name:</label>
                    <input type="text" id="new_username" placeholder="Enter username">
                </div>
                <div class="form-group">
                    <label>Duration (min):</label>
                    <select id="new_duration">
                        <option value="60">1 minute</option>
                        <option value="300" selected>5 minutes</option>
                        <option value="600">10 minutes</option>
                        <option value="1800">30 minutes</option>
                        <option value="3600">1 hour</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Max Uses:</label>
                    <input type="number" id="new_max_uses" value="10" min="1" max="100">
                </div>
                <button class="btn-add" onclick="addLicense()">Add License</button>
            </div>
            
            <table>
                <tr>
                    <th>HWID</th>
                    <th>User</th>
                    <th>Created</th>
                    <th>Expires</th>
                    <th>Last Used</th>
                    <th>Uses</th>
                    <th>Status</th>
                    <th>Actions</th>
                </tr>
    """
    
    for hwid, data in LICENSES.items():
        # Вычисляем время истечения
        expiration_time = data["created_at"] + data["subscription_duration"]
        expiration_readable = datetime.fromtimestamp(expiration_time).strftime("%Y-%m-%d %H:%M:%S") if data["created_at"] > 0 else "Не активирована"
        created_readable = datetime.fromtimestamp(data["created_at"]).strftime("%Y-%m-%d %H:%M:%S") if data["created_at"] > 0 else "Не активирована"
        last_used_readable = datetime.fromtimestamp(data["last_used"]).strftime("%Y-%m-%d %H:%M:%S") if data["last_used"] > 0 else "Никогда"
        is_active = data["use_count"] < data["max_uses"] and int(time.time()) <= data["created_at"] + data["subscription_duration"]
        status = "Активна" if is_active else "Истекла"
        status_class = "status-active" if is_active else "status-expired"
        
        html += f"""
            <tr>
                <td><code>{hwid}</code></td>
                <td>{data["user_name"]}</td>
                <td>{created_readable}</td>
                <td>{expiration_readable}</td>
                <td>{last_used_readable}</td>
                <td>{data["use_count"]}/{data["max_uses"]}</td>
                <td class="{status_class}">{status}</td>
                <td>
                    <button class="btn-reset" onclick="resetLicense('{hwid}')">🔄 Reset</button>
                    <button class="btn-extend" onclick="extendLicense('{hwid}')">⏰ Extend</button>
                    <button class="btn-delete" onclick="deleteLicense('{hwid}')">🗑️ Delete</button>
                </td>
            </tr>
        """
    
    html += """
            </table>
        </div>
        
        <script>
            function addLicense() {
                const hwid = document.getElementById('new_hwid').value;
                const username = document.getElementById('new_username').value;
                const duration = document.getElementById('new_duration').value;
                const maxUses = document.getElementById('new_max_uses').value;
                
                if (!hwid || !username) {
                    alert('Please fill in HWID and Username');
                    return;
                }
                
                fetch('/admin/add_license?key=FloraVisuals2024_Admin_Key_7x9K2mP8qR5', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        hwid: hwid,
                        username: username,
                        duration: parseInt(duration),
                        max_uses: parseInt(maxUses)
                    })
                })
                .then(response => response.json())
                .then(data => {
                    alert(data.message);
                    location.reload();
                })
                .catch(error => alert('Error: ' + error));
            }
            
            function resetLicense(hwid) {
                if (confirm('Reset this license? This will reset use count and start time.')) {
                    fetch('/admin/reset_license?key=FloraVisuals2024_Admin_Key_7x9K2mP8qR5', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({hwid: hwid})
                    })
                    .then(response => response.json())
                    .then(data => {
                        alert(data.message);
                        location.reload();
                    })
                    .catch(error => alert('Error: ' + error));
                }
            }
            
            function extendLicense(hwid) {
                const duration = prompt('Extend license by how many minutes?', '5');
                if (duration && !isNaN(duration)) {
                    fetch('/admin/extend_license?key=FloraVisuals2024_Admin_Key_7x9K2mP8qR5', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({hwid: hwid, minutes: parseInt(duration)})
                    })
                    .then(response => response.json())
                    .then(data => {
                        alert(data.message);
                        location.reload();
                    })
                    .catch(error => alert('Error: ' + error));
                }
            }
            
            function deleteLicense(hwid) {
                if (confirm('Are you sure you want to DELETE this license? This cannot be undone!')) {
                    fetch('/admin/delete_license?key=FloraVisuals2024_Admin_Key_7x9K2mP8qR5', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({hwid: hwid})
                    })
                    .then(response => response.json())
                    .then(data => {
                        alert(data.message);
                        location.reload();
                    })
                    .catch(error => alert('Error: ' + error));
                }
            }
        </script>
    </body>
    </html>
    """
    
    return html

@app.route('/admin/reset_license', methods=['POST'])
def admin_reset_license():
    """Сброс лицензии (установка нового времени создания)"""
    admin_key = request.args.get('key')
    if admin_key != "FloraVisuals2024_Admin_Key_7x9K2mP8qR5":
        return jsonify({"message": "Неверный ключ администратора"}), 403

    data = request.get_json()
    hwid = data.get('hwid')

    if not hwid or hwid not in LICENSES:
        return jsonify({"message": "Лицензия не найдена"}), 404

    license_data = LICENSES[hwid]
    license_data['created_at'] = int(time.time())  # Новое время создания
    license_data['last_used'] = 0
    license_data['use_count'] = 0

    return jsonify({"message": f"Лицензия для {hwid} сброшена и активирована"}), 200

@app.route('/admin/add_license', methods=['POST'])
def admin_add_license():
    """Добавление новой лицензии"""
    admin_key = request.args.get('key')
    if admin_key != "FloraVisuals2024_Admin_Key_7x9K2mP8qR5":
        return jsonify({"message": "Неверный ключ администратора"}), 403

    data = request.get_json()
    hwid = data.get('hwid')
    username = data.get('username')
    duration = data.get('duration', 300)  # 5 минут по умолчанию
    max_uses = data.get('max_uses', 10)

    if not hwid or not username:
        return jsonify({"message": "HWID и имя пользователя обязательны"}), 400

    if hwid in LICENSES:
        return jsonify({"message": "Лицензия с таким HWID уже существует"}), 400

    LICENSES[hwid] = {
        "user_name": username,
        "subscription_duration": duration,
        "max_uses": max_uses,
        "created_at": 0,  # Будет установлено при первом использовании
        "last_used": 0,
        "use_count": 0
    }

    return jsonify({"message": f"Лицензия для {hwid} добавлена"}), 200

@app.route('/admin/extend_license', methods=['POST'])
def admin_extend_license():
    """Продление лицензии"""
    admin_key = request.args.get('key')
    if admin_key != "FloraVisuals2024_Admin_Key_7x9K2mP8qR5":
        return jsonify({"message": "Неверный ключ администратора"}), 403

    data = request.get_json()
    hwid = data.get('hwid')
    minutes = data.get('minutes', 5)

    if not hwid or hwid not in LICENSES:
        return jsonify({"message": "Лицензия не найдена"}), 404

    license_data = LICENSES[hwid]
    license_data['subscription_duration'] += minutes * 60  # Добавляем секунды

    return jsonify({"message": f"Лицензия для {hwid} продлена на {minutes} минут"}), 200

@app.route('/admin/delete_license', methods=['POST'])
def admin_delete_license():
    """Удаление лицензии"""
    admin_key = request.args.get('key')
    if admin_key != "FloraVisuals2024_Admin_Key_7x9K2mP8qR5":
        return jsonify({"message": "Неверный ключ администратора"}), 403

    data = request.get_json()
    hwid = data.get('hwid')

    if not hwid or hwid not in LICENSES:
        return jsonify({"message": "Лицензия не найдена"}), 404

    del LICENSES[hwid]
    return jsonify({"message": f"Лицензия для {hwid} удалена"}), 200

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
        print(f"📊 Admin panel: https://{railway_url}/admin/licenses?key=FloraVisuals2024_Admin_Key_7x9K2mP8qR5")
    elif railway_project_id:
        # Если есть project ID, но нет domain
        print(f"🌐 Railway Project ID: {railway_project_id}")
        print(f"🔗 Try this URL: https://{railway_project_id}.up.railway.app")
        print(f"🔗 License check endpoint: https://{railway_project_id}.up.railway.app/check_license")
        print(f"📊 Admin panel: https://{railway_project_id}.up.railway.app/admin/licenses?key=FloraVisuals2024_Admin_Key_7x9K2mP8qR5")
    else:
        print("🌐 Local development mode")
        print(f"🔗 License check endpoint: http://localhost:{port}/check_license")
        print(f"📊 Admin panel: http://localhost:{port}/admin/licenses?key=FloraVisuals2024_Admin_Key_7x9K2mP8qR5")
        print("💡 To get Railway URL: Go to Railway Dashboard → Settings → Networking → Generate Domain")
    
    print("=" * 50)
    app.run(host='0.0.0.0', port=port, debug=False)
