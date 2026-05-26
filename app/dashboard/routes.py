from flask import render_template
from flask_login import login_required, current_user
from app.dashboard import bp
from app import db
from app.models import MeterReading, Payment, Accrual
from sqlalchemy import desc
from datetime import datetime


@bp.route('/')
@login_required
def home():
    user_id = current_user.id
    
    # Последние показания
    latest_reading = MeterReading.query.filter_by(user_id=user_id)\
        .order_by(desc(MeterReading.reading_date)).first()
    
    # Последние 5 показаний
    readings = MeterReading.query.filter_by(user_id=user_id)\
        .order_by(desc(MeterReading.reading_date)).limit(5).all()
    all_readings = MeterReading.query.filter_by(user_id=user_id)\
        .order_by(desc(MeterReading.reading_date)).all()
    
    # Платежи (последние 10)
    payments = Payment.query.filter_by(user_id=user_id)\
        .order_by(desc(Payment.payment_date)).limit(10).all()
    
    # Суммируем начисления по типам
    total_accrued_membership = db.session.query(db.func.sum(Accrual.amount))\
        .filter_by(user_id=user_id, accrual_type='membership').scalar() or 0
    total_accrued_target = db.session.query(db.func.sum(Accrual.amount))\
        .filter_by(user_id=user_id, accrual_type='target').scalar() or 0
    total_accrued_electricity = db.session.query(db.func.sum(Accrual.amount))\
        .filter_by(user_id=user_id, accrual_type='electricity').scalar() or 0

    # Суммируем подтверждённые платежи по типам
    total_paid_membership = db.session.query(db.func.sum(Payment.amount))\
        .filter_by(user_id=user_id, payment_type='membership', verified_by_admin=True).scalar() or 0
    total_paid_target = db.session.query(db.func.sum(Payment.amount))\
        .filter_by(user_id=user_id, payment_type='target', verified_by_admin=True).scalar() or 0
    total_paid_electricity = db.session.query(db.func.sum(Payment.amount))\
        .filter_by(user_id=user_id, payment_type='electricity', verified_by_admin=True).scalar() or 0

    # Балансы
    balance_membership = total_paid_membership - total_accrued_membership  # отрицательный = долг
    balance_target = total_paid_target - total_accrued_target
    balance_electricity = total_paid_electricity - total_accrued_electricity
    
    current_year = datetime.utcnow().year
    
    return render_template('dashboard/home.html',
                           title='Личный кабинет',
                           latest_reading=latest_reading,
                           readings=readings,
                           all_readings=all_readings,
                           payments=payments,
                           balance_membership=balance_membership,
                           balance_target=balance_target,
                           balance_electricity=balance_electricity,
                           current_year=current_year)