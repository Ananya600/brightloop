import re
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from catalog.models import Customer

User = get_user_model()


def validate_strong_password(pw):
    if len(pw) <= 8:
        raise ValidationError('Password must be more than 8 characters.')
    if not re.search(r'[A-Z]', pw):
        raise ValidationError('Password needs an uppercase letter.')
    if not re.search(r'[a-z]', pw):
        raise ValidationError('Password needs a lowercase letter.')
    if not re.search(r'[^A-Za-z0-9]', pw):
        raise ValidationError('Password needs a special character.')


class SignupForm(forms.ModelForm):
    name = forms.CharField(max_length=150)
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['email']

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('An account with this email already exists.')
        return email

    def clean(self):
        data = super().clean()
        p1, p2 = data.get('password1'), data.get('password2')
        if p1:
            validate_strong_password(p1)
        if p1 and p2 and p1 != p2:
            self.add_error('password2', 'Passwords do not match.')
        return data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email
        user.role = 'customer'
        user.set_password(self.cleaned_data['password1'])
        user.save()
        Customer.objects.create(user=user, name=self.cleaned_data['name'], email=user.email)
        return user