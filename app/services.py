# app/services.py
from datetime import date
from app.models import Tariff

def get_active_tariffs(calculation_date=None):
    """
    Возвращает активные тарифы на указанную дату.
    Если дата не указана, берётся сегодня.
    Возвращает словарь: {'base': rate, 'losses': rate}
    """
    if calculation_date is None:
        calculation_date = date.today()
        
    # Находим последний 'base' тариф, действующий на дату
    base_tariff = Tariff.query.filter(
        Tariff.tariff_type == 'base',
        Tariff.effective_from <= calculation_date
    ).order_by(Tariff.effective_from.desc()).first()
    
    # То же самое для 'losses'
    losses_tariff = Tariff.query.filter(
        Tariff.tariff_type == 'losses',
        Tariff.effective_from <= calculation_date
    ).order_by(Tariff.effective_from.desc()).first()
    
    return {
        'base': base_tariff.rate if base_tariff else 0,
        'losses': losses_tariff.rate if losses_tariff else 0
    }