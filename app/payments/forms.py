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

class PublicPaymentForm(FlaskForm):
    full_name = StringField('ФИО плательщика', validators=[DataRequired(), Length(max=150)])
    plot_number = StringField('Номер участка', validators=[DataRequired(), Length(max=10)])
    payment_type = SelectField('Назначение платежа',
                               choices=[('membership', 'Членские взносы'),
                                        ('target', 'Целевой взнос'),
                                        ('electricity', 'Электроэнергия')],
                               validators=[DataRequired()])
    amount = FloatField('Сумма (руб.)', validators=[DataRequired(), NumberRange(min=1, max=999999)])
    submit = SubmitField('Сформировать QR-код')