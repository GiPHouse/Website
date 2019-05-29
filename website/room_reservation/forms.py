from django import forms
from django.db.models.query_utils import Q
from django.forms import ModelForm, ValidationError
from django.utils import timezone

from room_reservation.models import Reservation


class ReservationForm(ModelForm):
    """Form for a logged in user to make/update reservation."""

    pk = forms.IntegerField(widget=forms.HiddenInput(),
                            initial=None, required=False)

    class Meta:
        """Meta class for ReservationForm."""

        model = Reservation
        fields = ('room', 'start_time', 'end_time')

    def clean(self):
        """
        Validate the input for the reservation.

        By checking:

        - All checks made by ModelForm.
        - Reservation does not collide with another reservation.
        - Reservation is not too long.
        """
        cleaned_data = super().clean()
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if end_time.date() - start_time.date() >= timezone.timedelta(days=1):
            raise ValidationError('Reservation too long. Please shorten your reservation', code='invalid')

        if start_time >= end_time:
            raise ValidationError('Start time needs to be before end time.', code='invalid')

        if start_time.hour < 8 or start_time.hour >= 18 or end_time.hour < 8 or start_time.hour > 18:
            raise ValidationError('Please enter times between 8:00 and 18:00.', code='invalid')

        already_taken = (
            Reservation.objects
            .filter(room=cleaned_data.get("room"))
            .filter(
                Q(start_time__lte=start_time, end_time__gt=start_time)
                | Q(start_time__lt=end_time, end_time__gte=end_time)
                | Q(start_time__gte=start_time, end_time__lte=end_time)
            )
            .exclude(pk=cleaned_data.get("pk"))
            .exists()
        )

        if already_taken:
            raise ValidationError('Room already reserved in this timeslot.', code='invalid')

    def __init__(self, *args, **kwargs):
        """Initialize the object and give user-friendly widgets for the datetime objects."""
        super().__init__(*args, **kwargs)

        self.fields['start_time'].widget.attrs['placeholder'] = '2000-12-01 23:59'
        self.fields['end_time'].widget.attrs['placeholder'] = '2000-12-01 23:59'
