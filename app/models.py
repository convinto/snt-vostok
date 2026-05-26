from datetime import datetime, date
from app.extensions import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    is_admin = db.Column(db.Boolean, default=False)
    accruals = db.relationship('Accrual', back_populates='user', lazy='dynamic')
    appeals = db.relationship('Appeal', back_populates='user', lazy='dynamic')

    full_name = db.Column(db.String(150))
    phone = db.Column(db.String(20))
    desired_plot_number = db.Column(db.String(10))
    passport_data = db.Column(db.String(200))
    registration_address = db.Column(db.String(300))

    plot = db.relationship('Plot', back_populates='owner', uselist=False)
    meter_readings = db.relationship('MeterReading', back_populates='user', lazy='dynamic')
    payments = db.relationship('Payment', back_populates='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.full_name or self.username}>'

class Plot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plot_number = db.Column(db.String(10), unique=True, nullable=False)
    cadastral_number = db.Column(db.String(30))
    area = db.Column(db.Float)
    owner_name = db.Column(db.String(150))
    accruals = db.relationship('Accrual', back_populates='plot', lazy='dynamic')
    appeals = db.relationship('Appeal', back_populates='plot', lazy='dynamic')

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)

    # Тарифы (заполняешь ты)
    electricity_tariff = db.Column(db.Float, default=5.50)  # руб/кВт⋅ч
    membership_fee = db.Column(db.Float, default=1500.0)    # руб/год

    owner = db.relationship('User', back_populates='plot')
    meter_readings = db.relationship('MeterReading', back_populates='plot', lazy='dynamic')
    payments = db.relationship('Payment', back_populates='plot', lazy='dynamic')

    def __repr__(self):
        return f'<Plot {self.plot_number}>'

class Tariff(db.Model):
    """Тарифы на электроэнергию (история изменений)"""
    id = db.Column(db.Integer, primary_key=True)
    tariff_type = db.Column(db.String(20), nullable=False)  # 'base' или 'losses'
    rate = db.Column(db.Float, nullable=False)              # руб/кВт⋅ч
    effective_from = db.Column(db.Date, nullable=False)     # с какой даты действует
    description = db.Column(db.String(200))                 # основание (номер приказа)
    
    def __repr__(self):
        return f'<Tariff {self.tariff_type} {self.rate} от {self.effective_from}>'

class MeterReading(db.Model):
    """Показания электросчётчика"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    plot_id = db.Column(db.Integer, db.ForeignKey('plot.id'), nullable=False)
    
    reading_value = db.Column(db.Float, nullable=False)      # текущее показание
    reading_date = db.Column(db.Date, nullable=False)        # дата снятия
    period = db.Column(db.String(7), nullable=False)         # ГГГГ-ММ для группировки
    
    consumption = db.Column(db.Float)                        # расход за период (кВт⋅ч)
    
    # Поля для раздельного учёта
    base_amount = db.Column(db.Float)    # сумма по гос. тарифу
    losses_amount = db.Column(db.Float)  # сумма на покрытие потерь
    total_amount = db.Column(db.Float)   # итоговая сумма
    
    photo_filename = db.Column(db.String(255))
    notes = db.Column(db.Text)
    
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', back_populates='meter_readings')
    plot = db.relationship('Plot', back_populates='meter_readings')

class Payment(db.Model):
    """Зафиксированные платежи"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    plot_id = db.Column(db.Integer, db.ForeignKey('plot.id'), nullable=False)
    
    payment_type = db.Column(db.String(20), nullable=False)   # 'membership', 'electricity', 'target'
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    period = db.Column(db.String(7))                          # за какой период
    payment_method = db.Column(db.String(50), default='bank_transfer')
    
    description = db.Column(db.String(300))                   # из назначения платежа
    verified_by_admin = db.Column(db.Boolean, default=False)  # подтверждён председателем
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', back_populates='payments')
    plot = db.relationship('Plot', back_populates='payments')

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.relationship('User', backref='posts')

    def __repr__(self):
        return f'<Post {self.title}>'
    
class Accrual(db.Model):
    """Начисления (членские, целевые взносы, электроэнергия по показаниям)"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    plot_id = db.Column(db.Integer, db.ForeignKey('plot.id'), nullable=False)
    
    accrual_type = db.Column(db.String(20), nullable=False)   # 'membership', 'target', 'electricity'
    amount = db.Column(db.Float, nullable=False)
    period = db.Column(db.String(7))                           # ГГГГ или ГГГГ-ММ
    description = db.Column(db.String(300))                    # Например, "Членские взносы 2026"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', back_populates='accruals')
    plot = db.relationship('Plot', back_populates='accruals')

class Appeal(db.Model):
    """Обращения/заявления садоводов"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    plot_id = db.Column(db.Integer, db.ForeignKey('plot.id'))        # необязательно
    subject = db.Column(db.String(200), nullable=False)              # тема
    body = db.Column(db.Text, nullable=False)                        # текст
    status = db.Column(db.String(20), default='new')                 # new, in_progress, closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='appeals')
    plot = db.relationship('Plot', back_populates='appeals')

class Task(db.Model):
    """Задачи/проекты СНТ"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='planned')  # planned, in_progress, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    stages = db.relationship('TaskStage', backref='task', lazy='dynamic',
                             order_by='TaskStage.order')

    def __repr__(self):
        return f'<Task {self.title}>'


class TaskStage(db.Model):
    """Этапы выполнения задачи"""
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    planned_cost = db.Column(db.Float, default=0.0)
    actual_cost = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='planned')
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))