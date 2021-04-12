from datetime import datetime

from bootstrap_datepicker_plus import DatePickerInput, DateTimePickerInput, TimePickerInput
from django import forms
import re
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from . import models


class DateInput(forms.DateInput):
    input_type = 'date'


class TimeInput(forms.TimeInput):
    input_type = 'time'


class student(UserCreationForm):
    id = forms.CharField(max_length=7, label='Id', widget=forms.TextInput(attrs={'class': 'form-control'}))
    branch = forms.ChoiceField(choices=models.UserProfile.branches, label='Branch')
    year = forms.ChoiceField(choices=models.UserProfile.years, label='Year', widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['id', 'username', 'password1', 'password2']

    def clean(self):
        cd = super().clean()
        if models.UserProfile.objects.filter(id=cd.get('id').capitalize()).first() is not None:
            raise forms.ValidationError('Account with this Id no. already exists\nIf this Id no. belongs to you, report to the mail_id:rahulpinjarla@gmail.com')

        if not re.match(r'[s,S][0-9]{6}', cd.get('id')):
            raise forms.ValidationError('Invalid id no')

        if (cd.get('branch') == 'puc' and (cd.get('year') != ('p1' or 'p2'))) or (cd.get('branch') != 'puc' and (cd.get('year') == ('p1' or 'p2'))):
            raise forms.ValidationError('Invalid year and branch combination ')


class choice(forms.Form):
    choices = []
    choice = forms.CharField(label='ch', max_length=1, widget=forms.RadioSelect(choices=choices))


class new_as(forms.Form):
    as_name = forms.CharField(max_length=200, label='Name of the assignment')
    pub_date = forms.DateTimeField(widget=DateTimePickerInput(), label='Test date and time')
    duration = forms.DurationField(label='Duration(hh:mm:ss)')

    def clean(self):
        pd = super().clean().get('pub_date')
        if pd.replace(tzinfo=None) <= datetime.now():
            raise forms.ValidationError('Test date and time cannot be in past')


class new_qn(forms.Form):
    question = forms.CharField(label='Question', max_length=200, widget=forms.Textarea(attrs={'rows': 4, 'cols': 50}))
    img = forms.ImageField(required=False, label='Image(optional)')
    choices = forms.CharField(label='Choices(Enter all choices as comma separated string eg:option1,option2,option3...)'
                              , max_length=500, widget=forms.Textarea(attrs={'rows': 2, 'cols': 30}))
    answer = forms.IntegerField(label='Answer(Enter the index of one of the choices above eg:if ans is option3, enter 3')

    def clean(self):
        cd = super().clean()
        choices = cd.get('choices').split(',')
        answer = cd.get('answer')
        g = ' or '.join([f'{i+1} if answer is {choices[i]} \n' for i in range(len(choices))])

        if not (0 < answer <= len(choices)):
            raise forms.ValidationError(f'Answer field got an invalid choice index,\n Enter {g}')
