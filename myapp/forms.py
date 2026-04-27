from django import forms
from .models import RefactoringTask, UploadedFile, TaskRating
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class RefactoringTaskForm(forms.ModelForm):
    class Meta:
        model = RefactoringTask
        fields = ['language', 'task_type', 'title', 'description', 'input_code', 'expected_output', 'solution_code', 'show_tests', 'code_file']

        widgets = {
            'input_code': forms.Textarea(attrs={'class': 'ace-editor-input', 'rows': 15}),
            'expected_output': forms.Textarea(attrs={'rows': 10}),
            'solution_code': forms.Textarea(attrs={'rows': 10}),
        }

        help_texts = {
            'solution_code': 'Required for Test Writing tasks only. This is the correct version of the buggy code — used to verify student tests pass on a working implementation.',
            'expected_output': 'Unit tests run against the student\'s code. Not used for Test Writing tasks.',
        }

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