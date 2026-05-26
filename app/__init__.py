from flask import Flask
from config import Config
from app.extensions import db, login, flask_admin
from app.models import User, Plot, Post, MeterReading, Payment, Accrual, Appeal, Task, TaskStage, Tariff
from app.admin import (UserAdmin, PlotAdmin, PostAdmin, MeterReadingAdmin,
                       PaymentAdmin, AccrualAdmin, AppealAdmin,
                       TaskAdmin, TaskStageAdmin, TariffAdmin)
from flask_migrate import Migrate

migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login.init_app(app)
    flask_admin.init_app(app)
    migrate.init_app(app, db)

    flask_admin.add_view(UserAdmin(User, db.session))
    flask_admin.add_view(PlotAdmin(Plot, db.session))
    flask_admin.add_view(PostAdmin(Post, db.session))
    flask_admin.add_view(TariffAdmin(Tariff, db.session, name='Тарифы'))
    flask_admin.add_view(MeterReadingAdmin(MeterReading, db.session))
    flask_admin.add_view(PaymentAdmin(Payment, db.session))
    flask_admin.add_view(AccrualAdmin(Accrual, db.session, name='Начисления'))
    flask_admin.add_view(AppealAdmin(Appeal, db.session, name='Обращения'))
    flask_admin.add_view(TaskAdmin(Task, db.session, name='Задачи'))
    flask_admin.add_view(TaskStageAdmin(TaskStage, db.session, name='Этапы задач'))

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.dashboard import bp as dashboard_bp
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')

    from app.payments import bp as payments_bp
    app.register_blueprint(payments_bp, url_prefix='/payments')

    from app.appeals import bp as appeals_bp
    app.register_blueprint(appeals_bp, url_prefix='/appeals')

    # Автоматическое создание администратора при первом запуске
    with app.app_context():
        if not User.query.filter_by(is_admin=True).first():
            admin = User(
                username='admin',
                email='admin@snt.ru',
                full_name='Председатель',
                is_admin=True
            )
            admin.set_password('secret')
            db.session.add(admin)
            db.session.commit()
            print("✅ Администратор создан (admin@snt.ru / secret)")

    # Применяем миграции и создаём папку для базы, если используется SQLite
    import os
    if 'sqlite' in app.config.get('SQLALCHEMY_DATABASE_URI', ''):
        data_dir = '/data'
        os.makedirs(data_dir, exist_ok=True)
        from flask_migrate import upgrade as _upgrade
        with app.app_context():
            _upgrade()
    else:
        with app.app_context():
            db.create_all()

    return app