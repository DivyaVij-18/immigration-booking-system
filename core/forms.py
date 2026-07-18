import re

from django import forms
from django.core.exceptions import ValidationError

from .models import Booking, Slot


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['full_name', 'email', 'phone', 'office', 'slot']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your full name',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email address',
                'required': True,
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your phone number',
                'id': 'id_phone',
                'required': True,
            }),
            'office': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_office',
            }),
            'slot': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_slot',
            }),
        }

    def __init__(self, *args, **kwargs):
        initial_office = kwargs.pop('initial_office', None)
        super().__init__(*args, **kwargs)

        self.fields['slot'].queryset = Slot.objects.none()
        self.fields['slot'].empty_label = 'Select an available slot'

        office_id = None
        if self.data.get('office'):
            try:
                office_id = int(self.data.get('office'))
            except (ValueError, TypeError):
                pass
        elif initial_office:
            office_id = initial_office

        if office_id:
            self.fields['office'].initial = office_id
            self.fields['slot'].queryset = Slot.objects.filter(
                office_id=office_id,
                available=True,
            )

    def clean_slot(self):
        slot = self.cleaned_data['slot']
        if not slot.available:
            raise ValidationError('This slot is no longer available.')
        office = self.cleaned_data.get('office')
        if office and slot.office_id != office.id:
            raise ValidationError('Selected slot does not belong to the chosen office.')
        return slot

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()

        print("PHONE RECEIVED:", repr(phone))

        if not phone:
            raise ValidationError("Phone number is required.")

        return phone

class PaymentForm(forms.Form):
    card_holder = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Name on card',
        }),
    )
    card_number = forms.CharField(
        max_length=16,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '16-digit card number',
            'maxlength': '16',
        }),
    )
    expiry = forms.CharField(
        max_length=5,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'MM/YY',
            'maxlength': '5',
        }),
    )
    cvv = forms.CharField(
        max_length=3,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'CVV',
            'maxlength': '3',
        }),
    )

    def clean_card_number(self):
        value = self.cleaned_data['card_number'].replace(' ', '')
        if not value.isdigit() or len(value) != 16:
            raise ValidationError('Card number must be exactly 16 digits.')
        return value

    def clean_cvv(self):
        value = self.cleaned_data['cvv']
        if not value.isdigit() or len(value) != 3:
            raise ValidationError('CVV must be exactly 3 digits.')
        return value

    def clean_expiry(self):
        value = self.cleaned_data['expiry']
        if not re.match(r'^\d{2}/\d{2}$', value):
            raise ValidationError('Expiry must be in MM/YY format.')
        month = int(value[:2])
        if month < 1 or month > 12:
            raise ValidationError('Invalid month in expiry date.')
        return value


class OTPForm(forms.Form):
    otp = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg text-center letter-spacing',
            'placeholder': '000000',
            'maxlength': '6',
            'autocomplete': 'one-time-code',
        }),
    )

    def clean_otp(self):
        value = self.cleaned_data['otp']
        if not value.isdigit():
            raise ValidationError('OTP must contain only digits.')
        return value