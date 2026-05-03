console.log("Script loaded");

// Global editor instances — accessible from inline scripts in templates
var editor = null;
var readOnlyEditor = null;
var unitTestsEditor = null;

document.addEventListener('DOMContentLoaded', function() {

    require.config({
        paths: { 'vs': 'https://cdn.jsdelivr.net/npm/monaco-editor@0.44.0/min/vs' }
    });

    require(['vs/editor/editor.main'], function() {

        // ── Main editor (student writes code) ──────────────────────────
        var initialValue = '';
        if (typeof taskType !== 'undefined' && taskType === 'test_writing') {
            var lang = (typeof taskLanguage !== 'undefined') ? taskLanguage : 'python';
            if (lang === 'cpp') {
                initialValue =
                    "#include <cassert>\n" +
                    "#include <iostream>\n\n" +
                    "// Write your tests here using assert()\n" +
                    "// Example:\n" +
                    "// assert(myFunction(input) == expected);\n\n" +
                    "int main() {\n" +
                    "    // test_example\n" +
                    "    assert(true); // replace with real assertion\n\n" +
                    "    std::cout << \"All tests passed.\" << std::endl;\n" +
                    "    return 0;\n" +
                    "}\n";
            } else if (lang === 'java') {
                initialValue =
                    "class TestMain {\n" +
                    "    public static void main(String[] args) {\n" +
                    "        // Write your tests using assert statements\n" +
                    "        // Example:\n" +
                    "        // assert MyClass.myMethod(input) == expected : \"test description\";\n\n" +
                    "        assert true : \"replace with real assertion\";\n\n" +
                    "        System.out.println(\"All tests passed.\");\n" +
                    "    }\n" +
                    "}\n";
            } else {
                initialValue =
                    "import unittest\n\n\n" +
                    "class TestSolution(unittest.TestCase):\n" +
                    "    def test_example(self):\n" +
                    "        # Write your test here\n" +
                    "        pass\n\n\n" +
                    "if __name__ == '__main__':\n" +
                    "    unittest.main()\n";
            }
        }

        editor = monaco.editor.create(document.getElementById('editor'), {
            value: initialValue,
            language: 'python',
            theme: 'vs-dark',
            automaticLayout: true,
            minimap: { enabled: false },
            fontSize: 14,
            scrollBeyondLastLine: false
        });

        // ── Readonly editor (task code display) ────────────────────────
        readOnlyEditor = monaco.editor.create(document.getElementById('readonly-editor'), {
            value: (typeof readOnlyCode !== 'undefined') ? readOnlyCode : '',
            language: 'python',
            theme: 'vs-dark',
            readOnly: true,
            automaticLayout: true,
            minimap: { enabled: false },
            wordWrap: 'on',
            fontSize: 14,
            scrollBeyondLastLine: false
        });

        // ── Unit tests editor (tests display) ──────────────────────────
        if (document.getElementById('unit-tests-editor')) {
            unitTestsEditor = monaco.editor.create(document.getElementById('unit-tests-editor'), {
                value: (typeof expectedOutput !== 'undefined') ? expectedOutput : '',
                language: 'python',
                theme: 'vs-dark',
                readOnly: true,
                automaticLayout: true,
                minimap: { enabled: false },
                fontSize: 14,
                scrollBeyondLastLine: false
            });
        }

        console.log("Monaco Editor initialized");

        // ── File upload drop zone ───────────────────────────────────────
        var uploadZone       = document.getElementById('upload-zone');
        var fileInputElement = document.getElementById('fileInput');
        var fileChosenElement = document.getElementById('file-chosen');
        var submitBtn        = document.getElementById('submitBtn');

        function handleFile(file) {
            if (!file) return;
            fileChosenElement.textContent = file.name;
            submitBtn.disabled = false;
            uploadZone.classList.add('has-file');
            var reader = new FileReader();
            reader.onload = function(e) { editor.setValue(e.target.result); };
            reader.readAsText(file);
        }

        if (uploadZone && fileInputElement) {
            uploadZone.addEventListener('click', function(e) {
                if (e.target !== submitBtn && !submitBtn.contains(e.target))
                    fileInputElement.click();
            });
            fileInputElement.addEventListener('change', function(e) {
                handleFile(e.target.files[0]);
            });
            uploadZone.addEventListener('dragover', function(e) {
                e.preventDefault();
                uploadZone.classList.add('dragover');
            });
            uploadZone.addEventListener('dragleave', function() {
                uploadZone.classList.remove('dragover');
            });
            uploadZone.addEventListener('drop', function(e) {
                e.preventDefault();
                uploadZone.classList.remove('dragover');
                handleFile(e.dataTransfer.files[0]);
            });
        }

        // ── Run code button ─────────────────────────────────────────────
        var csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        var taskDataElement = document.getElementById('task-data');
        var task_id = taskDataElement ? taskDataElement.dataset.taskId : null;

        var runButton = document.getElementById('run-code');
        runButton.addEventListener('click', function() {
            var code = editor.getValue();
            var data = JSON.stringify({ code: code });

            console.log("Run button clicked");

            if (task_id) {
                var xhr = new XMLHttpRequest();
                xhr.open('POST', `/myapp/run-code/${task_id}/`, true);
                xhr.setRequestHeader('Content-Type', 'application/json');
                xhr.setRequestHeader('X-CSRFToken', csrfToken);

                xhr.onload = function() {
                    if (xhr.status == 200) {
                        var response = JSON.parse(xhr.responseText);

                        if (response.task_type === 'test_writing') {
                            var resultsDiv = document.getElementById('test-writing-results');
                            var buggyBox = document.getElementById('buggy-result-box');
                            var buggyLabel = document.getElementById('buggy-result-label');
                            var buggyOutput = document.getElementById('buggy-result-output');
                            var solutionBox = document.getElementById('solution-result-box');
                            var solutionLabel = document.getElementById('solution-result-label');
                            var solutionOutput = document.getElementById('solution-result-output');

                            buggyBox.className = 'tw-result-box ' + (response.buggy_passed ? 'tw-warning' : 'tw-success');
                            buggyLabel.innerHTML = response.buggy_passed
                                ? '<i data-lucide="alert-triangle" style="width:16px;height:16px;vertical-align:middle;margin-right:6px;"></i>Tests on buggy code: PASSED — your tests did not catch the bugs.'
                                : '<i data-lucide="check-circle" style="width:16px;height:16px;vertical-align:middle;margin-right:6px;"></i>Tests on buggy code: FAILED as expected — bugs detected!';
                            buggyOutput.textContent = response.buggy_output;

                            solutionBox.className = 'tw-result-box ' + (response.solution_passed ? 'tw-success' : 'tw-error');
                            solutionLabel.innerHTML = response.solution_passed
                                ? '<i data-lucide="check-circle" style="width:16px;height:16px;vertical-align:middle;margin-right:6px;"></i>Tests on solution code: PASSED — tests are correct.'
                                : '<i data-lucide="x-circle" style="width:16px;height:16px;vertical-align:middle;margin-right:6px;"></i>Tests on solution code: FAILED — tests have errors or are too strict.';
                            solutionOutput.textContent = response.solution_output;

                            if (typeof lucide !== 'undefined') lucide.createIcons();

                            resultsDiv.style.display = 'block';
                            resultsDiv.scrollIntoView({ behavior: 'smooth' });

                            var twCode = editor.getValue();
                            appendRunItem(twCode, '[Buggy] ' + response.buggy_output, '[Solution] ' + response.solution_output);

                        } else {
                            var codeOut   = (response.code_stdout  || '').trim();
                            var codeErr   = (response.code_stderr  || '').trim();
                            var testOut   = (response.test_stdout  || '').trim();
                            var testErr   = (response.test_stderr  || '').trim();
                            var rc        = response.code_returncode;

                            var allTests  = (testOut + testErr).toLowerCase();
                            var testsPassed = allTests && /\bok\b|passed/.test(allTests) && !/failed|error/.test(allTests);
                            var testsFailed = allTests && /failed|error/.test(allTests);

                            // ── Build structured modal body ──
                            var html = '';

                            // Code section
                            html += `<div>
                              <div class="modal-section-title">Code Output</div>
                              <div class="modal-block">`;
                            html += `<div class="modal-block-row ${codeOut ? 'modal-out' : 'modal-empty'}">${escapeHtml(codeOut || 'No output')}</div>`;
                            if (codeErr) html += `<div class="modal-block-row modal-err">${escapeHtml(codeErr)}</div>`;
                            html += `</div>`;
                            html += `<span class="modal-rc ${rc === 0 ? 'modal-rc-ok' : 'modal-rc-fail'}">exit code ${rc}</span>`;
                            html += `</div>`;

                            // Tests section
                            var testContent = testOut || testErr;
                            if (testContent) {
                                var testClass = testsPassed ? 'modal-tests-pass' : testsFailed ? 'modal-tests-fail' : 'modal-out';
                                html += `<div>
                                  <div class="modal-section-title">Test Results</div>
                                  <div class="modal-block">
                                    <div class="modal-block-row ${testClass}">${escapeHtml(testContent)}</div>
                                  </div>
                                </div>`;
                            }

                            testOutput.innerHTML = html;

                            // Status badge
                            var badge = document.getElementById('modal-status-badge');
                            if (badge) {
                                if (testsPassed)      { badge.textContent = '✓ Tests passed'; badge.className = 'modal-status-badge modal-status-pass'; }
                                else if (testsFailed) { badge.textContent = '✗ Tests failed'; badge.className = 'modal-status-badge modal-status-fail'; }
                                else                  { badge.textContent = 'No tests';       badge.className = 'modal-status-badge modal-status-none'; }
                            }

                            modal.classList.add('open');
                            if (typeof lucide !== 'undefined') lucide.createIcons();
                            lastTestResults = html;

                            var runCode = editor.getValue();
                            var runOutput = (response.code_stdout || '') + (response.code_stderr || '');
                            var runTests = (response.test_stdout || '') + (response.test_stderr || '');
                            appendRunItem(runCode, runOutput, runTests);
                        }
                    } else {
                        console.error('Error processing request.');
                    }
                };

                xhr.send(data);
            } else {
                console.error('Task ID is not defined.');
            }
        });

        // ── Form submission (file upload form) ──────────────────────────
        var form = fileInputElement ? fileInputElement.closest('form') : null;
        if (form && fileInputElement) {
            form.addEventListener('submit', function(event) {
                if (fileInputElement.files.length === 0) {
                    event.preventDefault();
                    fileInputElement.click();
                }
            });
        }

    }); // end require callback

    // ── Event delegation for run history items ──────────────────────────
    document.addEventListener('click', function(event) {
        if (event.target.classList.contains('toggle-details-btn')) {
            var details = event.target.nextElementSibling;
            details.style.display = details.style.display === 'none' ? 'block' : 'none';
        }
    });

    // ── Modal controls ───────────────────────────────────────────────────
    var modal = document.getElementById("testResultsModal");
    var span = document.getElementsByClassName("close-button")[0];
    var testOutput = document.getElementById("test-results-output");
    var expandableSection = document.getElementById("expandable-test-results");
    var expandedTestOutput = document.getElementById("expanded-test-results-output");
    var lastTestResults = "";

    var showResultsButton = document.getElementById('show-results');
    if (showResultsButton) {
        showResultsButton.addEventListener('click', function() {
            if (lastTestResults) {
                expandedTestOutput.innerHTML = lastTestResults;
                expandableSection.style.display = expandableSection.style.display === "block" ? "none" : "block";
            }
        });
    }

    document.addEventListener('click', function(event) {
        if (event.target === expandableSection || event.target.closest('.close-results')) {
            expandableSection.style.display = "none";
        }
    });

    var modalCloseBtn = document.getElementById('modal-close-btn');
    if (modalCloseBtn) {
        modalCloseBtn.onclick = function() { modal.classList.remove('open'); };
    }

    window.onclick = function(event) {
        if (modal && event.target == modal) { modal.classList.remove('open'); }
    };

    // ── Admin toggle tests button ─────────────────────────────────────────
    var adminToggleBtn = document.getElementById('admin-toggle-tests-btn');
    if (adminToggleBtn) {
        adminToggleBtn.addEventListener('click', function() {
            var taskId = this.dataset.taskId;
            var csrf   = this.dataset.csrf;
            fetch(`/myapp/tasks/${taskId}/toggle-tests/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrf, 'Content-Type': 'application/json' }
            })
            .then(r => r.json())
            .then(function(data) {
                if (data.show_tests) {
                    adminToggleBtn.innerHTML = '<i data-lucide="eye" style="width:13px;height:13px;vertical-align:middle;margin-right:4px;"></i>Tests visible';
                    adminToggleBtn.classList.remove('pill-hidden');
                    adminToggleBtn.classList.add('pill-visible');
                } else {
                    adminToggleBtn.innerHTML = '<i data-lucide="eye-off" style="width:13px;height:13px;vertical-align:middle;margin-right:4px;"></i>Tests hidden';
                    adminToggleBtn.classList.remove('pill-visible');
                    adminToggleBtn.classList.add('pill-hidden');
                }
                if (typeof lucide !== 'undefined') lucide.createIcons();
            })
            .catch(function() { alert('Failed to toggle test visibility.'); });
        });
    }

    // ── Toggle tests panel ────────────────────────────────────────────────
    var toggleTestsBtn = document.getElementById('toggle-tests-btn');
    var testsPanel = document.getElementById('tests-panel');
    if (toggleTestsBtn && testsPanel) {
        toggleTestsBtn.addEventListener('click', function() {
            var open = testsPanel.style.display === 'block';
            testsPanel.style.display = open ? 'none' : 'block';
            toggleTestsBtn.innerHTML = open
                ? '<i data-lucide="flask-conical" style="width:14px;height:14px;"></i>Show Unit Tests'
                : '<i data-lucide="flask-conical" style="width:14px;height:14px;"></i>Hide Unit Tests';
            if (typeof lucide !== 'undefined') lucide.createIcons();
            if (!open && unitTestsEditor) setTimeout(function() { unitTestsEditor.layout(); }, 50);
        });
    }

    // ── Ratings panel ─────────────────────────────────────────────────────
    var container = document.getElementById('ratings-container');
    if (container) {
        container.style.maxHeight = '0px';
        container.style.display = 'none';
    }

    var toggleBtn = document.getElementById('toggle-ratings');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', function() {
            if (container.style.display === 'none' || container.style.maxHeight === '0px') {
                container.style.display = 'block';
                setTimeout(function() {
                    container.style.maxHeight = '5000px';
                    container.style.padding = '20px';
                }, 10);
            } else {
                container.style.maxHeight = '0px';
                container.style.padding = '0';
                setTimeout(function() {
                    container.style.display = 'none';
                }, 300);
            }
        });
    }

}); // end DOMContentLoaded


function escapeHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}

function appendRunItem(code, output, testsOutput) {
    var existingItems = document.querySelectorAll('.code-run-item');
    var newNum = existingItems.length + 1;
    var now = new Date().toLocaleString();

    var div = document.createElement('div');
    div.className = 'code-run-item';
    div.innerHTML =
        '<button class="toggle-details-btn">Detaily spustenia #' + newNum + '</button>' +
        '<div class="code-run-details" style="display:none;">' +
            '<pre>' + escapeHtml(code) + '</pre>' +
            '<p>Output:</p>' +
            '<pre>' + escapeHtml(output) + '</pre>' +
            '<p>Tests Output:</p>' +
            '<pre>' + escapeHtml(testsOutput) + '</pre>' +
            '<p class="code-run-info">Created At: ' + now + '</p>' +
        '</div>';

    document.getElementById('coderuns-list').appendChild(div);
}
