import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, current_app
)
from werkzeug.security import check_password_hash, generate_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, RadioField, IntegerRangeField, TextAreaField
from wtforms.validators import DataRequired
from wtforms.validators import StopValidation, NumberRange

class OptionRequired(object):
    """
    Checks the field's data is 'truthy' otherwise stops the validation chain.

    This validator checks that the ``data`` attribute on the field is a 'true'
    value (effectively, it does ``if field.data``.) Furthermore, if the data
    is a string type, a string containing only whitespace characters is
    considered false.

    If the data is empty, also removes prior errors (such as processing errors)
    from the field.

    **NOTE** this validator used to be called `Required` but the way it behaved
    (requiring coerced data, not input data) meant it functioned in a way
    which was not symmetric to the `Optional` validator and furthermore caused
    confusion with certain fields which coerced data to 'falsey' values like
    ``0``, ``Decimal(0)``, ``time(0)`` etc. Unless a very specific reason
    exists, we recommend using the :class:`InputRequired` instead.

    :param message:
        Error message to raise in case of a validation error.
    """
    field_flags = ('required', )

    def __init__(self, message=None):
        self.message = message

    def __call__(self, form, field):
        print(field, field.data)
        if int(field.data) == 0:
            if self.message is None:
                message = field.gettext('Must choose an option in this field.')
            else:
                message = self.message

            field.errors[:] = []
            raise StopValidation(message)

# ATI_choices = [('completely disagree', 'completely disagree'), ('largely disagree', 'largely disagree'), ('slightly disagree', 'slightly disagree'), ('slightly agree', 'slightly agree'), ('largely agree', 'largely agree'), ('completely agree', 'completely agree')]
ATI_choices = choices=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6')]
class ATIForm(FlaskForm):
    answer_1 = RadioField('I like to occupy myself in greater detail with technical systems.', choices=ATI_choices, validators=[DataRequired()])
    answer_2 = RadioField('I like testing the functions of new technical systems.', choices=ATI_choices, validators=[DataRequired()])
    answer_3 = RadioField('I predominantly deal with technical systems because I have to.', choices=ATI_choices, validators=[DataRequired()])
    answer_4 = RadioField('When I have a new technical system in front of me, I try it out intensively.', choices=ATI_choices, validators=[DataRequired()])
    answer_5 = RadioField('I enjoy spending time becoming acquainted with a new technical system.', choices=ATI_choices, validators=[DataRequired()])
    answer_6 = RadioField('It is enough for me that a technical system works; I don’t care how or why.', choices=ATI_choices, validators=[DataRequired()])
    
    answer_7 = RadioField('I try to understand how a technical system exactly works.', choices=ATI_choices, validators=[DataRequired()])
    answer_8 = RadioField('It is enough for me to know the basic functions of a technical system.', choices=ATI_choices, validators=[DataRequired()])
    answer_9 = RadioField('I try to make full use of the capabilities of a technical system.', choices=ATI_choices, validators=[DataRequired()])
    answer_10 = RadioField('Attention check: choose option completely agree.', choices=ATI_choices, validators=[DataRequired()])

    submit_button = SubmitField('Submit')

TiA_choices = [('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')]

class TiA_Form(FlaskForm):
    # Reliability/Competence
    answer_1 = RadioField('The system is capable of interpreting situations correctly.', choices=TiA_choices, validators=[DataRequired()])
    answer_6 = RadioField('The system works reliably.', choices=TiA_choices, validators=[DataRequired()])
    answer_10 = RadioField('A system malfunction is likely.', choices=TiA_choices, validators=[DataRequired()])
    answer_13 = RadioField('The system is capable of taking over complicated tasks.', choices=TiA_choices, validators=[DataRequired()])
    answer_15 = RadioField('The system might make sporadic errors.', choices=TiA_choices, validators=[DataRequired()])
    answer_19 = RadioField('I am confident about the system’s capabilities.', choices=TiA_choices, validators=[DataRequired()])

    # Understanding/Predictability
    answer_2 = RadioField('The system state was always clear to me.', choices=TiA_choices, validators=[DataRequired()])
    answer_7 = RadioField('The system reacts unpredictably.', choices=TiA_choices, validators=[DataRequired()])
    answer_11 = RadioField('I was able to understand why things happened.', choices=TiA_choices, validators=[DataRequired()])
    answer_16 = RadioField('It’s difficult to identify what the system will do next.', choices=TiA_choices, validators=[DataRequired()])

    # Familiarity
    answer_3 = RadioField('I already know similar systems.', choices=TiA_choices, validators=[DataRequired()])
    answer_17 = RadioField('I have already used similar systems.', choices=TiA_choices, validators=[DataRequired()])

    # Attention check
    answer_20 = RadioField('Choose option strongly disagree.', choices=TiA_choices, validators=[DataRequired()])

    # Intention of Developers
    answer_4 = RadioField('The developers are trustworthy.', choices=TiA_choices, validators=[DataRequired()])
    answer_8 = RadioField('The developers take my well-being seriously.', choices=TiA_choices, validators=[DataRequired()])

    # Propensity to Trust
    answer_5 = RadioField('One should be careful with unfamiliar automated systems.', choices=TiA_choices, validators=[DataRequired()])
    answer_12 = RadioField('I rather trust a system than I mistrust it.', choices=TiA_choices, validators=[DataRequired()])
    answer_18 = RadioField('Automated systems generally work well.', choices=TiA_choices, validators=[DataRequired()])
    
    # Trust in Automation
    answer_9 = RadioField('I trust the system.', choices=TiA_choices, validators=[DataRequired()])
    answer_14 = RadioField('I can rely on the system.', choices=TiA_choices, validators=[DataRequired()])

    submit_button = SubmitField('Submit')

class NasatlxForm(FlaskForm):
    # mental_demand = DecimalRangeField('How mentally demanding was the task?', choices=nasa_choices, validators=[DataRequired()])
    mental_demand = IntegerRangeField('1. How mentally demanding was the task?', validators=[DataRequired(), NumberRange(min=-7, max=7)], 
        render_kw={"oninput": "updateTextInput('mental_demand_value', this.value);", "onchange": "updateTextInput('mental_demand_value', this.value);"})
    physical_demand = IntegerRangeField('2. How physically demanding was the task?', validators=[DataRequired(), NumberRange(min=-7, max=7)], 
        render_kw={"oninput": "updateTextInput('physical_demand_value', this.value);", "onchange": "updateTextInput('physical_demand_value', this.value);"})
    temporal_demand = IntegerRangeField('3. How hurried or rushed was the pace of task?', validators=[DataRequired(), NumberRange(min=-7, max=7)], 
        render_kw={"oninput": "updateTextInput('temporal_demand_value', this.value);", "onchange": "updateTextInput('temporal_demand_value', this.value);"})
    performance = IntegerRangeField('4. How successful were you in accomplishing what you were asked to do?', validators=[DataRequired(), NumberRange(min=-7, max=7)], 
        render_kw={"oninput": "updateTextInput('performance_value', this.value);", "onchange": "updateTextInput('performance_value', this.value);"})
    effort = IntegerRangeField('5. How hard did you have to work to accomplish your level of performance?', validators=[DataRequired(), NumberRange(min=-7, max=7)], 
        render_kw={"oninput": "updateTextInput('effort_value', this.value);", "onchange": "updateTextInput('effort_value', this.value);"})
    frustration = IntegerRangeField('6. How insecure, discouraged, irritated, stressed, and annoyed were you?', validators=[DataRequired(), NumberRange(min=-7, max=7)], 
        render_kw={"oninput": "updateTextInput('frustration_value', this.value);", "onchange": "updateTextInput('frustration_value', this.value);"})
    submit_button = SubmitField('Submit')

class PostFrom(FlaskForm):
    answer_1 = StringField('1 + 1 = ', validators=[DataRequired()])
    answer_2 = StringField('2 + 2 = ', validators=[DataRequired()])
    answer_3 = StringField('3 + 3 = ', validators=[DataRequired()])
    answer_4 = StringField('4 + 4 = ', validators=[DataRequired()])
    submit_button = SubmitField('Submit')

class planning_form(FlaskForm):
    submit_button = SubmitField('Plan looks nice, move forward to execution',render_kw={"onclick": "updateplan()", "class": "btn btn-success btn-block"})

expertise_list = [('1', '1: No prior experience/knowledge'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5: Extensive prior experience/knowledge')]

class ExpertiseForm(FlaskForm):
    # llm_expertise = IntegerRangeField('1. To what extent are you familiar with large language models?', validators=[OptionRequired(), NumberRange(min=1, max=5)],  render_kw={"oninput": "updateTextInput('llm_expertise_value', this.value);", "onchange": "updateTextInput('llm_expertise_value', this.value);"})
    llm_expertise = RadioField('To what extent are you familiar with large language models (e.g., ChatGPT)?', choices=expertise_list, validators=[DataRequired()])
    assistant_expertise = RadioField('Do you have any experience or knowledge in working with automation assistant (e.g., Siri, Alexa, Copilot)?', choices=expertise_list, validators=[DataRequired()])
    # assistant_expertise = IntegerRangeField('2. Do you have any experience or knowledge in working with automation assistant?', validators=[OptionRequired(), NumberRange(min=1, max=5)], render_kw={"oninput": "updateTextInput('assistant_expertise_value', this.value);", "onchange": "updateTextInput('assistant_expertise_value', this.value);"})
    submit_button = SubmitField('Submit')

binary_correctness = [('Yes', 'Yes, I think the execution addresses all requirements of the task instruction'), ('No', 'No, I think something is missing or wrong with the execution process')]
confidence_choices = [('unconfident', 'unconfident'), ('somewhat unconfident', 'somewhat unconfident'), ('neutral', 'neutral'), ('somewhat confident', 'somewhat confident'), ('confident', 'confident')]
class ExecutionForm(FlaskForm):
    correctness = RadioField('Do you trust that the execution process can provide a correct outcome based on the task instructions?', choices=binary_correctness, validators=[DataRequired()])
    confidence = RadioField('How confident are you with your judgement above of the execution process? ', choices=confidence_choices, validators=[DataRequired()])
    submit_button = SubmitField('Submit')

binary_correctness_ = [('Yes', 'Yes, I think this plan addresses all requirements of the task instruction'), ('No', 'No, I think something is missing or wrong with the plan')]
class PlanningForm(FlaskForm):
    correctness = RadioField('Do you trust that the execution of this plan can provide a correct outcome based on the task instructions?', choices=binary_correctness_, validators=[DataRequired()])
    confidence = RadioField('How confident are you with your judgement above of the execution of this plan? ', choices=confidence_choices, validators=[DataRequired()])
    submit_button = SubmitField('Plan looks nice, move forward to execution',render_kw={"onclick": "updateplan()", "class": "btn btn-success btn-block"})

answer_list_1 = [('1', 'only one'), ('2', 'more than one')]
answer_list_2 = [('1', 'When you find some steps are missing'), ('2', 'When you find some steps are redudant'), ('3', 'When you find one primary step can be transformed to more than one action')]
class QualificationForm_1(FlaskForm):
    question_1 = RadioField('Each primary step (1. or x.) can be transformed to how many actions in the execution stage?', choices=answer_list_1, validators=[DataRequired()])
    question_2 = RadioField('When should participants use Split step in the planning stage?', choices=answer_list_2, validators=[DataRequired()])
    submit_button = SubmitField('Submit')

answer_list_3 = [('1', 'Edit the plan'), ('2', 'Nothing'), ('3', 'Provide feedback to the plan')]
class QualificationForm_2(FlaskForm):
    question_1 = RadioField('Each primary step (1. or x.) can be transformed to how many actions in the execution stage?', choices=answer_list_1, validators=[DataRequired()])
    question_2 = RadioField('What can you do in the planning stage?', choices=answer_list_3, validators=[DataRequired()])
    submit_button = SubmitField('Submit')

class FeedbackForm(FlaskForm):
    planning_feedback = TextAreaField('Please share any comments, remarks or suggestions regarding the planning stage of LLM Assistant.', validators=[DataRequired()])
    execution_feedback = TextAreaField('Please share any comments, remarks or suggestions regarding the execution stage of LLM Assistant.', validators=[DataRequired()])
    other_feedback = TextAreaField('Besides above feedback, any other comments, remarks or suggestions regarding the study?', validators=[DataRequired()])
    submit_button = SubmitField('Submit')

def flash_errors(form):
    """Flashes form errors"""
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"Error in the %s field - %s" % (
                getattr(form, field).label.text,
                error
            ), 'error')

