from django.contrib.auth import get_user_model
from django.contrib import admin
from django.forms import CharField
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import Group
from django.contrib.admin.widgets import FilteredSelectMultiple
from django import forms

from users.models import User


class CustomUserCreationForm(UserCreationForm):

    class Meta:
        model = User
        fields = ('email',)


class CustomUserChangeForm(UserChangeForm):

    cooking_philosophy_0 = CharField(label='Cooking Philosophy (1)', required=False)
    cooking_philosophy_1 = CharField(label='Cooking Philosophy (2)', required=False)
    cooking_philosophy_2 = CharField(label='Cooking Philosophy (3)', required=False)

    personal_cooking_mission_0 = CharField(label='Personal Cooking Mission (1)', required=False)
    personal_cooking_mission_1 = CharField(label='Personal Cooking Mission (2)', required=False)
    personal_cooking_mission_2 = CharField(label='Personal Cooking Mission (3)', required=False)

    source_of_inspiration_0 = CharField(label='Source of inspiration (1)', required=False)
    source_of_inspiration_1 = CharField(label='Source of inspiration (2)', required=False)
    source_of_inspiration_2 = CharField(label='Source of inspiration (3)', required=False)

    class Meta:
        model = User
        fields = ['email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['cooking_philosophy_0'].initial = ''
        self.fields['cooking_philosophy_1'].initial = ''
        self.fields['cooking_philosophy_2'].initial = ''

        self.fields['personal_cooking_mission_0'].initial = ''
        self.fields['personal_cooking_mission_1'].initial = ''
        self.fields['personal_cooking_mission_2'].initial = ''

        self.fields['source_of_inspiration_0'].initial = ''
        self.fields['source_of_inspiration_1'].initial = ''
        self.fields['source_of_inspiration_2'].initial = ''

        if self.instance.pk:
            try:
                self.fields['cooking_philosophy_0'].initial = self.instance.cooking_philosophy[0]
            except (TypeError, IndexError):
                pass
            try:
                self.fields['cooking_philosophy_1'].initial = self.instance.cooking_philosophy[1]
            except (TypeError, IndexError):
                pass
            try:
                self.fields['cooking_philosophy_2'].initial = self.instance.cooking_philosophy[2]
            except (TypeError, IndexError):
                pass

            try:
                self.fields['personal_cooking_mission_0'].initial = self.instance.personal_cooking_mission[0]
            except (TypeError, IndexError):
                pass
            try:
                self.fields['personal_cooking_mission_1'].initial = self.instance.personal_cooking_mission[1]
            except (TypeError, IndexError):
                pass
            try:
                self.fields['personal_cooking_mission_2'].initial = self.instance.personal_cooking_mission[2]
            except (TypeError, IndexError):
                pass

            try:
                self.fields['source_of_inspiration_0'].initial = self.instance.source_of_inspiration[0]
            except (TypeError, IndexError):
                pass
            try:
                self.fields['source_of_inspiration_1'].initial = self.instance.source_of_inspiration[1]
            except (TypeError, IndexError):
                pass
            try:
                self.fields['source_of_inspiration_2'].initial = self.instance.source_of_inspiration[2]
            except (TypeError, IndexError):
                pass

    def save_m2m(self):
        super()._save_m2m()

    def save(self, *args, **kwargs):
        instance = super().save()
        instance.cooking_philosophy = [
            self.cleaned_data.get('cooking_philosophy_0', ''),
            self.cleaned_data.get('cooking_philosophy_1', ''),
            self.cleaned_data.get('cooking_philosophy_2', '')
        ]
        instance.personal_cooking_mission = [
            self.cleaned_data.get('personal_cooking_mission_0', ''),
            self.cleaned_data.get('personal_cooking_mission_1', ''),
            self.cleaned_data.get('personal_cooking_mission_2', '')
        ]
        instance.source_of_inspiration = [
            self.cleaned_data.get('source_of_inspiration_0', ''),
            self.cleaned_data.get('source_of_inspiration_1', ''),
            self.cleaned_data.get('source_of_inspiration_2', '')
        ]
        instance.save()
        return instance

class GroupAdminForm(forms.ModelForm):
    class Meta:
        model = Group
        exclude = []

    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=FilteredSelectMultiple('users', False)  # TODO: use another widget as the number of users grows
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['users'].initial = self.instance.user_set.all()

    def save_m2m(self):
        self.instance.user_set.set(self.cleaned_data['users'])

    def save(self, *args, **kwargs):
        instance = super().save()
        self.save_m2m()
        return instance



