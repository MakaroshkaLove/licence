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
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>FloraVisuals - Панель управления лицензиями</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container { 
                max-width: 1400px; 
                margin: 0 auto; 
                background: rgba(255, 255, 255, 0.95); 
                padding: 30px; 
                border-radius: 20px; 
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                backdrop-filter: blur(10px);
            }
            .header {
                text-align: center;
                margin-bottom: 40px;
                padding: 20px;
                background: linear-gradient(45deg, #4CAF50, #45a049);
                border-radius: 15px;
                color: white;
                box-shadow: 0 10px 20px rgba(76, 175, 80, 0.3);
            }
            .header h1 { 
                font-size: 2.5em; 
                margin-bottom: 10px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }
            .header p { 
                font-size: 1.2em; 
                opacity: 0.9;
            }
            .add-license { 
                background: linear-gradient(135deg, #e8f5e8, #f1f8e9); 
                padding: 25px; 
                border-radius: 15px; 
                margin-bottom: 30px;
                border: 2px solid #4CAF50;
                box-shadow: 0 5px 15px rgba(76, 175, 80, 0.2);
            }
            .add-license h3 { 
                margin-bottom: 20px; 
                color: #2e7d32; 
                font-size: 1.5em;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .form-row { 
                display: flex; 
                gap: 20px; 
                flex-wrap: wrap; 
                margin-bottom: 15px;
            }
            .form-group { 
                flex: 1; 
                min-width: 200px;
            }
            .form-group label { 
                display: block; 
                margin-bottom: 5px; 
                font-weight: 600; 
                color: #333;
            }
            .form-group input, .form-group select { 
                width: 100%; 
                padding: 12px; 
                border: 2px solid #ddd; 
                border-radius: 8px; 
                font-size: 14px;
                transition: all 0.3s ease;
            }
            .form-group input:focus, .form-group select:focus {
                outline: none;
                border-color: #4CAF50;
                box-shadow: 0 0 10px rgba(76, 175, 80, 0.3);
            }
            .table-container {
                overflow-x: auto;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            }
            table { 
                width: 100%; 
                border-collapse: collapse; 
                background: white;
            }
            th { 
                background: linear-gradient(45deg, #4CAF50, #45a049); 
                color: white; 
                padding: 15px 10px; 
                text-align: left; 
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            td { 
                padding: 15px 10px; 
                border-bottom: 1px solid #eee;
                vertical-align: middle;
            }
            tr:hover { 
                background-color: #f8f9fa; 
                transform: scale(1.01);
                transition: all 0.2s ease;
            }
            tr:nth-child(even) { 
                background-color: #f8f9fa; 
            }
            .hwid-cell {
                font-family: 'Courier New', monospace;
                background: #f5f5f5;
                padding: 8px;
                border-radius: 5px;
                font-size: 12px;
            }
            .time-remaining {
                font-weight: bold;
                padding: 5px 10px;
                border-radius: 20px;
                font-size: 12px;
                text-align: center;
            }
            .time-active {
                background: #e8f5e8;
                color: #2e7d32;
            }
            .time-expired {
                background: #ffebee;
                color: #c62828;
            }
            .time-warning {
                background: #fff3e0;
                color: #ef6c00;
            }
            button { 
                padding: 8px 15px; 
                border: none; 
                cursor: pointer; 
                border-radius: 8px; 
                margin: 2px; 
                font-weight: 600;
                transition: all 0.3s ease;
                font-size: 12px;
            }
            .btn-reset { 
                background: linear-gradient(45deg, #ff9800, #f57c00); 
                color: white; 
            }
            .btn-reset:hover { 
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(255, 152, 0, 0.4);
            }
            .btn-delete { 
                background: linear-gradient(45deg, #f44336, #d32f2f); 
                color: white; 
            }
            .btn-delete:hover { 
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(244, 67, 54, 0.4);
            }
            .btn-add { 
                background: linear-gradient(45deg, #4CAF50, #45a049); 
                color: white; 
                padding: 15px 30px; 
                font-size: 16px;
            }
            .btn-add:hover { 
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(76, 175, 80, 0.4);
            }
            .btn-extend { 
                background: linear-gradient(45deg, #2196F3, #1976D2); 
                color: white; 
            }
            .btn-extend:hover { 
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(33, 150, 243, 0.4);
            }
            .status-active { 
                color: #4CAF50; 
                font-weight: bold; 
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            .status-expired { 
                color: #f44336; 
                font-weight: bold; 
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1px));
                gap: 20px;
                margin-bottom: 30px;
            }
            .stat-card {
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white;
                padding: 20px;
                border-radius: 15px;
                text-align: center;
                box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
            }
            .stat-number {
                font-size: 2em;
                font-weight: bold;
                margin-bottom: 5px;
            }
            .stat-label {
                font-size: 0.9em;
                opacity: 0.9;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔐 FloraVisuals</h1>
                <p>Панель управления лицензиями</p>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number" id="total-licenses">0</div>
                    <div class="stat-label">Всего лицензий</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="active-licenses">0</div>
                    <div class="stat-label">Активных</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="expired-licenses">0</div>
                    <div class="stat-label">Истекших</div>
                </div>
            </div>
            
            <div class="add-license">
                <h3>➕ Добавить новую лицензию</h3>
                <div class="form-row">
                    <div class="form-group">
                        <label>HWID:</label>
                        <input type="text" id="new_hwid" placeholder="Введите HWID">
                    </div>
                    <div class="form-group">
                        <label>Имя пользователя:</label>
                        <input type="text" id="new_username" placeholder="Введите имя пользователя">
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Время подписки:</label>
                        <select id="new_duration">
                            <option value="60">1 минута</option>
                            <option value="300" selected>5 минут</option>
                            <option value="600">10 минут</option>
                            <option value="1800">30 минут</option>
                            <option value="3600">1 час</option>
                            <option value="7200">2 часа</option>
                            <option value="86400">24 часа</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Максимум использований:</label>
                        <input type="number" id="new_max_uses" value="10" min="1" max="100">
                    </div>
                </div>
                <button class="btn-add" onclick="addLicense()">➕ Добавить лицензию</button>
            </div>
            
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>HWID</th>
                            <th>Пользователь</th>
                            <th>Создана</th>
                            <th>Истекает</th>
                            <th>Последнее использование</th>
                            <th>Использований</th>
                            <th>Осталось времени</th>
                            <th>Статус</th>
                            <th>Действия</th>
                        </tr>
                    </thead>
                    <tbody>
    """
    
    total_licenses = len(LICENSES)
    active_count = 0
    expired_count = 0
    
    for hwid, data in LICENSES.items():
        # Вычисляем время истечения
        expiration_time = data["created_at"] + data["subscription_duration"]
        expiration_readable = datetime.fromtimestamp(expiration_time).strftime("%Y-%m-%d %H:%M:%S") if data["created_at"] > 0 else "Не активирована"
        created_readable = datetime.fromtimestamp(data["created_at"]).strftime("%Y-%m-%d %H:%M:%S") if data["created_at"] > 0 else "Не активирована"
        last_used_readable = datetime.fromtimestamp(data["last_used"]).strftime("%Y-%m-%d %H:%M:%S") if data["last_used"] > 0 else "Никогда"
        
        # Вычисляем оставшееся время
        current_time = int(time.time())
        if data["created_at"] > 0:
            remaining_seconds = expiration_time - current_time
            if remaining_seconds > 0:
                remaining_minutes = remaining_seconds // 60
                remaining_secs = remaining_seconds % 60
                if remaining_minutes > 0:
                    time_remaining = f"{remaining_minutes}м {remaining_secs}с"
                else:
                    time_remaining = f"{remaining_secs}с"
                time_class = "time-warning" if remaining_seconds < 60 else "time-active"
                is_active = data["use_count"] < data["max_uses"]
                if is_active:
                    active_count += 1
                else:
                    expired_count += 1
            else:
                time_remaining = "Истекла"
                time_class = "time-expired"
                is_active = False
                expired_count += 1
        else:
            time_remaining = "Не активирована"
            time_class = "time-expired"
            is_active = False
            expired_count += 1
        
        status = "Активна" if is_active else "Истекла"
        status_class = "status-active" if is_active else "status-expired"
        
        html += f"""
            <tr>
                <td><div class="hwid-cell">{hwid}</div></td>
                <td>{data["user_name"]}</td>
                <td>{created_readable}</td>
                <td>{expiration_readable}</td>
                <td>{last_used_readable}</td>
                <td>{data["use_count"]}/{data["max_uses"]}</td>
                <td><div class="time-remaining {time_class}">{time_remaining}</div></td>
                <td class="{status_class}">{status}</td>
                <td>
                    <button class="btn-reset" onclick="resetLicense('{hwid}')">🔄 Сбросить</button>
                    <button class="btn-extend" onclick="extendLicense('{hwid}')">⏰ Продлить</button>
                    <button class="btn-delete" onclick="deleteLicense('{hwid}')">🗑️ Удалить</button>
                </td>
            </tr>
        """
    
    html += f"""
                    </tbody>
                </table>
            </div>
        </div>
        
        <script>
            // Обновляем статистику
            document.getElementById('total-licenses').textContent = '{total_licenses}';
            document.getElementById('active-licenses').textContent = '{active_count}';
            document.getElementById('expired-licenses').textContent = '{expired_count}';
            
            function addLicense() {{
                const hwid = document.getElementById('new_hwid').value;
                const username = document.getElementById('new_username').value;
                const duration = document.getElementById('new_duration').value;
                const maxUses = document.getElementById('new_max_uses').value;
                
                if (!hwid || !username) {{
                    alert('Пожалуйста, заполните HWID и имя пользователя');
                    return;
                }}
                
                fetch('/admin/add_license?key=FloraVisuals2024_Admin_Key_7x9K2mP8qR5', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        hwid: hwid,
                        username: username,
                        duration: parseInt(duration),
                        max_uses: parseInt(maxUses)
                    }})
                }})
                .then(response => response.json())
                .then(data => {{
                    alert(data.message);
                    location.reload();
                }})
                .catch(error => alert('Ошибка: ' + error));
            }}
            
            function resetLicense(hwid) {{
                if (confirm('Сбросить эту лицензию? Это обнулит счетчик использований и время создания.')) {{
                    fetch('/admin/reset_license?key=FloraVisuals2024_Admin_Key_7x9K2mP8qR5', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{hwid: hwid}})
                    }})
                    .then(response => response.json())
                    .then(data => {{
                        alert(data.message);
                        location.reload();
                    }})
                    .catch(error => alert('Ошибка: ' + error));
                }}
            }}
            
            function extendLicense(hwid) {{
                const duration = prompt('Продлить лицензию на сколько минут?', '5');
                if (duration && !isNaN(duration)) {{
                    fetch('/admin/extend_license?key=FloraVisuals2024_Admin_Key_7x9K2mP8qR5', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{hwid: hwid, minutes: parseInt(duration)}})
                    }})
                    .then(response => response.json())
                    .then(data => {{
                        alert(data.message);
                        location.reload();
                    }})
                    .catch(error => alert('Ошибка: ' + error));
                }}
            }}
            
            function deleteLicense(hwid) {{
                if (confirm('Вы уверены, что хотите УДАЛИТЬ эту лицензию? Это действие нельзя отменить!')) {{
                    fetch('/admin/delete_license?key=FloraVisuals2024_Admin_Key_7x9K2mP8qR5', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{hwid: hwid}})
                    }})
                    .then(response => response.json())
                    .then(data => {{
                        alert(data.message);
                        location.reload();
                    }})
                    .catch(error => alert('Ошибка: ' + error));
                }}
            }}
            
            // Автообновление каждые 30 секунд
            setInterval(() => {{
                location.reload();
            }}, 30000);
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
