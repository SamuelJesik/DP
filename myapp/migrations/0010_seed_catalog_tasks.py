import os
from django.db import migrations

# ── Task 1: Error Detection ────────────────────────────────────────────────────
TASK1_CODE = '''\
def factorial(n):
    """Returns the factorial of n."""
    if n == 0:
        return 1
    result = 1
    for i in range(1, n):   # AI-generated bug: off-by-one, misses multiplying by n
        result *= i
    return result


if __name__ == "__main__":
    print(factorial(5))   # prints 24 instead of 120
    print(factorial(0))   # prints 1  (correct)
    print(factorial(1))   # prints 1  (correct by accident)
'''

TASK1_TESTS = '''\
import unittest
from temp_code_{id} import factorial


class TestFactorial(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(factorial(0), 1)

    def test_one(self):
        self.assertEqual(factorial(1), 1)

    def test_five(self):
        self.assertEqual(factorial(5), 120)

    def test_ten(self):
        self.assertEqual(factorial(10), 3628800)


if __name__ == "__main__":
    unittest.main()
'''

# ── Task 2: Test Writing ───────────────────────────────────────────────────────
TASK2_BUGGY_CODE = '''\
class Stack:
    """A simple stack implementation — but it has bugs. Write tests to find them."""

    def __init__(self):
        self.items = []

    def push(self, item):
        self.items.append(item)

    def pop(self):
        # Bug 1: no empty-check — raises IndexError on empty stack
        return self.items.pop()

    def peek(self):
        # Bug 2: no empty-check — raises IndexError on empty stack
        return self.items[-1]

    def is_empty(self):
        return len(self.items) == 0

    def size(self):
        # Bug 3: off-by-one — returns len + 1
        return len(self.items) + 1
'''

TASK2_SOLUTION_CODE = '''\
class Stack:
    def __init__(self):
        self.items = []

    def push(self, item):
        self.items.append(item)

    def pop(self):
        if self.is_empty():
            raise IndexError("pop from empty stack")
        return self.items.pop()

    def peek(self):
        if self.is_empty():
            raise IndexError("peek from empty stack")
        return self.items[-1]

    def is_empty(self):
        return len(self.items) == 0

    def size(self):
        return len(self.items)
'''

# ── Task 3: Refactoring ────────────────────────────────────────────────────────
TASK3_CODE = '''\
def process_grades(grades):
    # Calculate average for math
    math_total = 0
    math_count = 0
    for g in grades["math"]:
        math_total = math_total + g
        math_count = math_count + 1
    math_avg = math_total / math_count
    if math_avg >= 90:
        math_grade = "A"
    elif math_avg >= 80:
        math_grade = "B"
    elif math_avg >= 70:
        math_grade = "C"
    elif math_avg >= 60:
        math_grade = "D"
    else:
        math_grade = "F"

    # Calculate average for science (same logic copy-pasted)
    science_total = 0
    science_count = 0
    for g in grades["science"]:
        science_total = science_total + g
        science_count = science_count + 1
    science_avg = science_total / science_count
    if science_avg >= 90:
        science_grade = "A"
    elif science_avg >= 80:
        science_grade = "B"
    elif science_avg >= 70:
        science_grade = "C"
    elif science_avg >= 60:
        science_grade = "D"
    else:
        science_grade = "F"

    # Calculate average for english (same logic copy-pasted again)
    english_total = 0
    english_count = 0
    for g in grades["english"]:
        english_total = english_total + g
        english_count = english_count + 1
    english_avg = english_total / english_count
    if english_avg >= 90:
        english_grade = "A"
    elif english_avg >= 80:
        english_grade = "B"
    elif english_avg >= 70:
        english_grade = "C"
    elif english_avg >= 60:
        english_grade = "D"
    else:
        english_grade = "F"

    return {"math": math_grade, "science": science_grade, "english": english_grade}


if __name__ == "__main__":
    test_grades = {
        "math": [85, 92, 78, 90],
        "science": [70, 65, 80, 75],
        "english": [55, 60, 58, 62],
    }
    print(process_grades(test_grades))
'''

TASK3_TESTS = '''\
import unittest
from temp_code_{id} import process_grades


class TestProcessGrades(unittest.TestCase):
    def _g(self, math, science, english):
        return {"math": math, "science": science, "english": english}

    def test_a_grade(self):
        result = process_grades(self._g([95, 92], [90, 91], [93, 94]))
        self.assertEqual(result["math"], "A")

    def test_b_grade(self):
        result = process_grades(self._g([85, 82], [90, 91], [93, 94]))
        self.assertEqual(result["math"], "B")

    def test_c_grade(self):
        result = process_grades(self._g([72, 74], [90, 91], [93, 94]))
        self.assertEqual(result["math"], "C")

    def test_d_grade(self):
        result = process_grades(self._g([60, 62], [90, 91], [93, 94]))
        self.assertEqual(result["math"], "D")

    def test_f_grade(self):
        result = process_grades(self._g([50, 55], [90, 91], [93, 94]))
        self.assertEqual(result["math"], "F")

    def test_all_subjects(self):
        result = process_grades(self._g([85, 92, 78, 90], [70, 65, 80, 75], [55, 60, 58, 62]))
        self.assertEqual(result["math"], "B")
        self.assertEqual(result["science"], "C")
        self.assertEqual(result["english"], "F")


if __name__ == "__main__":
    unittest.main()
'''


def seed_tasks(apps, schema_editor):
    from django.conf import settings

    RefactoringTask = apps.get_model('myapp', 'RefactoringTask')
    test_dir = os.path.join(settings.BASE_DIR, 'test_directory')
    os.makedirs(test_dir, exist_ok=True)

    # ── Task 1: Error Detection ────────────────────────────────────────────────
    t1 = RefactoringTask.objects.create(
        title="Error Detection: Fix the Factorial",
        description=(
            "The following function was AI-generated and is supposed to compute the factorial of n. "
            "It contains a subtle bug that causes it to return the wrong answer for most inputs. "
            "Find the bug and fix it so that all unit tests pass."
        ),
        language='python',
        task_type='error_detection',
        input_code=TASK1_CODE,
        expected_output=TASK1_TESTS.replace('{id}', '__PLACEHOLDER__'),
        solution_code=None,
    )
    # Write test file with the actual task id
    test_content = TASK1_TESTS.replace('{id}', str(t1.id))
    t1.expected_output = test_content
    t1.save()
    with open(os.path.join(test_dir, f'tests_task_{t1.id}.py'), 'w', encoding='utf-8') as f:
        f.write(test_content)

    # ── Task 2: Test Writing ───────────────────────────────────────────────────
    t2 = RefactoringTask.objects.create(
        title="Test Writing: Catch the Stack Bugs",
        description=(
            "The Stack class below has three bugs. "
            "Your job is NOT to fix the code — instead, write unittest test cases that expose each bug. "
            "Your tests should FAIL on the buggy version and PASS on a correct implementation. "
            "Hint: think about edge cases — what happens when the stack is empty? Does size() return the right number?"
        ),
        language='python',
        task_type='test_writing',
        input_code=TASK2_BUGGY_CODE,
        expected_output=None,
        solution_code=TASK2_SOLUTION_CODE,
    )

    # ── Task 3: Refactoring ────────────────────────────────────────────────────
    t3 = RefactoringTask.objects.create(
        title="Refactoring: Grade Calculator",
        description=(
            "The function below calculates letter grades for three subjects. "
            "It works correctly, but the code is pure spaghetti — the same logic is copy-pasted three times. "
            "Refactor it: eliminate the duplication by extracting helper function(s), "
            "while keeping the output identical. All unit tests must still pass."
        ),
        language='python',
        task_type='refactoring',
        input_code=TASK3_CODE,
        expected_output=TASK3_TESTS.replace('{id}', '__PLACEHOLDER__'),
        solution_code=None,
    )
    test_content = TASK3_TESTS.replace('{id}', str(t3.id))
    t3.expected_output = test_content
    t3.save()
    with open(os.path.join(test_dir, f'tests_task_{t3.id}.py'), 'w', encoding='utf-8') as f:
        f.write(test_content)


def unseed_tasks(apps, schema_editor):
    from django.conf import settings

    RefactoringTask = apps.get_model('myapp', 'RefactoringTask')
    titles = [
        "Error Detection: Fix the Factorial",
        "Test Writing: Catch the Stack Bugs",
        "Refactoring: Grade Calculator",
    ]
    test_dir = os.path.join(settings.BASE_DIR, 'test_directory')
    for task in RefactoringTask.objects.filter(title__in=titles):
        for path in [
            os.path.join(test_dir, f'tests_task_{task.id}.py'),
            os.path.join(test_dir, f'temp_code_{task.id}.py'),
        ]:
            if os.path.exists(path):
                os.remove(path)
        task.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0009_refactoringtask_task_type_solution_code'),
    ]

    operations = [
        migrations.RunPython(seed_tasks, reverse_code=unseed_tasks),
    ]
