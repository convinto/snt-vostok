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
    
    # Получаем порт от Amvera (она передаёт его в переменной PORT)
    port = int(os.environ.get('PORT', 5000))
    print(f"ПРИЛОЖЕНИЕ СТАРТУЕТ НА ПОРТУ: {port}", flush=True)
    
    app.run(host='0.0.0.0', port=port)