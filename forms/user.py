from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, BooleanField, SelectField, FileField, IntegerField, \
    FieldList, FormField
from wtforms.validators import DataRequired


class RegisterForm(FlaskForm):
    name = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    user_type = SelectField('Выберите роль', choices=[('ученик', 'Ученик'), ('учитель', 'Учитель')],
                            validators=[DataRequired()])
    submit = SubmitField('Войти')


class LoginForm(FlaskForm):
    name = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class LevelEntryForm(FlaskForm):
    word = StringField('Слово', validators=[DataRequired()], render_kw={"class": "form-control", "maxlength": "100"})
    translation = StringField('Перевод', validators=[DataRequired()],
                              render_kw={"class": "form-control", "maxlength": "100"})
    image = FileField('Изображение', validators=[DataRequired()], render_kw={"class": "form-control"})


class LevelForm(FlaskForm):
    level_name = StringField('Название уровня', validators=[DataRequired()],
                             render_kw={"class": "form-control", "maxlength": "100"})
    number_of_levels = IntegerField('Количество частей', validators=[DataRequired()],
                                    render_kw={"class": "form-control", "min": "1"})
    levels = FieldList(FormField(LevelEntryForm), min_entries=1)
    submit = SubmitField('Добавить уровень', render_kw={"class": "btn btn-primary"})
