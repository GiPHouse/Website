from django.contrib.admin import widgets
from django.forms import ModelForm,ValidationError
from django import forms
from .models import Reservation
#from tempus_dominus.widgets import DateTimePicker

class ReservationForm(ModelForm):
    class Meta:
        model = Reservation
        fields = ('room', 'start_time', 'end_time')

    def clean(self):
        cleaned_data = super().clean()
        room = cleaned_data.get("room")
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")
        #TODO, on update, this fails because it probably matched with itself
        already_taken1 = Reservation.objects.filter(
                room=room,
                start_time__lte=start_time,
                end_time__gt=start_time,
                ).exists()

        already_taken2 = Reservation.objects.filter(
                room=room,
                start_time__lt=end_time,
                end_time__gte=end_time,
                )
        already_taken3 = Reservation.objects.filter(
                room=room,
                    start_time__gte=start_time,
                    end_time__lte=end_time,
                )

        if already_taken1 or already_taken1 or already_taken3:
            raise ValidationError(('Room already reserved in this timeslot.'), code='invalid')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


        # TODO have user friendly widgets for datetimes.

        #self.fields['start_time'].widget = widgets.AdminSplitDateTime(
        #        date_attrs={
        #                'placeholder': '2000-12-01',
        #            },
        #        time_attrs={
        #                'placeholder': '23:59'
        #            }
        #        )
        #self.fields['start_time'].widget = DateTimePicker()
        #self.fields['start_time'].widget = DateTimePicker(
        #        options={
        #        'useCurrent': True,
        #        'format': 'YYYY-MM-dd hh:mm',
        #            },
        #        attrs={
        #       'append': 'fa fa-calendar',
        #       'input_toggle': False,
        #       'icon_toggle': True,
        #    })
        #
        #self.fields['start_time'].widget.attrs['placeholder'] = ' 2000-12-01 09:00'
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
