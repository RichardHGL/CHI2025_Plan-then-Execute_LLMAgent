from flask_wtf import FlaskForm

from wtforms import SubmitField, RadioField
from wtforms.validators import DataRequired

confidence_choices = [('unconfident', 'unconfident'), ('somewhat unconfident', 'somewhat unconfident'), ('neutral', 'neutral'), ('somewhat confident', 'somewhat confident'), ('confident', 'confident')]

class submit_form(FlaskForm):
    submit_button = SubmitField('Next')


