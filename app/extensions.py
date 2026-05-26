from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_admin import Admin

db = SQLAlchemy()
login = LoginManager()
login.login_view = 'auth.login'
flask_admin = Admin(name='Админ-панель СНТ')  # <-- новое имя