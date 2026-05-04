import re

from django import forms
from django.contrib.auth.models import User

from .models import Address


NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z\s.'-]{1,149}$")
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.]{3,150}$")
PHONE_PATTERN = re.compile(r"^\d{10}$")
PINCODE_PATTERN = re.compile(r"^\d{6}$")
ADDRESS_PATTERN = re.compile(r"^[A-Za-z0-9\s,./#'()&-]{5,255}$")
PLACE_PATTERN = re.compile(r"^[A-Za-z][A-Za-z\s.'-]{1,99}$")
GMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@gmail\.com$")


def _validate_optional_name(value, field_label):
    value = (value or "").strip()
    if value and not NAME_PATTERN.fullmatch(value):
        raise forms.ValidationError(f"{field_label} should contain only letters and common name characters.")
    return value


def _validate_required_name(value, field_label):
    value = (value or "").strip()
    if not value:
        raise forms.ValidationError(f"{field_label} is required.")
    if not NAME_PATTERN.fullmatch(value):
        raise forms.ValidationError(f"{field_label} should contain only letters and common name characters.")
    return value


def _validate_gmail(value):
    value = (value or "").strip().lower()
    if not value:
        raise forms.ValidationError("Email is required.")
    if not GMAIL_PATTERN.fullmatch(value):
        raise forms.ValidationError("Please enter a valid Gmail address ending with @gmail.com.")
    return value


def _validate_phone(value):
    value = re.sub(r"\D", "", (value or "").strip())
    if not PHONE_PATTERN.fullmatch(value):
        raise forms.ValidationError("Mobile number must be exactly 10 digits.")
    return value


def _validate_pincode(value):
    value = (value or "").strip()
    if not PINCODE_PATTERN.fullmatch(value):
        raise forms.ValidationError("Pincode must be exactly 6 digits.")
    return value


def _validate_address_line(value, field_label, required=True):
    value = (value or "").strip()
    if not value:
        if required:
            raise forms.ValidationError(f"{field_label} is required.")
        return value
    if not ADDRESS_PATTERN.fullmatch(value):
        raise forms.ValidationError(f"{field_label} contains invalid characters or is too short.")
    return value


def _validate_place(value, field_label):
    value = (value or "").strip()
    if not value:
        raise forms.ValidationError(f"{field_label} is required.")
    if not PLACE_PATTERN.fullmatch(value):
        raise forms.ValidationError(f"{field_label} should contain only letters and common place characters.")
    return value


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name', 'maxlength': '150', 'autocomplete': 'given-name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name', 'maxlength': '150', 'autocomplete': 'family-name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email', 'inputmode': 'email', 'autocomplete': 'email', 'pattern': '[A-Za-z0-9._%+-]+@gmail\\.com', 'title': 'Enter a valid Gmail address ending with @gmail.com'}),
        }

    def clean_first_name(self):
        return _validate_optional_name(self.cleaned_data.get('first_name'), 'First name')

    def clean_last_name(self):
        return _validate_optional_name(self.cleaned_data.get('last_name'), 'Last name')

    def clean_email(self):
        return _validate_gmail(self.cleaned_data.get('email'))


class RegistrationForm(forms.Form):
    username = forms.CharField(max_length=150, label='Username', widget=forms.TextInput(attrs={'placeholder': 'Username', 'class': 'form-control', 'minlength': '3', 'maxlength': '150', 'autocomplete': 'username', 'pattern': '[A-Za-z0-9_.]{3,150}', 'title': 'Use 3 or more letters, numbers, underscore, or dot only'}))
    email = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'placeholder': 'Email', 'class': 'form-control', 'inputmode': 'email', 'autocomplete': 'email', 'pattern': '[A-Za-z0-9._%+-]+@gmail\\.com', 'title': 'Enter a valid Gmail address ending with @gmail.com'}))
    password = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'class': 'form-control', 'minlength': '8', 'autocomplete': 'new-password'}))
    confirm = forms.CharField(label='Confirm Password', widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password', 'class': 'form-control', 'minlength': '8', 'autocomplete': 'new-password'}))

    # Address fields
    full_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'placeholder': 'Full name', 'class': 'form-control', 'maxlength': '150', 'autocomplete': 'name'}))
    phone = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'placeholder': 'Phone number', 'class': 'form-control', 'inputmode': 'numeric', 'maxlength': '10', 'minlength': '10', 'pattern': '\\d{10}', 'title': 'Enter exactly 10 digits', 'autocomplete': 'tel'}))
    address_line1 = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'placeholder': 'Address line 1', 'class': 'form-control', 'maxlength': '255', 'autocomplete': 'address-line1'}))
    address_line2 = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'placeholder': 'Address line 2 (optional)', 'class': 'form-control', 'maxlength': '255', 'autocomplete': 'address-line2'}))
    city = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'City', 'class': 'form-control', 'maxlength': '100', 'autocomplete': 'address-level2'}))
    state = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'State', 'class': 'form-control', 'maxlength': '100', 'autocomplete': 'address-level1'}))
    pincode = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'placeholder': 'Pincode', 'class': 'form-control', 'inputmode': 'numeric', 'maxlength': '6', 'minlength': '6', 'pattern': '\\d{6}', 'title': 'Enter exactly 6 digits', 'autocomplete': 'postal-code'}))
    country = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Country', 'class': 'form-control', 'maxlength': '100', 'autocomplete': 'country-name'}))

    def clean_username(self):
        username = (self.cleaned_data['username'] or '').strip()
        if not USERNAME_PATTERN.fullmatch(username):
            raise forms.ValidationError('Username must be 3 or more characters and can only use letters, numbers, underscore, or dot.')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Username already taken')
        return username

    def clean_email(self):
        return _validate_gmail(self.cleaned_data.get('email'))

    def clean_full_name(self):
        return _validate_required_name(self.cleaned_data.get('full_name'), 'Full name')

    def clean_phone(self):
        return _validate_phone(self.cleaned_data.get('phone'))

    def clean_address_line1(self):
        return _validate_address_line(self.cleaned_data.get('address_line1'), 'Address line 1')

    def clean_address_line2(self):
        return _validate_address_line(self.cleaned_data.get('address_line2'), 'Address line 2', required=False)

    def clean_city(self):
        return _validate_place(self.cleaned_data.get('city'), 'City')

    def clean_state(self):
        return _validate_place(self.cleaned_data.get('state'), 'State')

    def clean_pincode(self):
        return _validate_pincode(self.cleaned_data.get('pincode'))

    def clean_country(self):
        return _validate_place(self.cleaned_data.get('country'), 'Country')

    def clean(self):
        cleaned = super().clean()
        pwd = cleaned.get('password')
        confirm = cleaned.get('confirm')
        if pwd and confirm and pwd != confirm:
            raise forms.ValidationError('Passwords do not match')
        if pwd and len(pwd) < 8:
            self.add_error('password', 'Password must be at least 8 characters long.')
        if pwd and not re.search(r'[A-Za-z]', pwd):
            self.add_error('password', 'Password must contain at least one letter.')
        if pwd and not re.search(r'\d', pwd):
            self.add_error('password', 'Password must contain at least one number.')
        return cleaned


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['full_name', 'email', 'phone', 'address_line1', 'address_line2', 'city', 'state', 'pincode', 'country', 'is_default']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '150', 'autocomplete': 'name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'inputmode': 'email', 'autocomplete': 'email', 'pattern': '[A-Za-z0-9._%+-]+@gmail\\.com', 'title': 'Enter a valid Gmail address ending with @gmail.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'inputmode': 'numeric', 'maxlength': '10', 'minlength': '10', 'pattern': '\\d{10}', 'title': 'Enter exactly 10 digits', 'autocomplete': 'tel'}),
            'address_line1': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '255', 'autocomplete': 'address-line1'}),
            'address_line2': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '255', 'autocomplete': 'address-line2'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '100', 'autocomplete': 'address-level2'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '100', 'autocomplete': 'address-level1'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control', 'inputmode': 'numeric', 'maxlength': '6', 'minlength': '6', 'pattern': '\\d{6}', 'title': 'Enter exactly 6 digits', 'autocomplete': 'postal-code'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '100', 'autocomplete': 'country-name'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_full_name(self):
        return _validate_required_name(self.cleaned_data.get('full_name'), 'Full name')

    def clean_email(self):
        return _validate_gmail(self.cleaned_data.get('email'))

    def clean_phone(self):
        return _validate_phone(self.cleaned_data.get('phone'))

    def clean_address_line1(self):
        return _validate_address_line(self.cleaned_data.get('address_line1'), 'Address line 1')

    def clean_address_line2(self):
        return _validate_address_line(self.cleaned_data.get('address_line2'), 'Address line 2', required=False)

    def clean_city(self):
        return _validate_place(self.cleaned_data.get('city'), 'City')

    def clean_state(self):
        return _validate_place(self.cleaned_data.get('state'), 'State')

    def clean_pincode(self):
        return _validate_pincode(self.cleaned_data.get('pincode'))

    def clean_country(self):
        return _validate_place(self.cleaned_data.get('country'), 'Country')
