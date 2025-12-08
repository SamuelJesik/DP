# myapp/views.py
# projekt/views.py

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

 ##############################################################################################

@login_required
def add_task(request):
    if not request.user.is_superuser:
        return render(request, 'unauthorized.html', status=403)
    
    if request.method == 'POST':
        form = RefactoringTaskForm(request.POST, request.FILES)
        if form.is_valid():
            task = form.save()
            
            input_code = form.cleaned_data.get('input_code')
            expected_output_content = form.cleaned_data.get('expected_output')
            language = form.cleaned_data.get('language') 
            
            if expected_output_content:
                try:
                    test_dir = os.path.join(settings.BASE_DIR, 'test_directory')
                    if not os.path.exists(test_dir):
                        os.makedirs(test_dir)

                    if language == 'python':
                        filename = f"tests_task_{task.id}.py"
                        if "import unittest" not in expected_output_content:
                            expected_output_content = "import unittest\n" + expected_output_content
                        
                        match = re.search(r"(?:def|class)\s+([a-zA-Z_][a-zA-Z0-9_]*)", input_code)
                        if match:
                            target_name = match.group(1)
                            import_line = f"from temp_code_{task.id} import {target_name}"
                            if "from temp_code" not in expected_output_content:
                                expected_output_content = expected_output_content.replace("import unittest", f"import unittest\n{import_line}")
                        
                        if "unittest.main()" not in expected_output_content:
                            expected_output_content += "\n\nif __name__ == '__main__':\n    unittest.main()"

                    elif language == 'cpp':
                        filename = f"tests_task_{task.id}.cpp"

                        include_line = f'#include "temp_code_{task.id}.cpp"\n'
                        
                        if f'temp_code_{task.id}.cpp' not in expected_output_content:
                            expected_output_content = include_line + expected_output_content
                            
                        if "#include <cassert>" not in expected_output_content:
                            expected_output_content = "#include <cassert>\n" + expected_output_content

                    elif language == 'java':
                        filename = f"TestMain_{task.id}.java"

                        expected_output_content = expected_output_content.replace("public class TestMain", f"public class TestMain_{task.id}")

                    filepath = os.path.join(test_dir, filename)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(expected_output_content)

                    messages.success(request, f'Úloha uložená. Testy pre {language} vytvorené.')
                
                except Exception as e:
                    messages.error(request, f'Chyba pri generovaní testov: {e}')
            
            return redirect('tasks')
    else:
        form = RefactoringTaskForm()
    return render(request, 'add_task.html', {'form': form})

@login_required
def list_tasks(request):
    sort_by = request.GET.get('sort', '-id')
    
    valid_sorts = ['title', 'language', '-id', 'id']
    
    if sort_by not in valid_sorts:
        sort_by = '-id'
    tasks = RefactoringTask.objects.all().order_by(sort_by)
    
    return render(request, 'tasks.html', {'tasks': tasks, 'current_sort': sort_by})

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
    logger.info(f"Received run_code request for task_id: {task_id}")

    try:
        data = json.loads(request.body.decode('utf-8'))
        code = data.get('code')
        if not code:
            return JsonResponse({"error": "No code provided."}, status=400)

        task = get_object_or_404(RefactoringTask, id=task_id)
        language = task.language 
        
        host_tests_dir = os.path.join(settings.BASE_DIR, 'test_directory')
        if not os.path.exists(host_tests_dir):
            os.makedirs(host_tests_dir)

        filename = f"temp_code_{task_id}.py"
        run_command = []
        
        # --- 1. SPÚŠŤANIE KÓDU ---
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

        file_path = os.path.join(host_tests_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as temp_file:
            temp_file.write(code)

        docker_cmd = ['docker', 'run', '--rm', '-v', f"{host_tests_dir}:/usr/src/app", 'python-runner'] + run_command

        result = subprocess.run(
            docker_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            encoding='utf-8', errors='replace', timeout=30
        )
        full_output = (result.stdout or "") + (result.stderr or "")

        # --- 2. SPÚŠŤANIE TESTOV ---
        test_stdout = ""
        test_stderr = ""
        
        if language == 'python':
            test_pattern = f'tests_task_{task_id}*.py'
            docker_test_cmd = [
                'docker', 'run', '--rm', '-v', f"{host_tests_dir}:/tests", '-v', f"{host_tests_dir}:/usr/src/app",
                'python-runner', 'python', '-m', 'unittest', 'discover', '/tests', test_pattern
            ]
            try:
                test_result = subprocess.run(
                    docker_test_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace', timeout=30
                )
                test_stdout = test_result.stdout or ""
                test_stderr = test_result.stderr or ""
            except subprocess.TimeoutExpired:
                test_stderr = "Tests timed out."

        elif language == 'cpp':
            test_file = f"tests_task_{task_id}.cpp"
            if os.path.exists(os.path.join(host_tests_dir, test_file)):
                test_cmd = ['bash', '-c', f"g++ -DRUNNING_TESTS /tests/{test_file} -o /tests/test_app_{task_id} && /tests/test_app_{task_id}"]
                docker_test_cmd = ['docker', 'run', '--rm', '-v', f"{host_tests_dir}:/tests", '-v', f"{host_tests_dir}:/usr/src/app", 'python-runner'] + test_cmd
                try:
                    test_result = subprocess.run(
                        docker_test_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace', timeout=30
                    )
                    if test_result.returncode == 0:
                        test_stdout = "✅ Všetky testy prešli.\n" + (test_result.stdout or "")
                    else:
                        test_stdout = "❌ Testy zlyhali.\n" + (test_result.stdout or "") + (test_result.stderr or "")
                except subprocess.TimeoutExpired:
                    test_stderr = "Tests timed out."
            else:
                test_stdout = "Testovací súbor nebol nájdený."

        elif language == 'java':
            match = re.search(r'public\s+class\s+(\w+)', code)
            student_class_name = match.group(1) if match else "Main"
            student_filename = f"{student_class_name}.java"
            test_class_name = f"TestMain_{task_id}"
            test_filename = f"{test_class_name}.java"

            if os.path.exists(os.path.join(host_tests_dir, test_filename)):
                test_cmd = [
                    'bash', '-c',
                    f"javac /usr/src/app/{student_filename} /usr/src/app/{test_filename} && java -DTEST=true -cp /usr/src/app:/tests {test_class_name}"
                ]
                docker_test_cmd = ['docker', 'run', '--rm', '-v', f"{host_tests_dir}:/usr/src/app", '-v', f"{host_tests_dir}:/tests", 'python-runner'] + test_cmd
                
                try:
                    # Java kompilácia trvá dlhšie, preto 45s
                    test_result = subprocess.run(
                        docker_test_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace', timeout=45
                    )
                    if test_result.returncode == 0:
                        test_stdout = "✅ Všetky testy prešli.\n" + (test_result.stdout or "")
                    else:
                        test_stdout = "❌ Testy zlyhali.\n" + (test_result.stdout or "") + (test_result.stderr or "")
                except subprocess.TimeoutExpired:
                    test_stderr = "Tests timed out (Java)."
            else:
                test_stdout = "Testovací súbor nebol nájdený."

        CodeRun.objects.create(
            user=request.user, task=task, code=code,
            output=full_output, tests_output=test_stdout + test_stderr
        )

        return JsonResponse({
            "code_stdout": result.stdout or "",
            "code_stderr": result.stderr or "",
            "code_returncode": result.returncode,
            "test_stdout": test_stdout,
            "test_stderr": test_stderr,
        })

    except Exception as e:
        logger.exception("Chyba pri spúšťaní kódu")
        return JsonResponse({"error": str(e)}, status=500)

# --- OLLAMA INTEGRATION ZAČIATOK ---

def query_ollama(prompt, model="llama3"):
    """
    Pomocná funkcia na komunikáciu s lokálnou AI.
    """
    url = "http://localhost:11434/api/generate"
    data = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json"  
    }
    
    try:
        response = requests.post(url, json=data, timeout=60) # Timeout 60s, AI chvíľu premýšľa
        response.raise_for_status()
        return response.json().get('response', '')
    except requests.exceptions.RequestException as e:
        print(f"Chyba Ollama: {e}")
        return None

@login_required
def generate_task_assignment(request):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Nemáš práva.'}, status=403)

    lang = request.GET.get('lang', 'python')

    # Nastavenie špecifík pre jazyky
    if lang == 'cpp':
        lang_name = "C++"
        code_example = "#include <iostream>\n..."
        test_instruction = "Vytvor súbor s 'int main()', ktorý includuje riešenie a pomocou 'assert()' overí výsledok. Kód riešenia (main) obaľ do '#ifndef RUNNING_TESTS'."
    elif lang == 'java':
        lang_name = "Java"
        code_example = "public class Main { ... }"
        test_instruction = """
        Vytvor testovaciu triedu s názvom 'public class TestMain'.
        Táto trieda musí mať metódu 'public static void main(String[] args)'.
        V nej vytvor inštanciu testovanej triedy a over výsledky.
        Ak test zlyhá, vypíš chybu a zavolaj System.exit(1).
        """
    else:
        lang_name = "Python"
        code_example = "def function(): ..."
        test_instruction = "Python kód s 'import unittest' a triedou dediacou z unittest.TestCase."

    system_instruction = f"""
    Si expert na {lang_name}. Vygeneruj úlohu na refaktorizáciu.
    
    DÔLEŽITÉ: Nepoužívaj JSON formát! Použi presne tento formát s oddeľovačmi:
    
    ===TITLE===
    (Sem napíš názov úlohy)
    ===DESCRIPTION===
    (Sem napíš popis problému)
    ===CODE===
    (Sem vlož len čistý {lang_name} kód zadania. Nepoužívaj markdown značky. Ak je to C++ alebo Java, pridaj do main() funkcie ochranu.)
    ===TESTS===
    (Sem vlož {test_instruction})
    """

    user_message = f"Vygeneruj jednu stredne ťažkú úlohu pre {lang_name} (Spaghetti code)."

    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": user_message}
    ]

    ai_response_text = query_ollama_chat(messages)

    if ai_response_text:
        task_data = parse_ai_response_custom(ai_response_text)
        
        if task_data.get('input_code'):
            return JsonResponse(task_data)
        else:
            return JsonResponse({'error': 'AI nevrátila kód v správnom formáte. Skús znova.'}, status=500)
    else:
        return JsonResponse({'error': 'Ollama neodpovedá.'}, status=503)


@login_required
def get_task_hint(request, task_id):
    """
    Vráti nápovedu od AI pre konkrétnu úlohu.
    """
    # 1. Načítame úlohu z DB
    task = get_object_or_404(RefactoringTask, id=task_id)
    
    # 2. Vytvoríme prompt pre AI
    prompt = f"""
    Si nápomocný učiteľ programovania. Študent rieši úlohu na refaktorizáciu.
    Názov úlohy: {task.title}
    Popis problému: {task.description}
    Kód na opravu:
    {task.input_code}

    Študent sa zasekol. Napíš mu krátku, povzbudivú radu (max 2-3 vety), na čo sa má sústrediť (napr. "Všimni si, že sa ten istý kód opakuje 3x...").
    NEPREZRÁDZAJ celé riešenie. Odpovedz v Slovenčine.
    
    Výstup musí byť JSON v tvare:
    {{ "hint": "Tvoja rada sem..." }}
    """

    # 3. Zavoláme našu existujúcu funkciu query_ollama
    ai_response = query_ollama(prompt)

    if ai_response:
        try:
            data = json.loads(ai_response)
            return JsonResponse({'hint': data.get('hint', 'AI nenašla konkrétnu radu.')})
        except json.JSONDecodeError:
            return JsonResponse({'hint': ai_response})
    
    return JsonResponse({'error': 'AI momentálne neodpovedá.'}, status=503)
# --- OLLAMA INTEGRATION KONIEC ---

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

        # 1. SYSTEM PROMPT (TOTO JE MOZOG AI)
        system_content = f"""
        You are a strict code mentor. The student is working on "{task.title}".
        Student's code:
        {task.input_code}

        INSTRUCTIONS:
        1. Analyze the code logic in English.
        2. Identify the bug but DO NOT fix it for the student.
        3. Provide a helpful hint using the Socratic method (ask questions).
        4. **OUTPUT THE FINAL RESPONSE IN SLOVAK LANGUAGE ONLY.**
        """

        # 2. Zostavenie správ pre Ollama Chat API
        messages_payload = []
        
        # A) Pridáme System inštrukciu
        messages_payload.append({
            "role": "system",
            "content": system_content
        })

        # B) Pridáme históriu (aby si pamätal kontext)
        for msg in history:
            role = "user" if msg['sender'] == 'user' else "assistant"
            messages_payload.append({
                "role": role,
                "content": msg['text']
            })

        # C) Pridáme aktuálnu správu od teba
        messages_payload.append({
            "role": "user",
            "content": user_message
        })

        # 3. Odoslanie do AI
        ai_response_text = query_ollama_chat(messages_payload)

        if ai_response_text:
            return JsonResponse({'response': ai_response_text})
        else:
            return JsonResponse({'error': 'AI mentor spí (Ollama neodpovedá).'}, status=503)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    

def query_ollama_chat(messages, model="llama3"):
    """
    Odosiela konverzáciu na Ollama API.
    Toto nahrádza ten dlhý try-except blok vo vnútri funkcií.
    """
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
    


def parse_ai_response_custom(text):
    """
    Parsuje text z AI, ktorý je rozdelený vlastnými značkami (===TITLE=== atď.).
    Odolné voči chybám v JSONe.
    """
    data = {}
    markers = {
        "title": "===TITLE===",
        "description": "===DESCRIPTION===",
        "input_code": "===CODE===",
        "expected_output": "===TESTS==="
    }
    
    for key, marker in markers.items():
        if marker in text:
            start = text.find(marker) + len(marker)
            content = text[start:]
            
            next_marker_pos = len(text)
            for m in markers.values():
                pos = content.find(m)
                if pos != -1 and pos < next_marker_pos:
                    next_marker_pos = pos
            
            clean_content = content[:next_marker_pos].strip()
            for lang in ['', 'python', 'cpp', 'java', 'c++']:
                clean_content = clean_content.replace(f"```{lang}", "").replace("```", "")
            
            data[key] = clean_content.strip()

    return data