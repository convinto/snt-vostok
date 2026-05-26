import os
from app import create_app

app = create_app()

# Автоматическое создание папки /data и миграции при старте
if __name__ == '__main__':
    # Создаём папку для базы данных, если её нет
    os.makedirs('/data', exist_ok=True)
    
    # Применяем миграции (без импорта Flask-Migrate вручную)
    from flask_migrate import upgrade
    with app.app_context():
        upgrade()
    
    # Запускаем на порту от Amvera или 5000 локально
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)