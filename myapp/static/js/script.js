console.log("Script loaded");
console.log("Direct log without waiting for DOMContentLoaded");

document.addEventListener('DOMContentLoaded', (event) => {
    console.log("DOM fully loaded and parsed");


    var editor = ace.edit("editor");
    editor.setTheme("ace/theme/monokai");
    editor.session.setMode("ace/mode/python");

    if (typeof taskType !== 'undefined') {
        if (taskType === 'test_writing') {
            editor.setValue(
                "import unittest\n\n\n" +
                "class TestStack(unittest.TestCase):\n" +
                "    def test_example(self):\n" +
                "        # Write your test here\n" +
                "        pass\n\n\n" +
                "if __name__ == '__main__':\n" +
                "    unittest.main()\n",
                -1
            );
        }
    }

    console.log("Ace Editor initialized");


    
    

    var readOnlyEditor = ace.edit("readonly-editor");
    readOnlyEditor.setTheme("ace/theme/monokai");
    readOnlyEditor.session.setMode("ace/mode/python");
    readOnlyEditor.setValue(readOnlyCode, -1);
    readOnlyEditor.setReadOnly(true);
    readOnlyEditor.session.setUseWrapMode(true);
    readOnlyEditor.setShowPrintMargin(false);

    //runcode

    
    var unitTestsEditor = null;
    if (document.getElementById("unit-tests-editor")) {
        unitTestsEditor = ace.edit("unit-tests-editor");
        unitTestsEditor.setTheme("ace/theme/monokai");
        unitTestsEditor.session.setMode("ace/mode/python");
        unitTestsEditor.setValue(expectedOutput, -1);
        unitTestsEditor.setReadOnly(true);
    }




    var uploadBtnElement = document.getElementById('uploadBtn');
    var fileInputElement = document.getElementById('fileInput');
    var fileChosenElement = document.getElementById('file-chosen');
    
    // Event delegation — works for both existing and dynamically added run items
    document.addEventListener('click', function(event) {
        if (event.target.classList.contains('toggle-details-btn')) {
            var details = event.target.nextElementSibling;
            details.style.display = details.style.display === 'none' ? 'block' : 'none';
        }
    });

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
                if (expandableSection.style.display === "block") {
                    expandableSection.style.display = "none";
                } else {
                    expandableSection.style.display = "block";
                }
            }
        });
    }


document.addEventListener('click', function(event) {
    if (event.target === expandableSection || event.target.closest('.close-results')) {
        expandableSection.style.display = "none";
    }
});

    if (span) {
        span.onclick = function() {
            modal.style.display = "none";
        };
    }

    window.onclick = function(event) {
        if (modal && event.target == modal) {
            modal.style.display = "none";
        }
    };

    if (uploadBtnElement && fileInputElement) {
        console.log("Upload button and file input found");

        uploadBtnElement.addEventListener('click', () => {
            console.log("Custom 'Choose File' button clicked");
            fileInputElement.click();
        });


        fileInputElement.addEventListener('change', (event) => {
            console.log("File input changed");
            var file = event.target.files[0];
            if (file) {
                console.log("File chosen:", file.name);

                // Display the file name
                fileChosenElement.textContent = file.name;

                // Update the Ace Editor with the contents of the file
                var reader = new FileReader();
                reader.onload = function(e) {
                    editor.setValue(e.target.result);
                    console.log("Ace Editor updated with file content");
                };
                reader.readAsText(file);
            } else {
                fileChosenElement.textContent = 'No file chosen';
                console.log("No file chosen");
            }
        });
    }

        //runcode

var csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

var taskDataElement = document.getElementById('task-data');
var task_id = taskDataElement ? taskDataElement.dataset.taskId : null;

var runButton = document.getElementById('run-code');
runButton.addEventListener('click', function() {
    var code = editor.getSession().getValue(); 
    var data = JSON.stringify({ code: code });
    
    console.log("Run button clicked");
    console.log("Sending the following data to the server: ", data);

    // Kontrola, či máme task_id predtým, ako spravíme request
    if (task_id) {
        var xhr = new XMLHttpRequest();
        xhr.open('POST', `/myapp/run-code/${task_id}/`, true); // Použiť template literal pre vloženie task_id
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.setRequestHeader('X-CSRFToken', csrfToken); // Posielame CSRF token

        xhr.onload = function() {
            if (xhr.status == 200) {
                var response = JSON.parse(xhr.responseText);

                if (response.task_type === 'test_writing') {
                    // ── Test Writing results ──────────────────────────────────
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

                    var twCode = editor.getSession().getValue();
                    appendRunItem(
                        twCode,
                        '[Buggy] ' + response.buggy_output,
                        '[Solution] ' + response.solution_output
                    );

                } else {
                    // ── Normal / Error Detection / Refactoring results ────────
                    var formattedStdout = (response.code_stdout || '').replace(/\n/g, '<br>');
                    var formattedStderr = (response.code_stderr || '').replace(/\n/g, '<br>');
                    var formattedTestStdout = (response.test_stdout || '').replace(/\n/g, '<br>');
                    var formattedTestStderr = (response.test_stderr || '').replace(/\n/g, '<br>');
                    var output = `
                        <p><strong>Code output:</strong><br>${formattedStdout || '(none)'}</p>
                        <p><strong>Code stderr:</strong><br>${formattedStderr || '(none)'}</p>
                        <p><strong>Return code:</strong> ${response.code_returncode}</p>
                        <hr>
                        <p><strong>Test output:</strong><br>${formattedTestStdout || '(none)'}</p>
                        <p><strong>Test stderr:</strong><br>${formattedTestStderr || '(none)'}</p>
                    `;
                    testOutput.innerHTML = output;
                    modal.style.display = "block";
                    lastTestResults = output;

                    var runCode = editor.getSession().getValue();
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
    

    var form = document.querySelector('form');
    form.addEventListener('submit', function(event) {
        console.log("Form submitted");
        if (fileInputElement.files.length === 0) {
            console.log("No file set to the hidden input, submission prevented.");
            event.preventDefault();
            fileInputElement.click();
        } else {
            console.log("File is set, proceeding with the form submission.");
        }
    });
    console.log("Attaching click event listeners to show-tasks-btn elements.");

    
    
});


