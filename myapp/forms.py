from django import forms
from .models import RefactoringTask, UploadedFile, TaskRating
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class RefactoringTaskForm(forms.ModelForm):
    class Meta:
        model = RefactoringTask
        fields = ['title', 'description', 'input_code', 'expected_output', 'code_file']

class UploadCodeForm(forms.ModelForm):
    class Meta:
        model = UploadedFile
        fields = ['file']
        labels = {
            'file': 'Upload File',
        }
        help_texts = {
            'file': 'Select a .py file to upload.',
        }
        widgets = {
            'file': forms.FileInput(attrs={'accept': '.py'}),
        }

class RegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

class TaskRatingForm(forms.ModelForm):
    class Meta:
        model = TaskRating
        fields = ['rating', 'feedback']
