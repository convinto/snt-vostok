import csv
from datetime import datetime
from app import create_app
from app.models import db, User, Plot, Tariff, MeterReading, Payment

app = create_app()

CSV_FILE = 'plot_36.csv'
PLOT_NUMBER = '36'
DELIMITER = ';'
ENCODING = 'utf-8-sig'          # <- специальная кодировка для CSV с BOM

with app.app_context():
    plot = Plot.query.filter_by(plot_number=PLOT_NUMBER).first()
    if not plot:
        print(f"Участок {PLOT_NUMBER} не найден.")
        exit()
    user = User.query.filter_by(id=plot.user_id).first()
    if not user:
        print(f"К участку {PLOT_NUMBER} не привязан пользователь.")
        exit()

    with open(CSV_FILE, 'r', encoding=ENCODING) as f:
        reader = csv.DictReader(f, delimiter=DELIMITER)
        # Выведем заголовки, чтобы убедиться, что BOM не мешает
        print("Заголовки:", reader.fieldnames)
        rows = list(reader)

    print(f"Найдено строк: {len(rows)}")

    last_tariff_value = None

    for row in rows:
        date_str = row['Дата платежа'].strip()
        try:
            payment_date = datetime.strptime(date_str, '%d.%m.%Y').date()
        except:
            print(f"Неверный формат даты: {date_str}, пропускаем строку")
            continue

        prev_reading = float(row['Предыдущий'].replace(',', '.'))
        curr_reading = float(row['Текущий'].replace(',', '.'))
        volume = float(row['Расчетный объем'].replace(',', '.'))
        price = float(row['Стоимость кВт.ч'].replace(',', '.'))
        paid = float(row['Уплачено, руб.'].replace(',', '.'))

        period = payment_date.strftime('%Y-%m')

        if price != last_tariff_value:
            existing = Tariff.query.filter_by(
                tariff_type='base',
                effective_from=payment_date,
                rate=price
            ).first()
            if not existing:
                tariff = Tariff(
                    tariff_type='base',
                    rate=price,
                    effective_from=payment_date,
                    description=f'Импорт истории участок {PLOT_NUMBER}'
                )
                db.session.add(tariff)
                last_tariff_value = price

        reading = MeterReading(
            user_id=user.id,
            plot_id=plot.id,
            reading_value=curr_reading,
            reading_date=payment_date,
            period=period,
            consumption=volume,
            base_amount=paid,
            losses_amount=0,
            total_amount=paid,
            notes=f'Импорт: пред. {prev_reading}, тек. {curr_reading}',
            is_verified=True
        )
        db.session.add(reading)

        payment = Payment(
            user_id=user.id,
            plot_id=plot.id,
            payment_type='electricity',
            amount=paid,
            payment_date=payment_date,
            period=period,
            payment_method='bank_transfer',
            description=f'Оплата э/э за {period} (импорт)',
            verified_by_admin=True
        )
        db.session.add(payment)

    db.session.commit()
    print(f"Импорт завершён! Загружено {len(rows)} записей.")