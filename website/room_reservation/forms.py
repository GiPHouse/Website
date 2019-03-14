from django.forms import ModelForm, ValidationError
from .models import Reservation
from django.db.models.query_utils import Q
from datetime import timedelta


class ReservationForm(ModelForm):
    """Form for a logged in user to make/update resvation."""

    class Meta:
        model = Reservation
        fields = ('room', 'start_time', 'end_time')

    def clean(self):
        """
        Validate the input by checking:
        - All checks made by ModelForm.
        - Reservation does not collide with another reservation.
        - Reservation is not too long.
        """
        cleaned_data = super().clean()
        room = cleaned_data.get("room")
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        # TODO, on update, this fails because it is probably matched with itself
        already_taken = Reservation.objects.filter(
            Q(
                room=room,
                start_time__lte=start_time,
                end_time__gt=start_time,)
            | Q(
                room=room,
                start_time__lt=end_time,
                end_time__gte=end_time,
            )
            | Q(
                room=room,
                start_time__gte=start_time,
                end_time__lte=end_time,
            )
        ).exists()

        if already_taken:
            raise ValidationError(
                ('Room already reserved in this timeslot.'), code='invalid')

        if end_time - start_time > timedelta(hours=12):
            raise ValidationError(
                ('Rerservation too long. Please shorten your reservation'), code='invalid')

    def __init__(self, *args, **kwargs):
        """
        Initialize the object and
        give user-friendly widgets for the datetime objects.
        """
        super().__init__(*args, **kwargs)

        # TODO have user friendly widgets for datetimes.
        self.fields['start_time'].widget.attrs['placeholder'] = '2000-12-01 23:59'
        self.fields['end_time'].widget.attrs['placeholder'] = '2000-12-01 23:59'
