import secrets
from datetime import datetime, date
from flask import flash, Response
from flask_admin.actions import action
from flask_admin.contrib.sqla import ModelView
from wtforms import PasswordField, DateField, SelectField
from app.models import User, Plot, Post, MeterReading, Payment, Appeal
from app.extensions import db
import csv
from io import StringIO
from app.services import get_active_tariffs
from app.models import Tariff
from flask import current_app
from app.models import Accrual
from app.models import Task, TaskStage

class AdminModelView(ModelView):
    def is_accessible(self):
        from flask_login import current_user
        return current_user.is_authenticated and current_user.is_admin

class UserAdmin(AdminModelView):
    column_list = ('id', 'full_name', 'username', 'email', 'phone',
                   'desired_plot_number', 'is_admin', 'plot')
    form_columns = ('username', 'email', 'full_name', 'phone',
                    'desired_plot_number', 'passport_data',
                    'registration_address', 'new_password', 'is_admin', 'plot')
    form_extra_fields = {
        'new_password': PasswordField('Новый пароль')
    }
    column_searchable_list = ('full_name', 'username', 'email', 'phone', 'desired_plot_number')

    # У UserAdmin НЕ должно быть on_model_change для показаний, здесь только сброс пароля
    def on_model_change(self, form, model, is_created):
        if form.new_password.data:
            model.set_password(form.new_password.data)

    @action('reset_password', 'Сбросить пароль', 'Вы уверены?')
    def action_reset_password(self, ids):
        new_passwords = {}
        for user_id in ids:
            user = User.query.get(user_id)
            if user:
                new_password = secrets.token_urlsafe(8)
                user.set_password(new_password)
                new_passwords[user.full_name or user.username] = new_password
        db.session.commit()
        msg = 'Новые пароли:<br>' + '<br>'.join(
            f'{name}: <code>{pwd}</code>' for name, pwd in new_passwords.items()
        )
        flash(msg, 'info')

class PlotAdmin(AdminModelView):
    column_list = ('id', 'plot_number', 'cadastral_number', 'area', 'owner_name', 'owner',
                   'electricity_tariff', 'membership_fee')
    form_columns = ('plot_number', 'cadastral_number', 'area', 'owner_name', 'owner',
                    'electricity_tariff', 'membership_fee')
    column_searchable_list = ('plot_number', 'cadastral_number', 'owner_name')

class PostAdmin(AdminModelView):
    column_list = ('title', 'author', 'created_at')
    form_columns = ('title', 'body', 'author')
    column_searchable_list = ('title',)

    def on_model_change(self, form, model, is_created):
        if is_created:
            from flask_login import current_user
            model.author = current_user

class MeterReadingAdmin(AdminModelView):
    column_list = ('id', 'user', 'plot', 'period', 'reading_value', 
                   'consumption', 'base_amount', 'losses_amount', 'total_amount', 'is_verified')
    form_columns = ('user', 'plot', 'reading_value', 'reading_date', 'period',
                    'photo_filename', 'notes', 'is_verified')
    column_searchable_list = ('user.full_name', 'plot.plot_number', 'period')
    column_filters = ('is_verified', 'period', 'plot.plot_number')
    
    def on_model_change(self, form, model, is_created):
        # Приводим reading_value к float на случай, если оно Decimal
        reading_value = float(model.reading_value) if model.reading_value else None

        if not reading_value or not model.plot_id:
            model.consumption = 0
            model.base_amount = 0
            model.losses_amount = 0
            model.total_amount = 0
            return

        # Ищем предыдущее показание
        prev = MeterReading.query.filter_by(
            plot_id=model.plot_id
        ).filter(
            MeterReading.id != model.id
        ).order_by(
            MeterReading.reading_date.desc()
        ).first()

        if not prev or not prev.reading_value:
            model.consumption = 0
            model.base_amount = 0
            model.losses_amount = 0
            model.total_amount = 0
            return

        prev_reading = float(prev.reading_value)
        consumption = reading_value - prev_reading
        if consumption < 0:
            consumption = 0
        model.consumption = consumption

        # Тарифы на дату показаний
        calc_date = model.reading_date if model.reading_date else date.today()
        tariffs = get_active_tariffs(calc_date)

        if consumption > 0:
            model.base_amount = round(consumption * tariffs['base'], 2)
            model.losses_amount = round(consumption * tariffs['losses'], 2)
            model.total_amount = round(model.base_amount + model.losses_amount, 2)
        else:
            model.base_amount = 0
            model.losses_amount = 0
            model.total_amount = 0

    @action('recalculate', 'Пересчитать', 'Вы уверены? Все выбранные показания будут пересчитаны.')
    def action_recalculate(self, ids):
        from app.services import get_active_tariffs
        from datetime import date
        
        for reading_id in ids:
            reading = MeterReading.query.get(reading_id)
            if not reading or not reading.plot:
                continue
            
            # Приводим к float
            reading_val = float(reading.reading_value) if reading.reading_value else None
            
            # Находим предыдущее показание
            prev = MeterReading.query.filter_by(
                plot_id=reading.plot_id
            ).filter(
                MeterReading.id != reading.id,
                MeterReading.reading_date < reading.reading_date
            ).order_by(MeterReading.reading_date.desc()).first()
            
            if prev and prev.reading_value and reading_val:
                prev_val = float(prev.reading_value)
                consumption = reading_val - prev_val
                if consumption < 0:
                    consumption = 0
            else:
                consumption = 0
            
            reading.consumption = consumption
            
            # Считаем суммы по тарифам
            calc_date = reading.reading_date if reading.reading_date else date.today()
            tariffs = get_active_tariffs(calc_date)
            if consumption > 0:
                reading.base_amount = round(consumption * tariffs['base'], 2)
                reading.losses_amount = round(consumption * tariffs['losses'], 2)
                reading.total_amount = round(reading.base_amount + reading.losses_amount, 2)
            else:
                reading.base_amount = 0
                reading.losses_amount = 0
                reading.total_amount = 0
        
        db.session.commit()
        flash(f'Пересчитано показаний: {len(ids)}')

    @action('export_csv', 'Выгрузить в CSV', 'Экспортировать выбранные показания?')
    def action_export_csv(self, ids):
        readings = MeterReading.query.filter(MeterReading.id.in_(ids)).all()
        si = StringIO()
        cw = csv.writer(si)
        cw.writerow(['ID', 'Участок', 'ФИО', 'Дата', 'Период', 'Показание', 
                     'Расход, кВт⋅ч', 'Гос. тариф, руб', 'Потери, руб', 'ИТОГО, руб', 'Подтверждено'])
        for r in readings:
            cw.writerow([
                r.id, r.plot.plot_number if r.plot else '',
                r.user.full_name if r.user else '',
                r.reading_date, r.period, r.reading_value,
                r.consumption,
                r.base_amount, r.losses_amount, r.total_amount,
                'Да' if r.is_verified else 'Нет'
            ])
        output = si.getvalue()
        return Response(output, mimetype='text/csv',
                       headers={'Content-Disposition': 'attachment; filename=meter_readings.csv'})

class PaymentAdmin(AdminModelView):
    column_list = ('id', 'user', 'plot', 'payment_type', 'amount', 'payment_date', 
                   'period', 'verified_by_admin')
    form_columns = ('user', 'plot', 'payment_type', 'amount', 'payment_date', 'period',
                    'payment_method', 'description', 'verified_by_admin')
    column_searchable_list = ('user.full_name', 'plot.plot_number', 'period')
    column_filters = ('payment_type', 'verified_by_admin', 'period', 'plot.plot_number')
    
    form_extra_fields = {
        'payment_type': SelectField('Тип платежа', choices=[
            ('membership', 'Членские взносы'),
            ('electricity', 'Электроэнергия'),
            ('target', 'Целевой взнос')
        ])
    }

    @action('export_csv', 'Выгрузить в CSV', 'Экспортировать выбранные платежи?')
    def action_export_csv(self, ids):
        payments = Payment.query.filter(Payment.id.in_(ids)).all()
        si = StringIO()
        cw = csv.writer(si)
        cw.writerow(['ID', 'Участок', 'ФИО', 'Тип', 'Сумма', 'Дата', 'Период', 
                     'Назначение', 'Подтверждён'])
        for p in payments:
            cw.writerow([
                p.id, p.plot.plot_number if p.plot else '',
                p.user.full_name if p.user else '',
                p.payment_type, p.amount, p.payment_date, p.period,
                p.description, 'Да' if p.verified_by_admin else 'Нет'
            ])
        output = si.getvalue()
        return Response(output, mimetype='text/csv',
                       headers={'Content-Disposition': 'attachment; filename=payments.csv'})
    
class TariffAdmin(AdminModelView):
    column_list = ('id', 'tariff_type', 'rate', 'effective_from', 'description')
    form_columns = ('tariff_type', 'rate', 'effective_from', 'description')
    column_labels = {
        'tariff_type': 'Тип',
        'rate': 'Ставка (руб/кВт⋅ч)',
        'effective_from': 'Действует с',
        'description': 'Основание'
    }
    form_choices = {
        'tariff_type': [
            ('base', 'Гос. тариф'),
            ('losses', 'Потери в сетях')
        ]
    }

class AccrualAdmin(AdminModelView):
    column_list = ('id', 'user', 'plot', 'accrual_type', 'amount', 'period', 'description')
    form_columns = ('user', 'plot', 'accrual_type', 'amount', 'period', 'description')
    column_searchable_list = ('user.full_name', 'plot.plot_number', 'period')
    column_filters = ('accrual_type', 'period')
    
    form_choices = {
        'accrual_type': [
            ('membership', 'Членские взносы'),
            ('target', 'Целевые взносы'),
            ('electricity', 'Электроэнергия')
        ]
    }

    # Массовое создание начислений для всех участков
    @action('create_mass', 'Создать начисления всем', 
            'Создать начисления указанного типа для всех участков?')
    def action_create_mass(self, ids):
        # Этот метод будет вызываться из формы, пока сделаем через отдельный маршрут,
        # но в админке можно просто создать запись через стандартную форму.
        pass  # Позже добавим отдельную страницу для массовых операций

class AppealAdmin(AdminModelView):
    column_list = ('id', 'user', 'plot', 'subject', 'status', 'created_at')
    form_columns = ('user', 'plot', 'subject', 'body', 'status')
    column_searchable_list = ('subject', 'user.full_name')
    column_filters = ('status',)
    form_choices = {
        'status': [
            ('new', 'Новое'),
            ('in_progress', 'В обработке'),
            ('closed', 'Закрыто')
        ]
    }

class TaskAdmin(AdminModelView):
    column_list = ('id', 'title', 'status', 'updated_at')
    form_columns = ('title', 'description', 'status')
    form_choices = {
        'status': [
            ('planned', 'Запланировано'),
            ('in_progress', 'В процессе'),
            ('completed', 'Завершено')
        ]
    }

class TaskStageAdmin(AdminModelView):
    column_list = ('id', 'task', 'title', 'status', 'planned_cost', 'actual_cost', 'order')
    form_columns = ('task', 'title', 'description', 'status', 'planned_cost', 'actual_cost', 'order')
    form_choices = {
        'status': [
            ('planned', 'Запланирован'),
            ('in_progress', 'Выполняется'),
            ('completed', 'Завершён')
        ]
    }