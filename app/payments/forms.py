from flask_wtf import FlaskForm
from wtforms import SelectField, FloatField, StringField, SubmitField
from wtforms.validators import DataRequired, NumberRange

class PaymentForm(FlaskForm):
    payment_type = SelectField('Назначение платежа', 
                               choices=[('membership', 'Членские взносы'),
                                        ('electricity', 'Электроэнергия'),
                                        ('target', 'Целевой взнос')],
                               validators=[DataRequired()])
    amount = FloatField('Сумма (руб.)', validators=[DataRequired(), NumberRange(min=1, max=999999)])
    plot_number = StringField('Номер участка')
    submit = SubmitField('Сформировать QR-код')