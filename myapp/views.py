import json
import logging
import os
import re
import subprocess
import sys
import tempfile

import requests

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .forms import RefactoringTaskForm, RegisterForm, TaskRatingForm, UploadCodeForm
from .models import CodeRun, RefactoringTask, TaskRating, UploadedFile


def _write_test_file(task, input_code, expected_output_content, language):
    """Write the test file to test_directory after saving a task."""
    test_dir = os.path.join(settings.BASE_DIR, 'test_directory')
    os.makedirs(test_dir, exist_ok=True)

    if language == 'python':
        filename = f"tests_task_{task.id}.py"
        if "import unittest" not in expected_output_content:
            expected_output_content = "import unittest\n" + expected_output_content
        match = re.search(r"(?:def|class)\s+([a-zA-Z_][a-zA-Z0-9_]*)", input_code or '')
        if match:
            target_name = match.group(1)
            import_line = f"from temp_code_{task.id} import {target_name}"
            if "from temp_code" not in expected_output_content:
                expected_output_content = expected_output_content.replace(
                    "import unittest", f"import unittest\n{import_line}"
                )
        if "unittest.main()" not in expected_output_content:
            expected_output_content += "\n\nif __name__ == '__main__':\n    unittest.main()"

    elif language == 'cpp':
        filename = f"tests_task_{task.id}.cpp"
        if f'temp_code_{task.id}.cpp' not in expected_output_content:
            expected_output_content = f'#include "temp_code_{task.id}.cpp"\n' + expected_output_content
        if "#include <cassert>" not in expected_output_content:
            expected_output_content = "#include <cassert>\n" + expected_output_content

    elif language == 'java':
        filename = f"TestMain_{task.id}.java"
        expected_output_content = expected_output_content.replace(
            "public class TestMain", f"public class TestMain_{task.id}"
        )
    else:
        return

    with open(os.path.join(test_dir, filename), 'w', encoding='utf-8') as f:
        f.write(expected_output_content)


@login_required
def add_task(request):
    if not request.user.is_superuser:
        return render(request, 'unauthorized.html', status=403)

    if request.method == 'POST':
        form = RefactoringTaskForm(request.POST, request.FILES)
        if form.is_valid():
            task = form.save()
            if form.cleaned_data.get('expected_output'):
                try:
                    _write_test_file(
                        task,
                        form.cleaned_data.get('input_code'),
                        form.cleaned_data.get('expected_output'),
                        form.cleaned_data.get('language'),
                    )
                    messages.success(request, f'Úloha uložená. Testy pre {task.language} vytvorené.')
                except Exception as e:
                    messages.error(request, f'Chyba pri generovaní testov: {e}')
            return redirect('tasks')
    else:
        form = RefactoringTaskForm()
    return render(request, 'add_task.html', {'form': form})


@login_required
def edit_task(request, task_id):
    if not request.user.is_superuser:
        return render(request, 'unauthorized.html', status=403)

    task = get_object_or_404(RefactoringTask, id=task_id)

    if request.method == 'POST':
        form = RefactoringTaskForm(request.POST, request.FILES, instance=task)
        if form.is_valid():
            task = form.save()
            if form.cleaned_data.get('expected_output'):
                try:
                    _write_test_file(
                        task,
                        form.cleaned_data.get('input_code'),
                        form.cleaned_data.get('expected_output'),
                        form.cleaned_data.get('language'),
                    )
                    messages.success(request, 'Úloha aktualizovaná. Testy prepísané.')
                except Exception as e:
                    messages.error(request, f'Chyba pri generovaní testov: {e}')
            else:
                messages.success(request, 'Úloha aktualizovaná.')
            return redirect('task_detail', task_id=task.id)
    else:
        form = RefactoringTaskForm(instance=task)
    return render(request, 'add_task.html', {'form': form, 'editing': True, 'task': task})

@login_required
def list_tasks(request):
    sort_by = request.GET.get('sort', '-id')
    valid_sorts = ['title', 'language', '-id', 'id', 'task_type']
    if sort_by not in valid_sorts:
        sort_by = '-id'

    tasks = RefactoringTask.objects.all().order_by(sort_by)

    submitted_task_ids = set(
        CodeRun.objects.filter(user=request.user).values_list('task_id', flat=True)
    )

    return render(request, 'tasks.html', {
        'tasks': tasks,
        'current_sort': sort_by,
        'submitted_task_ids': submitted_task_ids,
    })

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
    from django.db.models import Avg, Count
    total_tasks = RefactoringTask.objects.count()
    submitted_count = CodeRun.objects.filter(user=request.user).values('task').distinct().count()
    type_counts = {t: RefactoringTask.objects.filter(task_type=t).count()
                   for t in ['refactoring', 'error_detection', 'test_writing', 'code_extension']}

    rating_stats = TaskRating.objects.filter(user=request.user).aggregate(
        avg=Avg('rating'),
        count=Count('id'),
        task_count=Count('task', distinct=True),
    )
    avg_rating = round(rating_stats['avg'], 1) if rating_stats['avg'] else None
    rated_task_count = rating_stats['task_count'] or 0

    return render(request, 'index.html', {
        'total_tasks': total_tasks,
        'submitted_count': submitted_count,
        'type_counts': type_counts,
        'avg_rating': avg_rating,
        'rated_task_count': rated_task_count,
    })


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
    from django.db.models import Count, Max
    students = (
        User.objects
        .filter(is_superuser=False)
        .annotate(
            submission_count=Count('coderun', distinct=True),
            last_submission=Max('coderun__created_at'),
            rated_count=Count('task_ratings__task', distinct=True),
        )
        .order_by('username')
    )
    total_tasks = RefactoringTask.objects.count()
    return render(request, 'rating.html', {'students': students, 'total_tasks': total_tasks})


@login_required
def student_panel_api(request, user_id, task_id):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Forbidden'}, status=403)

    student = get_object_or_404(User, id=user_id)
    task = get_object_or_404(RefactoringTask, id=task_id)

    if request.method == 'POST':
        data = json.loads(request.body)
        rating_val = int(data.get('rating', 1))
        feedback = data.get('feedback', '').strip()
        TaskRating.objects.create(user=student, task=task, rating=rating_val, feedback=feedback)
        return JsonResponse({'ok': True})

    coderuns = list(
        CodeRun.objects.filter(user=student, task=task)
        .order_by('-created_at')
        .values('code', 'output', 'tests_output', 'created_at')[:5]
    )
    for r in coderuns:
        r['created_at'] = r['created_at'].strftime('%d %b %Y %H:%M')

    uploaded_files = list(
        UploadedFile.objects.filter(user=student, RefactoringTask=task)
        .order_by('-uploaded_at')
        .values('file', 'uploaded_at')
    )
    for f in uploaded_files:
        f['uploaded_at'] = f['uploaded_at'].strftime('%d %b %Y %H:%M')
        f['name'] = f['file'].split('/')[-1]

    ratings = list(
        TaskRating.objects.filter(user=student, task=task)
        .order_by('-created_at')
        .values('rating', 'feedback', 'created_at')
    )
    for r in ratings:
        r['created_at'] = r['created_at'].strftime('%d %b %Y %H:%M')

    return JsonResponse({
        'student': {'id': student.id, 'username': student.username, 'email': student.email},
        'task': {'id': task.id, 'title': task.title, 'task_type': task.task_type},
        'coderuns': coderuns,
        'uploaded_files': uploaded_files,
        'ratings': ratings,
    })


logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["POST"])
def toggle_show_tests(request, task_id):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized.'}, status=403)
    task = get_object_or_404(RefactoringTask, id=task_id)
    task.show_tests = not task.show_tests
    task.save()
    return JsonResponse({'show_tests': task.show_tests})


@login_required
def get_tasks_for_student(request, student_id):
    if not request.user.is_superuser:
        return render(request, 'unauthorized.html', status=403)

    from django.db.models import Max
    tasks = list(RefactoringTask.objects.all().values('id', 'title', 'language', 'task_type'))

    latest_run_ids = (
        CodeRun.objects
        .filter(user_id=student_id)
        .values('task_id')
        .annotate(latest_id=Max('id'))
    )
    latest_map = {r['task_id']: r['latest_id'] for r in latest_run_ids}

    run_details = {}
    if latest_map:
        for run in CodeRun.objects.filter(id__in=latest_map.values()).values('id', 'task_id', 'tests_output'):
            run_details[run['task_id']] = run

    rated_task_ids = set(
        TaskRating.objects.filter(user_id=student_id).values_list('task_id', flat=True)
    )

    tasks_data = []
    for task in tasks:
        tid = task['id']
        has_sub = tid in latest_map
        test_status = None
        if has_sub and tid in run_details:
            to = run_details[tid].get('tests_output') or ''
            if to:
                if re.search(r'passed|ok', to, re.IGNORECASE) and not re.search(r'failed|error', to, re.IGNORECASE):
                    test_status = 'pass'
                else:
                    test_status = 'fail'
        tasks_data.append({
            'id': tid,
            'title': task['title'],
            'language': task['language'],
            'task_type': task['task_type'],
            'has_submission': has_sub,
            'test_status': test_status,
            'is_rated': tid in rated_task_ids,
        })

    return JsonResponse({'tasks': tasks_data})

def _docker_run(host_tests_dir, run_command, timeout=30):
    """Run a command in the python-runner Docker container with host_tests_dir mounted."""
    cmd = [
        'docker', 'run', '--rm',
        '-v', f"{host_tests_dir}:/usr/src/app",
        '-v', f"{host_tests_dir}:/tests",
        'python-runner',
    ] + run_command
    return subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding='utf-8', errors='replace', timeout=timeout,
    )


@login_required
@require_http_methods(["POST"])
def run_code(request, task_id):
    logger.info(f"Received run_code request for task_id: {task_id}")

    try:
        data = json.loads(request.body.decode('utf-8'))
        code = data.get('code', '')

        task = get_object_or_404(RefactoringTask, id=task_id)
        language = task.language

        host_tests_dir = os.path.join(settings.BASE_DIR, 'test_directory')
        os.makedirs(host_tests_dir, exist_ok=True)

        if task.task_type == 'test_writing':
            if language == 'python':
                return _run_test_writing(request, task, task_id, code, host_tests_dir)
            elif language == 'cpp':
                return _run_test_writing_cpp(request, task, task_id, code, host_tests_dir)
            elif language == 'java':
                return _run_test_writing_java(request, task, task_id, code, host_tests_dir)

        if language == 'python':
            filename = f"temp_code_{task_id}.py"
            run_command = ['python', f'/usr/src/app/{filename}']
        elif language == 'cpp':
            filename = f"temp_code_{task_id}.cpp"
            run_command = ['bash', '-c', f"g++ /usr/src/app/{filename} -o /usr/src/app/app_{task_id} && /usr/src/app/app_{task_id}"]
        elif language == 'java':
            match = re.search(r'public\s+class\s+(\w+)', code)
            class_name = match.group(1) if match else "Main"
            filename = f"{class_name}.java"
            run_command = ['bash', '-c', f"javac /usr/src/app/{filename} && java -cp /usr/src/app {class_name}"]

        with open(os.path.join(host_tests_dir, filename), 'w', encoding='utf-8') as f:
            f.write(code)

        result = _docker_run(host_tests_dir, run_command)
        full_output = (result.stdout or "") + (result.stderr or "")

        test_stdout = ""
        test_stderr = ""

        if language == 'python':
            try:
                test_result = _docker_run(host_tests_dir, [
                    'python', '-m', 'unittest', 'discover', '/tests', f'tests_task_{task_id}*.py'
                ])
                test_stdout = test_result.stdout or ""
                test_stderr = test_result.stderr or ""
            except subprocess.TimeoutExpired:
                test_stderr = "Tests timed out."

        elif language == 'cpp':
            test_file = f"tests_task_{task_id}.cpp"
            if os.path.exists(os.path.join(host_tests_dir, test_file)):
                try:
                    test_result = _docker_run(host_tests_dir, ['bash', '-c',
                        f"g++ -DRUNNING_TESTS /tests/{test_file} -o /tests/test_app_{task_id} && /tests/test_app_{task_id}"
                    ])
                    if test_result.returncode == 0:
                        test_stdout = "✅ All tests passed.\n" + (test_result.stdout or "")
                    else:
                        test_stdout = "❌ Tests failed.\n" + (test_result.stdout or "") + (test_result.stderr or "")
                except subprocess.TimeoutExpired:
                    test_stderr = "Tests timed out."
            else:
                test_stdout = "No test file found."

        elif language == 'java':
            match = re.search(r'public\s+class\s+(\w+)', code)
            student_class_name = match.group(1) if match else "Main"
            test_class_name = f"TestMain_{task_id}"
            test_filename = f"{test_class_name}.java"
            if os.path.exists(os.path.join(host_tests_dir, test_filename)):
                try:
                    test_result = _docker_run(host_tests_dir, ['bash', '-c',
                        f"javac /usr/src/app/{student_class_name}.java /usr/src/app/{test_filename} && "
                        f"java -cp /usr/src/app {test_class_name}"
                    ], timeout=45)
                    if test_result.returncode == 0:
                        test_stdout = "✅ All tests passed.\n" + (test_result.stdout or "")
                    else:
                        test_stdout = "❌ Tests failed.\n" + (test_result.stdout or "") + (test_result.stderr or "")
                except subprocess.TimeoutExpired:
                    test_stderr = "Tests timed out (Java)."
            else:
                test_stdout = "No test file found."

        CodeRun.objects.create(
            user=request.user, task=task, code=code,
            output=full_output, tests_output=test_stdout + test_stderr,
        )

        return JsonResponse({
            "code_stdout": result.stdout or "",
            "code_stderr": result.stderr or "",
            "code_returncode": result.returncode,
            "test_stdout": test_stdout,
            "test_stderr": test_stderr,
        })

    except Exception as e:
        logger.exception("Error running code")
        return JsonResponse({"error": str(e)}, status=500)


def _run_test_writing(request, task, task_id, student_test_code, host_tests_dir):
    """
    For test_writing tasks: run the student's tests against the buggy code
    (expect FAIL) and against the solution code (expect PASS).
    """
    if not task.solution_code:
        return JsonResponse({"error": "This task has no solution code configured."}, status=500)

    # Inject import if student forgot it
    import_line = f"from temp_code_{task_id} import *"
    if f"temp_code_{task_id}" not in student_test_code:
        if "import unittest" in student_test_code:
            student_test_code = student_test_code.replace(
                "import unittest", f"import unittest\n{import_line}"
            )
        else:
            student_test_code = f"import unittest\n{import_line}\n" + student_test_code
    if "unittest.main()" not in student_test_code:
        student_test_code += "\n\nif __name__ == '__main__':\n    unittest.main()"

    student_test_file = f"student_tests_{task_id}.py"
    temp_code_file = f"temp_code_{task_id}.py"
    student_test_path = os.path.join(host_tests_dir, student_test_file)
    temp_code_path = os.path.join(host_tests_dir, temp_code_file)

    with open(student_test_path, 'w', encoding='utf-8') as f:
        f.write(student_test_code)

    run_cmd = ['bash', '-c', f'cd /usr/src/app && python -m unittest {student_test_file[:-3]} 2>&1']

    # Run 1: against buggy code (should FAIL)
    with open(temp_code_path, 'w', encoding='utf-8') as f:
        f.write(task.input_code)
    try:
        buggy_result = _docker_run(host_tests_dir, run_cmd)
        buggy_output = (buggy_result.stdout or "") + (buggy_result.stderr or "")
        buggy_passed = buggy_result.returncode == 0
    except subprocess.TimeoutExpired:
        buggy_output = "Timed out."
        buggy_passed = False

    # Run 2: against solution code (should PASS)
    with open(temp_code_path, 'w', encoding='utf-8') as f:
        f.write(task.solution_code)
    try:
        solution_result = _docker_run(host_tests_dir, run_cmd)
        solution_output = (solution_result.stdout or "") + (solution_result.stderr or "")
        solution_passed = solution_result.returncode == 0
    except subprocess.TimeoutExpired:
        solution_output = "Timed out."
        solution_passed = False

    CodeRun.objects.create(
        user=request.user, task=task, code=student_test_code,
        output=f"[Buggy] {buggy_output}",
        tests_output=f"[Solution] {solution_output}",
    )

    return JsonResponse({
        "task_type": "test_writing",
        "buggy_output": buggy_output,
        "buggy_passed": buggy_passed,
        "solution_output": solution_output,
        "solution_passed": solution_passed,
    })

def _run_test_writing_cpp(request, task, task_id, student_test_code, host_tests_dir):
    """
    C++ test_writing: compile student tests against buggy code (expect FAIL)
    then against solution code (expect PASS).
    Student writes a main() with asserts; we auto-inject the #include.
    """
    if not task.solution_code:
        return JsonResponse({"error": "This task has no solution code configured."}, status=500)

    include_line = f'#include "temp_code_{task_id}.cpp"'
    if f"temp_code_{task_id}" not in student_test_code:
        student_test_code = include_line + "\n" + student_test_code

    test_file = f"student_tests_{task_id}.cpp"
    code_file = f"temp_code_{task_id}.cpp"
    test_path = os.path.join(host_tests_dir, test_file)
    code_path = os.path.join(host_tests_dir, code_file)

    with open(test_path, 'w', encoding='utf-8') as f:
        f.write(student_test_code)

    compile_run = (
        f"g++ -DRUNNING_TESTS /tests/{test_file} -o /tests/tw_app_{task_id} "
        f"&& /tests/tw_app_{task_id}"
    )
    run_cmd = ['bash', '-c', compile_run]

    with open(code_path, 'w', encoding='utf-8') as f:
        f.write(task.input_code)
    try:
        buggy_result  = _docker_run(host_tests_dir, run_cmd)
        buggy_output  = (buggy_result.stdout or "") + (buggy_result.stderr or "")
        buggy_passed  = buggy_result.returncode == 0
    except subprocess.TimeoutExpired:
        buggy_output, buggy_passed = "Timed out.", False

    with open(code_path, 'w', encoding='utf-8') as f:
        f.write(task.solution_code)
    try:
        sol_result    = _docker_run(host_tests_dir, run_cmd)
        sol_output    = (sol_result.stdout or "") + (sol_result.stderr or "")
        sol_passed    = sol_result.returncode == 0
    except subprocess.TimeoutExpired:
        sol_output, sol_passed = "Timed out.", False

    CodeRun.objects.create(
        user=request.user, task=task, code=student_test_code,
        output=f"[Buggy] {buggy_output}", tests_output=f"[Solution] {sol_output}",
    )
    return JsonResponse({
        "task_type": "test_writing",
        "buggy_output": buggy_output, "buggy_passed": buggy_passed,
        "solution_output": sol_output, "solution_passed": sol_passed,
    })


def _run_test_writing_java(request, task, task_id, student_test_code, host_tests_dir):
    """
    Java test_writing: compile student TestMain + code class against buggy (expect FAIL)
    then solution (expect PASS).
    Student writes: class TestMain { public static void main(String[] args) { ... } }
    """
    if not task.solution_code:
        return JsonResponse({"error": "This task has no solution code configured."}, status=500)

    match = re.search(r'public\s+class\s+(\w+)', task.input_code)
    class_name = match.group(1) if match else f"TempCode{task_id}"

    # Ensure student uses plain 'class TestMain' (not public) so it can share a file
    student_test_code = re.sub(r'\bpublic\s+class\s+TestMain\b', 'class TestMain', student_test_code)
    if "class TestMain" not in student_test_code:
        student_test_code = "class TestMain {\n" + student_test_code + "\n}"

    test_file = f"student_tests_{task_id}.java"
    code_file = f"{class_name}.java"
    test_path = os.path.join(host_tests_dir, test_file)
    code_path = os.path.join(host_tests_dir, code_file)

    with open(test_path, 'w', encoding='utf-8') as f:
        f.write(student_test_code)

    compile_run = (
        f"javac /usr/src/app/{code_file} /usr/src/app/{test_file} "
        f"&& java -ea -cp /usr/src/app TestMain"
    )
    run_cmd = ['bash', '-c', compile_run]

    with open(code_path, 'w', encoding='utf-8') as f:
        f.write(task.input_code)
    try:
        buggy_result  = _docker_run(host_tests_dir, run_cmd, timeout=45)
        buggy_output  = (buggy_result.stdout or "") + (buggy_result.stderr or "")
        buggy_passed  = buggy_result.returncode == 0
    except subprocess.TimeoutExpired:
        buggy_output, buggy_passed = "Timed out.", False

    with open(code_path, 'w', encoding='utf-8') as f:
        f.write(task.solution_code)
    try:
        sol_result    = _docker_run(host_tests_dir, run_cmd, timeout=45)
        sol_output    = (sol_result.stdout or "") + (sol_result.stderr or "")
        sol_passed    = sol_result.returncode == 0
    except subprocess.TimeoutExpired:
        sol_output, sol_passed = "Timed out.", False

    CodeRun.objects.create(
        user=request.user, task=task, code=student_test_code,
        output=f"[Buggy] {buggy_output}", tests_output=f"[Solution] {sol_output}",
    )
    return JsonResponse({
        "task_type": "test_writing",
        "buggy_output": buggy_output, "buggy_passed": buggy_passed,
        "solution_output": sol_output, "solution_passed": sol_passed,
    })


def query_ollama(prompt, model="llama3"):
    url = "http://localhost:11434/api/generate"
    data = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
    }
    try:
        response = requests.post(url, json=data, timeout=60)
        response.raise_for_status()
        return response.json().get('response', '')
    except requests.exceptions.RequestException as e:
        print(f"Ollama error: {e}")
        return None

@login_required
def generate_task_assignment(request):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized.'}, status=403)

    lang       = request.GET.get('lang', 'python')
    task_type  = request.GET.get('task_type', 'refactoring')
    difficulty = request.GET.get('difficulty', 'medium')
    topic      = request.GET.get('topic', '').strip()

    if lang == 'cpp':
        lang_name = "C++"
        test_instruction = (
            "A file with 'int main()' that includes the solution and uses assert() to verify results. "
            "Wrap the solution's main() in '#ifndef RUNNING_TESTS'."
        )
    elif lang == 'java':
        lang_name = "Java"
        test_instruction = (
            "A class named 'public class TestMain' with a 'public static void main(String[] args)' method "
            "that creates an instance of the tested class, verifies results, and calls System.exit(1) on failure."
        )
    else:
        lang_name = "Python"
        test_instruction = "Python code with 'import unittest' and a class inheriting from unittest.TestCase."

    topic_hint = f" on the topic of '{topic}'" if topic else ""

    code_instruction = f"ONLY valid {lang_name} code. No markdown, no instructions, no explanatory text after the code — pure code only."

    if task_type == 'error_detection':
        system_instruction = f"""You are an expert {lang_name} developer. Generate an error-detection exercise{topic_hint}.

IMPORTANT: Do NOT use JSON. Use exactly this format with separators:

===TITLE===
(ONLY the task title itself, e.g. "Fix the Bug: Factorial". No preamble, no "Here is", no sentence — just the title.)
===DESCRIPTION===
(Tell the student there are 1-2 intentional bugs to find and fix. Describe what the function should do correctly.)
===CODE===
({code_instruction} Include 1-2 subtle but clear bugs and a main block showing example usage.)
===TESTS===
({code_instruction} {test_instruction} Tests must verify the CORRECT behavior after bugs are fixed. Nothing after the last closing brace.)"""
        user_message = f"Generate one {difficulty}-difficulty error detection task{topic_hint} for {lang_name}."

    elif task_type == 'test_writing':
        if lang == 'cpp':
            buggy_instruction = (
                f"{code_instruction} A class or function with 2-3 clear, testable bugs. "
                "Wrap any main() in '#ifndef RUNNING_TESTS ... #endif' so it does not conflict with the test file."
            )
            solution_instruction = (
                f"{code_instruction} The corrected version of the exact same code with all bugs fixed. "
                "Same '#ifndef RUNNING_TESTS' guard around main()."
            )
            tw_test_hint = (
                "Student writes a separate .cpp file with int main() containing assert() calls. "
                "The include for the code file is injected automatically — student does NOT write #include."
            )
        elif lang == 'java':
            buggy_instruction = (
                f"{code_instruction} A class with 2-3 clear, testable bugs. "
                "The class must have exactly one public class. No test code inside it."
            )
            solution_instruction = (
                f"{code_instruction} The corrected version with all bugs fixed. Same class name as the buggy version."
            )
            tw_test_hint = (
                "Student writes 'class TestMain' (NOT public class) with a "
                "'public static void main(String[] args)' that uses assert statements (JVM -ea flag is enabled). "
                "TestMain is compiled together with the code class automatically."
            )
        else:
            buggy_instruction = (
                f"ONLY valid Python code. A class or function with 2-3 clear, testable bugs. "
                "No markdown, no comments explaining the bugs, no instructions."
            )
            solution_instruction = (
                "ONLY valid Python code. The corrected version with all bugs fixed. "
                "No markdown, no instructions, no explanatory text — pure code only."
            )
            tw_test_hint = (
                "Student writes a unittest.TestCase subclass. "
                "The import of the code module is injected automatically."
            )

        system_instruction = f"""You are an expert {lang_name} developer. Generate a test-writing exercise{topic_hint}.

IMPORTANT: Do NOT use JSON. Use exactly this format with separators:

===TITLE===
(ONLY the task title itself, e.g. "Write Tests for: Stack". No preamble, no "Here is", no sentence — just the title.)
===DESCRIPTION===
(Describe the class/function. Tell the student it has 2-3 bugs and they must write tests that FAIL on the buggy version and PASS on the correct one. List the bugs as hints. Also tell the student: {tw_test_hint})
===BUGGY_CODE===
({buggy_instruction})
===SOLUTION===
({solution_instruction})"""
        user_message = f"Generate one {difficulty}-difficulty test-writing exercise{topic_hint} for {lang_name}."

    elif task_type == 'code_extension':
        system_instruction = f"""You are an expert {lang_name} developer. Generate a code extension exercise{topic_hint}.

IMPORTANT: Do NOT use JSON. Use exactly this format with separators:

===TITLE===
(ONLY the task title itself, e.g. "Extend: Add remove() to Stack". No preamble, no "Here is", no sentence — just the title.)
===DESCRIPTION===
(Describe exactly what new feature the student must add. The base code works — they only need to extend it. Include any constraints like raising exceptions.)
===CODE===
({code_instruction} Working base code with the new feature MISSING. Add a clear TODO comment where the feature should go.)
===TESTS===
({code_instruction} {test_instruction} Tests must verify only the NEW feature. Nothing after the last closing brace.)"""
        user_message = f"Generate one {difficulty}-difficulty code extension task{topic_hint} for {lang_name}."

    else:  # refactoring
        system_instruction = f"""You are an expert {lang_name} developer. Generate a refactoring task{topic_hint}.

IMPORTANT: Do NOT use JSON. Use exactly this format with separators:

===TITLE===
(ONLY the task title itself, e.g. "Refactor: Bank Account". No preamble, no "Here is", no sentence — just the title.)
===DESCRIPTION===
(Describe what is wrong with the code structure and what the student should refactor. The code must work correctly — only the structure is bad.)
===CODE===
({code_instruction} Spaghetti code with duplications or poor structure.)
===TESTS===
({code_instruction} {test_instruction} Tests must verify the output is unchanged after refactoring. Nothing after the last closing brace.)"""
        user_message = f"Generate one {difficulty}-difficulty refactoring task{topic_hint} for {lang_name} (spaghetti code)."

    messages_payload = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": user_message},
    ]

    try:
        ai_response_text = query_ollama_chat(messages_payload)
    except Exception as e:
        return JsonResponse({'error': f'Ollama error: {e}'}, status=503)

    if not ai_response_text:
        return JsonResponse({'error': 'Ollama is not responding.'}, status=503)

    try:
        task_data = parse_ai_response_custom(ai_response_text, task_type=task_type)
    except Exception as e:
        return JsonResponse({'error': f'Failed to parse AI response: {e}'}, status=500)

    task_data['task_type'] = task_type
    if task_data.get('input_code'):
        return JsonResponse(task_data)
    else:
        return JsonResponse({'error': 'AI did not return code in the expected format. Try again.'}, status=500)


@login_required
def get_task_hint(request, task_id):
    task = get_object_or_404(RefactoringTask, id=task_id)

    prompt = f"""
    You are a helpful programming teacher. A student is working on a refactoring task.
    Task title: {task.title}
    Problem description: {task.description}
    Code to fix:
    {task.input_code}

    The student is stuck. Write a short, encouraging hint (max 2-3 sentences) pointing out what to focus on (e.g. "Notice that the same code repeats 3 times...").
    Do NOT reveal the full solution. Respond in English.

    Output must be JSON in this format:
    {{ "hint": "Your hint here..." }}
    """

    ai_response = query_ollama(prompt)

    if ai_response:
        try:
            data = json.loads(ai_response)
            return JsonResponse({'hint': data.get('hint', 'AI nenašla konkrétnu radu.')})
        except json.JSONDecodeError:
            return JsonResponse({'hint': ai_response})

    return JsonResponse({'error': 'AI momentálne neodpovedá.'}, status=503)


@login_required
@csrf_exempt
def chat_with_ai(request, task_id):
    if request.method != "POST":
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    try:
        data = json.loads(request.body)
        user_message = data.get('message', '')
        history = data.get('history', [])
        task = get_object_or_404(RefactoringTask, id=task_id)
        student_code = data.get('student_code', '').strip()

        student_code_section = (
            f"\n\nStudent's current attempt:\n{student_code}"
            if student_code
            else "\n\n(The student has not written any code yet.)"
        )
        system_content = f"""You are a strict code mentor. The student is working on a refactoring task titled "{task.title}".

Task description: {task.description}

Original code to refactor:
{task.input_code}
{student_code_section}

INSTRUCTIONS:
- Compare the student's current attempt against the original code and the task description.
- Identify what the student is doing wrong or what they haven't addressed yet.
- Do NOT reveal the solution or rewrite the code for the student.
- Give a short, targeted hint (2-3 sentences) using the Socratic method — point out a specific issue and ask a guiding question.
- If the student has made progress, acknowledge it briefly before pointing to the next issue.
- Respond in English."""

        messages_payload = [{"role": "system", "content": system_content}]
        for msg in history:
            role = "user" if msg['sender'] == 'user' else "assistant"
            messages_payload.append({"role": role, "content": msg['text']})
        messages_payload.append({"role": "user", "content": user_message})

        ai_response_text = query_ollama_chat(messages_payload)

        if ai_response_text:
            return JsonResponse({'response': ai_response_text})
        return JsonResponse({'error': 'AI mentor spí (Ollama neodpovedá).'}, status=503)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def query_ollama_chat(messages, model="llama3"):

    try:
        url = "http://localhost:11434/api/chat"
        data = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.1}
        }
        response = requests.post(url, json=data, timeout=60)
        response.raise_for_status()
        return response.json()['message']['content']
    except Exception as e:
        print(f"Chyba Ollama Chat: {e}")
        return None
    

def clean_ai_code_block(text):
    """
    Odstráni markdown značky ```python a ``` z textu, ak tam sú.
    """
    if not text:
        return ""
    text = text.replace("```python", "").replace("```Python", "")
    text = text.replace("```", "")
    return text.strip()


def extract_json_from_text(text):
    """
    Nájde prvý a posledný znak JSON objektu ({ a }) a vráti to, čo je medzi nimi.
    Ignoruje všetok "kec" okolo toho (Markdown, vysvetľovanie).
    """
    try:
        start_index = text.find('{')
        end_index = text.rfind('}')
        
        if start_index != -1 and end_index != -1 and start_index < end_index:
            json_str = text[start_index:end_index+1]
            return json.loads(json_str)
        else:
            return None
    except json.JSONDecodeError:
        return None
    


def parse_ai_response_custom(text, task_type=''):
    """
    Parses AI response split by custom markers (===TITLE=== etc.).
    Handles both ===CODE=== and ===BUGGY_CODE=== as input_code,
    and ===SOLUTION=== as solution_code.
    """
    data = {}
    markers = {
        "title":         "===TITLE===",
        "description":   "===DESCRIPTION===",
        "input_code":    "===BUGGY_CODE===" if "===BUGGY_CODE===" in text else "===CODE===",
        "expected_output": "===TESTS===",
        "solution_code": "===SOLUTION===",
    }

    all_marker_strings = list(markers.values())

    for key, marker in markers.items():
        if marker not in text:
            continue
        start = text.find(marker) + len(marker)
        content = text[start:]

        next_marker_pos = len(content)
        for m in all_marker_strings:
            pos = content.find(m)
            if pos != -1 and pos < next_marker_pos:
                next_marker_pos = pos

        clean_content = content[:next_marker_pos].strip()
        # Remove ```lang fences (with or without language tag) as whole tokens
        clean_content = re.sub(r'```(?:python|cpp|c\+\+|java)?\s*', '', clean_content)

        data[key] = clean_content.strip()

    # Strip Llama preamble phrases from title (e.g. "Here is a test-writing exercise:")
    if data.get('title'):
        data['title'] = re.sub(
            r'^(here\s+is\s+(a\s+)?|this\s+is\s+(a\s+)?|below\s+is\s+(a\s+)?)',
            '', data['title'], flags=re.IGNORECASE
        ).strip().rstrip(':').strip()

        # If AI dumped a full sentence as title, keep only the first sentence/line
        title = data['title']
        first_line = title.splitlines()[0].strip()
        # Discard if the first line looks like code
        code_line = re.match(r'^(#include|#ifndef|#define|import |public |class |int |void |//)', first_line)
        if not code_line:
            if len(first_line) <= 80:
                data['title'] = first_line
            else:
                m = re.search(r'^(.{10,80}[.!?:])\s', first_line)
                data['title'] = m.group(1).rstrip('.!?:').strip() if m else first_line[:80].strip()
        else:
            data['title'] = ''  # will be replaced by synthetic fallback below

    # Fallback: synthesise a title from task type + description when AI fails
    if not data.get('title'):
        type_labels = {
            'refactoring': 'Refactor',
            'error_detection': 'Fix the Bug',
            'test_writing': 'Write Tests',
            'code_extension': 'Extend',
        }
        prefix = type_labels.get(task_type, 'Task')
        # Pull the first 5 words of the description as a hint
        desc_words = (data.get('description') or '').split()
        hint = ' '.join(desc_words[:5]).rstrip('.,;:') if desc_words else ''
        data['title'] = f"{prefix}: {hint}" if hint else prefix

    return data