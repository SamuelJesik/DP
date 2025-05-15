# myapp/urls.py

from django.urls import path
from . import views
from .views import add_task, list_tasks,task_detail, index, register,run_code,get_tasks_for_student
from django.contrib.auth.views import LoginView, LogoutView


urlpatterns = [
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('', views.index, name='index'),
    path('tasks/add/', add_task, name='add_task'),
    path('tasks/', list_tasks, name='tasks'),
    path('tasks/<int:task_id>/', views.task_detail, name='task_detail'),
    path('register/', register, name='register'),
    path('run-code/<int:task_id>/', run_code, name='run_code'),
    path('hodnotenie/', views.rating_view, name='rating_view'),
    path('get-tasks-for-student/<int:student_id>/', views.get_tasks_for_student, name='get_tasks_for_student'),
    path('students/<int:user_id>/tasks/<int:task_id>/', views.task_detail_view, name='task_detail_admin'),







]