from django.db import models
from django.contrib.auth.models import User
from django.conf import settings


from django.utils.deconstruct import deconstructible
import os

@deconstructible
class PathAndRename(object):
    def __init__(self, sub_path):
        self.sub_path = sub_path

    def __call__(self, instance, filename):
        folder_name = str(instance.user.id)
        return os.path.join(self.sub_path, folder_name, filename)

path_and_rename = PathAndRename("uploads")




class RefactoringTask(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    input_code = models.TextField(help_text="Pôvodný kód na refaktorizáciu vložte sem.")
    expected_output = models.TextField(help_text="Unit testy ktoré budú spúštané na kód (testovací súbor treba pridať manuálne.).", null=True, blank=True)
    code_file = models.FileField(upload_to='uploads/', null=True, blank=True)


class CodeRun(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    task = models.ForeignKey(RefactoringTask, on_delete=models.CASCADE)
    code = models.TextField()
    output = models.TextField()
    tests_output = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
class UploadedFile(models.Model):
    file = models.FileField(upload_to=path_and_rename)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    RefactoringTask = models.ForeignKey(RefactoringTask, on_delete=models.CASCADE, related_name='uploaded_files')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_files')



    def __str__(self):
        return self.title
class TaskRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='task_ratings')
    task = models.ForeignKey(RefactoringTask, on_delete=models.CASCADE, related_name='ratings')
    rating = models.IntegerField(default=1, choices=[(i, str(i)) for i in range(1, 11)])  # Hodnotenie od 1 do 10
    feedback = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.task.title} - {self.user.username} - Rating: {self.rating}"