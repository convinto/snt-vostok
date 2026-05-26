from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length

class AppealForm(FlaskForm):
    subject = StringField('Тема обращения', validators=[DataRequired(), Length(max=200)])
    body = TextAreaField('Текст обращения', validators=[DataRequired()])
    submit = SubmitField('Отправить')