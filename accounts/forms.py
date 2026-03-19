from django import forms
from django.contrib.auth.models import User
from .models import Address


class RegistrationForm(forms.Form):
    username = forms.CharField(max_length=150, label='Username', widget=forms.TextInput(attrs={'placeholder': 'Username', 'class':'form-control'}))
    email = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'placeholder':'Email','class':'form-control'}))
    password = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'placeholder':'Password','class':'form-control'}))
    confirm = forms.CharField(label='Confirm Password', widget=forms.PasswordInput(attrs={'placeholder':'Confirm Password','class':'form-control'}))

    # Address fields
    full_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'placeholder':'Full name','class':'form-control'}))
    phone = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'placeholder':'Phone number','class':'form-control'}))
    address_line1 = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'placeholder':'Address line 1','class':'form-control'}))
    address_line2 = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'placeholder':'Address line 2 (optional)','class':'form-control'}))
    city = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder':'City','class':'form-control'}))
    state = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder':'State','class':'form-control'}))
    pincode = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'placeholder':'Pincode','class':'form-control'}))
    country = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder':'Country','class':'form-control'}))

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Username already taken')
        return username

    def clean(self):
        cleaned = super().clean()
        pwd = cleaned.get('password')
        confirm = cleaned.get('confirm')
        if pwd and confirm and pwd != confirm:
            raise forms.ValidationError('Passwords do not match')
        return cleaned


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['full_name','email','phone','address_line1','address_line2','city','state','pincode','country']
        widgets = {
            'full_name': forms.TextInput(attrs={'class':'form-control'}),
            'email': forms.EmailInput(attrs={'class':'form-control'}),
            'phone': forms.TextInput(attrs={'class':'form-control'}),
            'address_line1': forms.TextInput(attrs={'class':'form-control'}),
            'address_line2': forms.TextInput(attrs={'class':'form-control'}),
            'city': forms.TextInput(attrs={'class':'form-control'}),
            'state': forms.TextInput(attrs={'class':'form-control'}),
            'pincode': forms.TextInput(attrs={'class':'form-control'}),
            'country': forms.TextInput(attrs={'class':'form-control'}),
        }