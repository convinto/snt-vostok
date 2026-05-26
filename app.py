import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Создаём папку для базы
    os.makedirs('/data', exist_ok=True)
    
    # Применяем миграции
    from flask_migrate import upgrade
    with app.app_context():
        upgrade()
    
    # Слушаем порт 80 (Amvera требует именно его для containerPort=80)
    app.run(host='0.0.0.0', port=80)