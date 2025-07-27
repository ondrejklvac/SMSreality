from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField, PasswordField, TextAreaField, IntegerField,
    BooleanField, SubmitField, SelectField
)
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange

# ——— PŮVODNÍ TŘÍDY —————————————————————————————————————————————————————————

class LoginForm(FlaskForm):
    email    = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Heslo', validators=[DataRequired()])
    remember = BooleanField('Zapamatovat si mě')
    submit   = SubmitField('Přihlásit se')

class SetPasswordForm(FlaskForm):
    password         = PasswordField('Heslo', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Potvrdit heslo', validators=[DataRequired(), EqualTo('password')])
    submit           = SubmitField('Nastavit heslo')

class ProductForm(FlaskForm):
    name        = StringField('Název', validators=[DataRequired()])
    description = TextAreaField('Popis', validators=[DataRequired()])
    price       = IntegerField('Cena (Kč)', validators=[DataRequired(), NumberRange(min=1)])
    is_active   = BooleanField('Aktivní', default=True)
    image       = FileField('Obrázek', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit      = SubmitField('Uložit')

class UserForm(FlaskForm):
    first_name = StringField('Jméno', validators=[DataRequired()])
    last_name  = StringField('Příjmení', validators=[DataRequired()])
    email      = StringField('E-mail', validators=[DataRequired(), Email()])
    credits    = IntegerField('Kredity', validators=[NumberRange(min=0)])
    is_admin   = BooleanField('Administrátor')
    submit     = SubmitField('Uložit')

class CheckoutForm(FlaskForm):
    shipping_address = TextAreaField(
        'Doručovací adresa *',
        validators=[
            DataRequired(message="Zadejte prosím doručovací adresu.")
        ]
    )
    shipping_method = SelectField(
        'Způsob doručení *',
        coerce=int,
        validators=[
            DataRequired(message="Vyberte prosím způsob doručení.")
        ]
    )
    accept_terms = BooleanField(
        'Souhlasím s obchodními podmínkami *',
        validators=[
            DataRequired(message="Musíte souhlasit s podmínkami.")
        ]
    )
    submit = SubmitField('Dokončit objednávku')

    class Meta:
        csrf = False


# ——— NOVÉ TŘÍDY PRO APP.PY ——————————————————————————————————————————————————————

class RegistrationForm(FlaskForm):
    first_name       = StringField('Jméno', validators=[DataRequired(), Length(min=2, max=30)])
    last_name        = StringField('Příjmení', validators=[DataRequired(), Length(min=2, max=30)])
    email            = StringField('E-mail', validators=[DataRequired(), Email()])
    password         = PasswordField('Heslo', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Potvrdit heslo', validators=[DataRequired(), EqualTo('password')])
    submit           = SubmitField('Registrovat se')

class UpdateAccountForm(FlaskForm):
    first_name = StringField('Jméno', validators=[DataRequired(), Length(min=2, max=30)])
    last_name  = StringField('Příjmení', validators=[DataRequired(), Length(min=2, max=30)])
    email      = StringField('E-mail', validators=[DataRequired(), Email()])
    submit     = SubmitField('Aktualizovat profil')

class CategoryForm(FlaskForm):
    name   = StringField('Název kategorie', validators=[DataRequired()])
    submit = SubmitField('Uložit')

class ShippingForm(FlaskForm):
    name        = StringField('Název dopravy', validators=[DataRequired()])
    description = TextAreaField('Popis dopravy', validators=[DataRequired()])
    price       = IntegerField('Cena (Kč)', validators=[DataRequired(), NumberRange(min=0)])
    submit      = SubmitField('Uložit')
