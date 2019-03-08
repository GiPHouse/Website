from django.contrib.admin import widgets
from django.forms import ModelForm
from django import forms
from .models import Reservation
from tempus_dominus.widgets import DateTimePicker

class ReservationForm(ModelForm):
    class Meta:
        model = Reservation
        fields = ('room', 'start_time', 'end_time')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['start_time'].widget = DateTimePicker()
        #self.fields['end_time'].widget = forms.PasswordInput()
        #self.fields['start_time'].input_formats = ['%d/%m/%Y %H:%M']
        #self.fields['start_time'].widget = forms.DateTimeInput(attrs={
        #    'class': 'form-control datetimepicker-input',
        #    'data-target': '#datetimepicker1'
        #})
        #self.fields['end_time'].input_formats = ['%d/%m/%Y %H:%M']
        #self.fields['end_time'].widget = forms.DateTimeInput(attrs={
        #    'class': 'form-control datetimepicker-input',
        #    'data-target': '#datetimepicker2'
        #})
