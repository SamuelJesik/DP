# myapp/views.py
# projekt/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from .models import  RefactoringTask, UploadedFile, CodeRun,TaskRating
from .forms import RefactoringTaskForm,TaskRatingForm
from .forms import UploadCodeForm
from django.contrib.auth.decorators import login_required  
from django.contrib.auth import login
from .forms import RegisterForm
from .forms import UploadCodeForm
from django.contrib import messages
from subprocess import Popen, PIPE
import subprocess
import os
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import logging
from django.views.decorators.http import require_http_methods
import json
import tempfile
import sys
from email import message



 ##############################################################################################

@login_required
def add_task(request):
    if not request.user.is_superuser:
        return render(request, 'unauthorized.html', status=403)
    if request.method == 'POST':
        form = RefactoringTaskForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Úloha bola úspešne pridaná.')
            return redirect('tasks')
    else:
        form = RefactoringTaskForm()
    return render(request, 'add_task.html', {'form': form})

@login_required
def list_tasks(request):
    tasks = RefactoringTask.objects.all()
    return render(request, 'tasks.html', {'tasks': tasks})

@login_required
def task_detail_view(request, user_id, task_id):
    user_id = int(user_id)
    if not request.user.is_superuser and request.user.id != user_id:
        return render(request, 'unauthorized.html', status=403)
    
    task = get_object_or_404(RefactoringTask, id=task_id)
    user = get_object_or_404(User, id=user_id)


    uploaded_files = UploadedFile.objects.filter(user_id=user_id, RefactoringTask_id=task_id).order_by('uploaded_at') 

    coderuns = CodeRun.objects.filter(user_id=user_id, task=task_id).order_by('created_at')
    ratings = TaskRating.objects.filter(user=user, task=task)

    if request.method == 'POST':
        form = TaskRatingForm(request.POST)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.user = user
            rating.task = task
            rating.save()
            messages.success(request, 'Hodnotenie bolo úspešne pridané.')
            return redirect(request.path_info)  
    else:
        form = TaskRatingForm()

    context = {
        'user': user,
        'task': task,
        'uploaded_files': uploaded_files,
        'coderuns': coderuns,
        'ratings': ratings,
        'form': form
    }
    
    return render(request, 'task_detail_admin.html', context)
@login_required
def task_detail(request, task_id):
    task = get_object_or_404(RefactoringTask, id=task_id)
    
    uploaded_files = task.uploaded_files.filter(user=request.user).order_by('uploaded_at') 
    coderuns = CodeRun.objects.filter(task_id=task_id, user_id=request.user).order_by('created_at')
    ratings = TaskRating.objects.filter(task=task, user=request.user).order_by('created_at')

    if request.method == 'POST':
        form = UploadCodeForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = UploadedFile(
                file=request.FILES['file'],
                RefactoringTask=task,
                user=request.user
            )
            uploaded_file.save()
            messages.success(request, 'Súbor bol úspešne nahraný.')

            return redirect('task_detail', task_id=task.id)
    else:
        form = UploadCodeForm()

    context = {
    'task': task,
    'form': form,
    'uploaded_files': uploaded_files,
    'coderuns': coderuns,
    'ratings': ratings,
}

    return render(request, 'task_detail.html', context)

@login_required
def index(request):
    return render(request, 'index.html')


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  
            
            return redirect('index')  
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

@login_required
def rating_view(request):
    if not request.user.is_superuser:
        return render(request, 'unauthorized.html', status=403)
    students = User.objects.filter(is_superuser=False)  
    return render(request, 'rating.html', {'students': students})


logger = logging.getLogger(__name__)


@login_required
def get_tasks_for_student(request, student_id):
    if not request.user.is_superuser:
        return render(request, 'unauthorized.html', status=403)


    tasks = RefactoringTask.objects.all().values('id', 'title')
    tasks_data = [{'id': task['id'], 'title': task['title']} for task in tasks]
    return JsonResponse({'tasks': tasks_data})

@login_required
@require_http_methods(["POST"])  
def run_code(request, task_id):

    logger.info(f"Received run_code request for task_id: {task_id} with body: {request.body}")

    try:

        data = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError as e:

        logger.error(f"JSON decode error: {e}")
        return JsonResponse({"error": "Invalid JSON data."}, status=400)

    code = data.get('code')
    if not code:
        error_msg = "No code provided in the POST request."
        logger.error(error_msg)
        return JsonResponse({"error": error_msg}, status=400)


    #tests

   # Path k adresáru s testami
    host_tests_dir = 'C:/Users/samxk/PycharmProjects/DP/test_directory'
    
    # Získanie dočasného adresára pre systém
    temp_dir = tempfile.gettempdir() 
    # Názov dočasného súboru pre kód užívateľa
    temp_code_file_name = f'temp_code_{task_id}.py' 
    # Cesta k dočasnému súboru v adresári s testami
    temp_code_file_path = os.path.join(host_tests_dir, temp_code_file_name) 
    
    # Execute the code
    try:
        
        # Uložíme kód do dočasného súboru
        with open(temp_code_file_path, 'w') as temp_file:
            temp_file.write(code)
        logger.info(f"Temporary code file created at {temp_code_file_path}.")


        # Vytvoríme Docker kontajner a spustíme skript
        docker_command = [
            'docker', 'run',
            '-v', f"{host_tests_dir}:/usr/src/app",  # adresár /tmp k pracovnému adresáru kontajnera
            'python-runner', 
            'python', f'/usr/src/app/{temp_code_file_name}'
        ]
        result = subprocess.run(
            docker_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30
        )
        temp_code_file_name = f'temp_code_{task_id}.py'
        test_pattern = f'tests_task_{task_id}*.py'  # Pattern pre hľadanie testov relevantných k task_id

         # Po vykonaní kódu spustíme unit testy
        docker_command_test = [
            'docker', 'run',
            '-v', f"{host_tests_dir}:/tests",
            'python-runner', 
            'python', '-m', 'unittest', 'discover', '/tests', test_pattern
        ]
        

        test_result = subprocess.run(
            docker_command_test,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=60  # Dlhší časový limit pre testy
        )

        code_run_instance = CodeRun(
            user=request.user,
            task=RefactoringTask.objects.get(id=task_id),
            code=code,
            output=result.stdout if result.stdout else result.stderr,
            tests_output=test_result.stdout if test_result.stdout else test_result.stderr
        )
        code_run_instance.save()


        # Zaznamenáme výsledky testov
        logger.info(f"Tests executed with stdout: {test_result.stdout}")
        if test_result.stderr:
            logger.error(f"Tests executed with stderr: {test_result.stderr}")

        # Odstránenie dočasného súboru
        os.remove(temp_code_file_path)
        logger.info(f"Temporary code file {temp_code_file_name} removed.")

        logger.info(f"Code executed with stdout: {result.stdout}")
        if result.stderr:
            logger.error(f"Code executed with stderr: {result.stderr}")
        output = result.stdout
        errors = result.stderr

        if output:
            print(output)  # Toto sa zaloguje do Docker logov
        if errors:
            print(errors, file=sys.stderr)  # Chyby sa zalogujú ako štandardný chybový výstup

        # Return the response
        return JsonResponse({
            "code_stdout": result.stdout,
            "code_stderr": result.stderr,
            "code_returncode": result.returncode,
            "test_stdout": test_result.stdout,
            "test_stderr": test_result.stderr,
            "test_returncode": test_result.returncode
        })

    except subprocess.TimeoutExpired as e:
        logger.error(f"Code execution exceeded time limit: {e}")
        return JsonResponse({"error": "Execution time exceeded limit."}, status=408)

    except Exception as e:
        logger.exception("An error occurred during code execution.")
        return JsonResponse({"error": str(e)}, status=500)
    

    