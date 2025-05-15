# myapp/admin.py

from django.contrib import admin
from .models import RefactoringTask



@admin.register(RefactoringTask)
class RefactoringTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'input_code', 'expected_output')
