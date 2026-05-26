from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.payments import bp
from app.payments.forms import PaymentForm
import urllib.parse
from qrcode import QRCode
from qrcode.image.pil import PilImage
from io import BytesIO
import base64

# Реквизиты СНТ
SNT_REQUISITES = {
    'name': 'СНТ «ВОСТОК»',
    'inn': '5031022807',
    'kpp': '503101001',
    'bank': 'ПАО Сбербанк',
    'bik': '044525225',
    'corr_account': '30101810400000000225',
    'account': '40703810040000007056'
}

def escape_qr_string(value):
    """Экранирует спецсимволы для платёжной строки по ГОСТ"""
    value = value.replace('\\', '\\\\')
    value = value.replace('|', '\\|')
    value = value.replace('=', '\\=')
    return value

def generate_payment_qr_string(data):
    """Генерирует платёжную строку по ГОСТ Р 56042-2014"""
    fields = []
    fields.append(f"Name={escape_qr_string(data['receiver'])}")
    fields.append(f"PersonalAcc={data['account']}")
    fields.append(f"BankName={escape_qr_string(data['bank'])}")
    fields.append(f"BIC={data['bik']}")
    fields.append(f"CorrespAcc={data['corr_account']}")
    fields.append(f"PayeeINN={data['inn']}")
    if data.get('kpp'):
        fields.append(f"KPP={data['kpp']}")
    fields.append(f"Sum={int(data['amount'] * 100)}")  # сумма в копейках
    fields.append(f"Purpose={escape_qr_string(data['purpose'])}")
    fields.append(f"LastName={escape_qr_string(data.get('payer_last_name', ''))}")
    fields.append(f"FirstName={escape_qr_string(data.get('payer_first_name', ''))}")
    return '|'.join(['ST00012'] + fields)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = PaymentForm()
    if request.method == 'GET' and current_user.plot:
        form.plot_number.data = current_user.plot.plot_number

    if form.validate_on_submit():
        # Данные платежа
        payment_data = {
            'receiver': SNT_REQUISITES['name'],
            'inn': SNT_REQUISITES['inn'],
            'kpp': SNT_REQUISITES.get('kpp', ''),
            'account': SNT_REQUISITES['account'],
            'bank': SNT_REQUISITES['bank'],
            'bik': SNT_REQUISITES['bik'],
            'corr_account': SNT_REQUISITES['corr_account'],
            'purpose': f"{dict(form.payment_type.choices).get(form.payment_type.data)}, участок {form.plot_number.data}",
            'amount': form.amount.data,
            'plot': form.plot_number.data or '—',
        }

        # Разбираем ФИО плательщика
        if current_user.full_name:
            parts = current_user.full_name.split()
            if len(parts) >= 3:
                payment_data['payer_last_name'] = parts[0]           # Фамилия
                payment_data['payer_first_name'] = ' '.join(parts[1:])  # Имя Отчество
            elif len(parts) == 2:
                payment_data['payer_last_name'] = parts[0]
                payment_data['payer_first_name'] = parts[1]
            else:
                payment_data['payer_last_name'] = parts[0]
                payment_data['payer_first_name'] = ''
        else:
            payment_data['payer_last_name'] = ''
            payment_data['payer_first_name'] = ''

        # Генерируем платёжную строку по ГОСТ
        qr_string = generate_payment_qr_string(payment_data)

        # Генерируем QR-код как PNG в base64
        qr_img = QRCode()
        qr_img.add_data(qr_string)
        qr_img.make(fit=True)
        img = qr_img.make_image(fill_color="black", back_color="white")
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        qr_base64 = base64.b64encode(buffered.getvalue()).decode()

        return render_template('payments/qr.html',
                               title='QR-код для оплаты',
                               payment_data=payment_data,
                               qr_base64=qr_base64,
                               qr_string=qr_string)

    return render_template('payments/create.html',
                           title='Сформировать платеж',
                           form=form)