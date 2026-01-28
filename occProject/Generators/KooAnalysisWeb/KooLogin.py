from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, IntegerField, FloatField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, NumberRange

class NameForm(FlaskForm):
    name = StringField('이름', validators=[DataRequired()])
    id = StringField('아이디', validators=[DataRequired()])
    employee_number = IntegerField('사번', validators=[DataRequired()])
    submit = SubmitField('Submit')