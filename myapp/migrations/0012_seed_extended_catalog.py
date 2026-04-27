import os
from django.db import migrations

# ── Error Detection 2: Binary Search ──────────────────────────────────────────
ED2_CODE = '''\
def binary_search(arr, target):
    """Returns the index of target in sorted arr, or -1 if not found."""
    left, right = 0, len(arr)   # Bug: right should be len(arr) - 1

    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1


if __name__ == "__main__":
    data = [1, 3, 5, 7, 9, 11, 13]
    print(binary_search(data, 7))   # expected 3
    print(binary_search(data, 1))   # expected 0
    print(binary_search(data, 4))   # expected -1
'''

ED2_TESTS = '''\
import unittest
from temp_code_{id} import binary_search


class TestBinarySearch(unittest.TestCase):
    def test_found_middle(self):
        self.assertEqual(binary_search([1, 3, 5, 7, 9], 5), 2)

    def test_found_first(self):
        self.assertEqual(binary_search([1, 3, 5, 7, 9], 1), 0)

    def test_found_last(self):
        self.assertEqual(binary_search([1, 3, 5, 7, 9], 9), 4)

    def test_not_found(self):
        self.assertEqual(binary_search([1, 3, 5, 7, 9], 4), -1)

    def test_single_element_found(self):
        self.assertEqual(binary_search([42], 42), 0)

    def test_single_element_not_found(self):
        self.assertEqual(binary_search([42], 7), -1)


if __name__ == "__main__":
    unittest.main()
'''

# ── Error Detection 3: FizzBuzz ────────────────────────────────────────────────
ED3_CODE = '''\
def fizzbuzz(n):
    """Returns a list of FizzBuzz strings from 1 to n."""
    result = []
    for i in range(1, n + 1):
        if i % 3 == 0:           # Bug: divisibility by 15 must be checked first
            result.append("Fizz")
        elif i % 5 == 0:
            result.append("Buzz")
        elif i % 15 == 0:        # Bug: this branch is never reached
            result.append("FizzBuzz")
        else:
            result.append(str(i))
    return result


if __name__ == "__main__":
    print(fizzbuzz(15))
'''

ED3_TESTS = '''\
import unittest
from temp_code_{id} import fizzbuzz


class TestFizzBuzz(unittest.TestCase):
    def test_fizz(self):
        self.assertEqual(fizzbuzz(3)[2], "Fizz")

    def test_buzz(self):
        self.assertEqual(fizzbuzz(5)[4], "Buzz")

    def test_fizzbuzz(self):
        self.assertEqual(fizzbuzz(15)[14], "FizzBuzz")

    def test_regular_number(self):
        self.assertEqual(fizzbuzz(1)[0], "1")

    def test_length(self):
        self.assertEqual(len(fizzbuzz(15)), 15)


if __name__ == "__main__":
    unittest.main()
'''

# ── Test Writing 2: BankAccount ────────────────────────────────────────────────
TW2_BUGGY = '''\
class BankAccount:
    """A simple bank account. Contains 3 bugs — write tests to find them."""

    def __init__(self, owner, balance=0):
        self.owner = owner
        self.balance = balance

    def deposit(self, amount):
        # Bug 1: accepts negative or zero amounts without error
        self.balance += amount

    def withdraw(self, amount):
        # Bug 2: allows balance to go negative (no insufficient-funds check)
        self.balance -= amount

    def transfer(self, other, amount):
        # Bug 3: deducts from self even if self has insufficient funds
        self.balance -= amount
        other.balance += amount

    def get_balance(self):
        return self.balance
'''

TW2_SOLUTION = '''\
class BankAccount:
    def __init__(self, owner, balance=0):
        self.owner = owner
        self.balance = balance

    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        self.balance += amount

    def withdraw(self, amount):
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        if amount > self.balance:
            raise ValueError("Insufficient funds")
        self.balance -= amount

    def transfer(self, other, amount):
        if amount > self.balance:
            raise ValueError("Insufficient funds for transfer")
        self.balance -= amount
        other.balance += amount

    def get_balance(self):
        return self.balance
'''

# ── Test Writing 3: TemperatureConverter ──────────────────────────────────────
TW3_BUGGY = '''\
class TemperatureConverter:
    """Converts between temperature scales. Contains 2 bugs — write tests to find them."""

    @staticmethod
    def celsius_to_fahrenheit(c):
        return c * 9 / 5 + 32           # correct

    @staticmethod
    def fahrenheit_to_celsius(f):
        return (f - 32) * 5 / 9         # correct

    @staticmethod
    def celsius_to_kelvin(c):
        return c + 273                  # Bug: should be + 273.15

    @staticmethod
    def kelvin_to_celsius(k):
        return k - 273                  # Bug: should be - 273.15
'''

TW3_SOLUTION = '''\
class TemperatureConverter:
    @staticmethod
    def celsius_to_fahrenheit(c):
        return c * 9 / 5 + 32

    @staticmethod
    def fahrenheit_to_celsius(f):
        return (f - 32) * 5 / 9

    @staticmethod
    def celsius_to_kelvin(c):
        return c + 273.15

    @staticmethod
    def kelvin_to_celsius(k):
        return k - 273.15
'''

# ── Refactoring 2: Salary Calculator ──────────────────────────────────────────
R2_CODE = '''\
def calculate_salaries(employees):
    full_time_results = []
    for emp in employees["full_time"]:
        gross = emp["hours"] * emp["rate"]
        if gross > 3000:
            tax = gross * 0.25
        elif gross > 1500:
            tax = gross * 0.15
        else:
            tax = gross * 0.10
        net = gross - tax
        full_time_results.append({"name": emp["name"], "gross": round(gross, 2),
                                   "tax": round(tax, 2), "net": round(net, 2)})

    # Exact same logic copy-pasted for part-time employees
    part_time_results = []
    for emp in employees["part_time"]:
        gross = emp["hours"] * emp["rate"]
        if gross > 3000:
            tax = gross * 0.25
        elif gross > 1500:
            tax = gross * 0.15
        else:
            tax = gross * 0.10
        net = gross - tax
        part_time_results.append({"name": emp["name"], "gross": round(gross, 2),
                                   "tax": round(tax, 2), "net": round(net, 2)})

    return {"full_time": full_time_results, "part_time": part_time_results}


if __name__ == "__main__":
    data = {
        "full_time": [{"name": "Alice", "hours": 160, "rate": 25}],
        "part_time": [{"name": "Bob",   "hours": 80,  "rate": 15}],
    }
    print(calculate_salaries(data))
'''

R2_TESTS = '''\
import unittest
from temp_code_{id} import calculate_salaries


class TestCalculateSalaries(unittest.TestCase):
    def setUp(self):
        self.data = {
            "full_time": [{"name": "Alice", "hours": 160, "rate": 25}],
            "part_time": [{"name": "Bob",   "hours": 80,  "rate": 15}],
        }

    def test_full_time_net(self):
        result = calculate_salaries(self.data)
        self.assertAlmostEqual(result["full_time"][0]["net"], 3000.0)

    def test_part_time_net(self):
        result = calculate_salaries(self.data)
        self.assertAlmostEqual(result["part_time"][0]["net"], 1080.0)

    def test_high_earner_tax(self):
        data = {"full_time": [{"name": "CEO", "hours": 200, "rate": 30}], "part_time": []}
        result = calculate_salaries(data)
        self.assertAlmostEqual(result["full_time"][0]["tax"], 1500.0)

    def test_low_earner_tax(self):
        data = {"full_time": [], "part_time": [{"name": "Intern", "hours": 40, "rate": 10}]}
        result = calculate_salaries(data)
        self.assertAlmostEqual(result["part_time"][0]["tax"], 40.0)


if __name__ == "__main__":
    unittest.main()
'''

# ── Refactoring 3: Shape Report ────────────────────────────────────────────────
R3_CODE = '''\
import math


def print_shape_report(shapes):
    print("=== Shape Report ===")
    for shape in shapes:
        if shape["type"] == "circle":
            area = math.pi * shape["radius"] ** 2
            perimeter = 2 * math.pi * shape["radius"]
            print(f"Circle      - Area: {area:.2f}, Perimeter: {perimeter:.2f}")
        elif shape["type"] == "rectangle":
            area = shape["width"] * shape["height"]
            perimeter = 2 * (shape["width"] + shape["height"])
            print(f"Rectangle   - Area: {area:.2f}, Perimeter: {perimeter:.2f}")
        elif shape["type"] == "triangle":
            a, b, c = shape["a"], shape["b"], shape["c"]
            s = (a + b + c) / 2
            area = (s * (s - a) * (s - b) * (s - c)) ** 0.5
            perimeter = a + b + c
            print(f"Triangle    - Area: {area:.2f}, Perimeter: {perimeter:.2f}")

    # Total area calculation — same logic copy-pasted again
    total_area = 0
    for shape in shapes:
        if shape["type"] == "circle":
            total_area += math.pi * shape["radius"] ** 2
        elif shape["type"] == "rectangle":
            total_area += shape["width"] * shape["height"]
        elif shape["type"] == "triangle":
            a, b, c = shape["a"], shape["b"], shape["c"]
            s = (a + b + c) / 2
            total_area += (s * (s - a) * (s - b) * (s - c)) ** 0.5
    print(f"Total area: {total_area:.2f}")


if __name__ == "__main__":
    shapes = [
        {"type": "circle",    "radius": 5},
        {"type": "rectangle", "width": 4, "height": 6},
        {"type": "triangle",  "a": 3, "b": 4, "c": 5},
    ]
    print_shape_report(shapes)
'''

R3_TESTS = '''\
import math
import unittest
from io import StringIO
import sys
from temp_code_{id} import print_shape_report


class TestShapeReport(unittest.TestCase):
    def _capture(self, shapes):
        buf = StringIO()
        sys.stdout = buf
        print_shape_report(shapes)
        sys.stdout = sys.__stdout__
        return buf.getvalue()

    def test_circle_area_in_output(self):
        out = self._capture([{"type": "circle", "radius": 5}])
        self.assertIn("78.54", out)

    def test_rectangle_area_in_output(self):
        out = self._capture([{"type": "rectangle", "width": 4, "height": 6}])
        self.assertIn("24.00", out)

    def test_triangle_area_in_output(self):
        out = self._capture([{"type": "triangle", "a": 3, "b": 4, "c": 5}])
        self.assertIn("6.00", out)

    def test_total_area(self):
        shapes = [
            {"type": "rectangle", "width": 3, "height": 4},
            {"type": "rectangle", "width": 2, "height": 5},
        ]
        out = self._capture(shapes)
        self.assertIn("22.00", out)


if __name__ == "__main__":
    unittest.main()
'''

# ── Code Extension 1: Library search ──────────────────────────────────────────
CE1_CODE = '''\
class Library:
    """A simple book library. Your task: add the search_by_author() method."""

    def __init__(self):
        self.books = []

    def add_book(self, title, author):
        self.books.append({"title": title, "author": author})

    def list_books(self):
        return list(self.books)

    def count(self):
        return len(self.books)

    # TODO: Add a method search_by_author(author) that:
    #   - Returns a list of book dicts whose "author" matches (case-insensitive)
    #   - Returns an empty list if no match is found


if __name__ == "__main__":
    lib = Library()
    lib.add_book("Clean Code", "Robert Martin")
    lib.add_book("The Pragmatic Programmer", "David Thomas")
    lib.add_book("Agile Software Development", "Robert Martin")
    print(lib.list_books())
    print(lib.count())
'''

CE1_TESTS = '''\
import unittest
from temp_code_{id} import Library


class TestLibrarySearch(unittest.TestCase):
    def setUp(self):
        self.lib = Library()
        self.lib.add_book("Clean Code", "Robert Martin")
        self.lib.add_book("The Pragmatic Programmer", "David Thomas")
        self.lib.add_book("Agile Software Development", "Robert Martin")

    def test_search_returns_correct_count(self):
        results = self.lib.search_by_author("Robert Martin")
        self.assertEqual(len(results), 2)

    def test_search_case_insensitive(self):
        results = self.lib.search_by_author("robert martin")
        self.assertEqual(len(results), 2)

    def test_search_no_match(self):
        results = self.lib.search_by_author("Unknown Author")
        self.assertEqual(results, [])

    def test_search_correct_title(self):
        results = self.lib.search_by_author("David Thomas")
        self.assertEqual(results[0]["title"], "The Pragmatic Programmer")

    def test_existing_methods_unaffected(self):
        self.assertEqual(self.lib.count(), 3)


if __name__ == "__main__":
    unittest.main()
'''

# ── Code Extension 2: ShoppingCart discount ───────────────────────────────────
CE2_CODE = '''\
class ShoppingCart:
    """A shopping cart. Your task: add the apply_discount() method."""

    def __init__(self):
        self.items = []
        self._discount = 0

    def add_item(self, name, price, quantity=1):
        self.items.append({"name": name, "price": price, "quantity": quantity})

    def subtotal(self):
        return sum(item["price"] * item["quantity"] for item in self.items)

    def total(self):
        return round(self.subtotal() * (1 - self._discount / 100), 2)

    # TODO: Add a method apply_discount(percent) that:
    #   - Accepts an integer or float percent (0–100 inclusive)
    #   - Raises ValueError if percent is outside 0–100
    #   - Stores the discount so that total() reflects it


if __name__ == "__main__":
    cart = ShoppingCart()
    cart.add_item("Laptop", 1200)
    cart.add_item("Mouse", 25, 2)
    print(f"Subtotal: {cart.subtotal()}")
    print(f"Total:    {cart.total()}")
'''

CE2_TESTS = '''\
import unittest
from temp_code_{id} import ShoppingCart


class TestShoppingCartDiscount(unittest.TestCase):
    def setUp(self):
        self.cart = ShoppingCart()
        self.cart.add_item("Laptop", 1000)
        self.cart.add_item("Mouse", 50, 2)   # subtotal = 1100

    def test_no_discount(self):
        self.assertAlmostEqual(self.cart.total(), 1100.0)

    def test_ten_percent(self):
        self.cart.apply_discount(10)
        self.assertAlmostEqual(self.cart.total(), 990.0)

    def test_full_discount(self):
        self.cart.apply_discount(100)
        self.assertAlmostEqual(self.cart.total(), 0.0)

    def test_invalid_above_100(self):
        with self.assertRaises(ValueError):
            self.cart.apply_discount(110)

    def test_invalid_negative(self):
        with self.assertRaises(ValueError):
            self.cart.apply_discount(-5)

    def test_subtotal_unaffected(self):
        self.cart.apply_discount(50)
        self.assertAlmostEqual(self.cart.subtotal(), 1100.0)


if __name__ == "__main__":
    unittest.main()
'''

# ── Code Extension 3: Calculator undo ─────────────────────────────────────────
CE3_CODE = '''\
class Calculator:
    """A chainable calculator. Your task: add the undo() method."""

    def __init__(self):
        self.result = 0
        self._history = []

    def add(self, n):
        self._history.append(self.result)
        self.result += n
        return self

    def subtract(self, n):
        self._history.append(self.result)
        self.result -= n
        return self

    def multiply(self, n):
        self._history.append(self.result)
        self.result *= n
        return self

    def reset(self):
        self.result = 0
        self._history.clear()
        return self

    # TODO: Add an undo() method that:
    #   - Reverts result to the value before the last operation
    #   - Raises IndexError if there is nothing to undo
    #   - Returns self (to allow chaining)


if __name__ == "__main__":
    calc = Calculator()
    calc.add(10).multiply(3).subtract(5)
    print(calc.result)   # 25
'''

CE3_TESTS = '''\
import unittest
from temp_code_{id} import Calculator


class TestCalculatorUndo(unittest.TestCase):
    def test_undo_single_operation(self):
        calc = Calculator()
        calc.add(10)
        calc.undo()
        self.assertEqual(calc.result, 0)

    def test_undo_restores_previous_value(self):
        calc = Calculator()
        calc.add(10).multiply(3)
        calc.undo()
        self.assertEqual(calc.result, 10)

    def test_undo_multiple_times(self):
        calc = Calculator()
        calc.add(5).add(3).subtract(2)
        calc.undo()
        calc.undo()
        self.assertEqual(calc.result, 5)

    def test_undo_raises_on_empty(self):
        calc = Calculator()
        with self.assertRaises(IndexError):
            calc.undo()

    def test_undo_returns_self(self):
        calc = Calculator()
        calc.add(10)
        self.assertIs(calc.undo(), calc)

    def test_chained_undo(self):
        calc = Calculator()
        calc.add(10).multiply(2)
        calc.undo().undo()
        self.assertEqual(calc.result, 0)


if __name__ == "__main__":
    unittest.main()
'''


SEED_TASKS = [
    dict(
        title="Fix the Bug: Binary Search",
        description=(
            "The binary_search function below was AI-generated and is supposed to find the index of a target "
            "value in a sorted list. It contains a subtle bug that causes an IndexError on some inputs. "
            "Find it and fix it so all tests pass."
        ),
        task_type='error_detection', language='python',
        input_code=ED2_CODE, tests=ED2_TESTS, solution_code=None,
    ),
    dict(
        title="Fix the Bug: FizzBuzz",
        description=(
            "The fizzbuzz function below has a logic error in the order of its conditions, causing it to "
            "never produce 'FizzBuzz'. Find the bug and fix it."
        ),
        task_type='error_detection', language='python',
        input_code=ED3_CODE, tests=ED3_TESTS, solution_code=None,
    ),
    dict(
        title="Write Tests for: BankAccount",
        description=(
            "The BankAccount class below has 3 bugs: it accepts invalid deposit amounts, allows overdrafts, "
            "and transfers funds even when the balance is insufficient. "
            "Write unittest cases that FAIL on this buggy version and PASS on a correct implementation."
        ),
        task_type='test_writing', language='python',
        input_code=TW2_BUGGY, tests=None, solution_code=TW2_SOLUTION,
    ),
    dict(
        title="Write Tests for: TemperatureConverter",
        description=(
            "The TemperatureConverter class below has 2 bugs in its Kelvin conversion methods — "
            "it uses 273 instead of 273.15. "
            "Write unittest cases that FAIL on this buggy version and PASS on a correct implementation."
        ),
        task_type='test_writing', language='python',
        input_code=TW3_BUGGY, tests=None, solution_code=TW3_SOLUTION,
    ),
    dict(
        title="Refactoring: Salary Calculator",
        description=(
            "The function below calculates salaries for full-time and part-time employees. "
            "It works correctly but the tax calculation logic is copy-pasted twice. "
            "Refactor it by extracting helper functions to eliminate the duplication. All tests must still pass."
        ),
        task_type='refactoring', language='python',
        input_code=R2_CODE, tests=R2_TESTS, solution_code=None,
    ),
    dict(
        title="Refactoring: Shape Report",
        description=(
            "The function below prints a report of geometric shapes and their total area. "
            "The area calculation logic is duplicated — once for printing, once for the total. "
            "Refactor it to eliminate the duplication without changing the output."
        ),
        task_type='refactoring', language='python',
        input_code=R3_CODE, tests=R3_TESTS, solution_code=None,
    ),
    dict(
        title="Extend: Add search_by_author() to Library",
        description=(
            "The Library class below manages a collection of books but is missing a search feature. "
            "Add a search_by_author(author) method that returns all books by a given author "
            "(case-insensitive match). Return an empty list if no match is found. "
            "Do not modify the existing methods."
        ),
        task_type='code_extension', language='python',
        input_code=CE1_CODE, tests=CE1_TESTS, solution_code=None,
    ),
    dict(
        title="Extend: Add apply_discount() to ShoppingCart",
        description=(
            "The ShoppingCart class below calculates totals but has no discount support. "
            "Add an apply_discount(percent) method that stores a percentage discount (0–100) "
            "and raises ValueError for invalid values. The existing total() method already "
            "reads self._discount, so once you store it correctly, total() will work automatically."
        ),
        task_type='code_extension', language='python',
        input_code=CE2_CODE, tests=CE2_TESTS, solution_code=None,
    ),
    dict(
        title="Extend: Add undo() to Calculator",
        description=(
            "The Calculator class below supports chained arithmetic operations but has no way to undo them. "
            "Add an undo() method that reverts result to the value before the last operation. "
            "It should raise IndexError if there is nothing to undo and return self for chaining. "
            "The _history list is already maintained by the existing methods — use it."
        ),
        task_type='code_extension', language='python',
        input_code=CE3_CODE, tests=CE3_TESTS, solution_code=None,
    ),
]


def seed_tasks(apps, schema_editor):
    from django.conf import settings
    RefactoringTask = apps.get_model('myapp', 'RefactoringTask')
    test_dir = os.path.join(settings.BASE_DIR, 'test_directory')
    os.makedirs(test_dir, exist_ok=True)

    for t in SEED_TASKS:
        task = RefactoringTask.objects.create(
            title=t['title'],
            description=t['description'],
            language=t['language'],
            task_type=t['task_type'],
            input_code=t['input_code'],
            expected_output=t['tests'].replace('{id}', '__PLACEHOLDER__') if t['tests'] else None,
            solution_code=t['solution_code'],
        )
        if t['tests']:
            test_content = t['tests'].replace('{id}', str(task.id))
            task.expected_output = test_content
            task.save()
            with open(os.path.join(test_dir, f'tests_task_{task.id}.py'), 'w', encoding='utf-8') as f:
                f.write(test_content)


def unseed_tasks(apps, schema_editor):
    from django.conf import settings
    RefactoringTask = apps.get_model('myapp', 'RefactoringTask')
    test_dir = os.path.join(settings.BASE_DIR, 'test_directory')
    titles = [t['title'] for t in SEED_TASKS]
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
        ('myapp', '0011_alter_refactoringtask_task_type'),
    ]

    operations = [
        migrations.RunPython(seed_tasks, reverse_code=unseed_tasks),
    ]
