from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, DateField
from wtforms.validators import DataRequired


class ScraperForm(FlaskForm):
    pass


class BasicButtonForm(FlaskForm):
    pass


class DownloadPasteForm(FlaskForm):
    pass


class SearchForm(FlaskForm):
    search_terms = StringField('search_terms', validators=[DataRequired()])


class DateForm(FlaskForm):
    date = DateField('date')
