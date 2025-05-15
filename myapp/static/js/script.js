console.log("Script loaded");
console.log("Direct log without waiting for DOMContentLoaded");

document.addEventListener('DOMContentLoaded', (event) => {
    console.log("DOM fully loaded and parsed");


    var editor = ace.edit("editor");
    editor.setTheme("ace/theme/monokai");
    editor.session.setMode("ace/mode/python");
    console.log("Ace Editor initialized");


    
    

    var readOnlyEditor = ace.edit("readonly-editor");
    readOnlyEditor.setTheme("ace/theme/monokai");
    readOnlyEditor.session.setMode("ace/mode/python");
    readOnlyEditor.setValue(readOnlyCode, -1);
    readOnlyEditor.setReadOnly(true); 

    //runcode

    
    var unitTestsEditor = ace.edit("unit-tests-editor");
    unitTestsEditor.setTheme("ace/theme/monokai");
    unitTestsEditor.session.setMode("ace/mode/python"); 
    unitTestsEditor.setValue(expectedOutput, -1); 
    unitTestsEditor.setReadOnly(true);




    var uploadBtnElement = document.getElementById('uploadBtn');
    var fileInputElement = document.getElementById('fileInput');
    var fileChosenElement = document.getElementById('file-chosen');
    
    var buttons = document.querySelectorAll('.toggle-details-btn');

    buttons.forEach(function(button) {
        button.addEventListener('click', function() {
            var details = button.nextElementSibling;
            details.style.display = details.style.display === 'none' ? 'block' : 'none';
        });
    });

    var modal = document.getElementById("testResultsModal");
    var span = document.getElementsByClassName("close-button")[0];
    var testOutput = document.getElementById("test-results-output");
    var expandableSection = document.getElementById("expandable-test-results");
    var expandedTestOutput = document.getElementById("expanded-test-results-output");
    var lastTestResults = "";
    
    var showResultsButton = document.getElementById('show-results');
showResultsButton.addEventListener('click', function() {
    if (lastTestResults) {
        // Prepneme zobrazenie výsledkov testov v rozbaliteľnej sekcii
        expandedTestOutput.innerHTML = lastTestResults;
        if (expandableSection.style.display === "block") {
            expandableSection.style.display = "none";
        } else {
            expandableSection.style.display = "block";
        }
    } else {
        console.log("Žiadne výsledky testov na zobrazenie.");
    }
});


document.addEventListener('click', function(event) {
    if (event.target === expandableSection || event.target.closest('.close-results')) {
        expandableSection.style.display = "none";
    }
});

    // Keď užívateľ klikne na <span> (x), zatvor modálne okno
    span.onclick = function() {
    modal.style.display = "none";
  }

    // Keď užívateľ klikne mimo modálneho okna, zatvor ho
    window.onclick = function(event) {
        if (event.target == modal) {
        modal.style.display = "none";
        }
    }

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
                var formattedStdout = response.code_stdout.replace(/\\n/g, '<br>');
                var formattedStderr = response.code_stderr.replace(/\\n/g, '<br>');
                var formattedTestStdout = response.test_stdout.replace(/\\n/g, '<br>');
                var formattedTestStderr = response.test_stderr.replace(/\\n/g, '<br>');
                var output = `
            <p><strong>Kód output:</strong> ${formattedStdout}</p>
            <p><strong>Code Stderr:</strong> ${formattedStderr || "No stderr output"}</p>
            <p><strong>Code Return Code:</strong> ${response.code_returncode}</p>
            <p><strong>Test output:</strong> ${formattedTestStdout}</p>
            <p><strong>Test Stderr:</strong> ${formattedTestStderr || "No stderr output"}</p>
            <p><strong>Test Return Code:</strong> ${response.test_returncode}</p>
        `;
                console.log('Výstup:', response.stdout);
                console.log('Chyby:', response.stderr);

                testOutput.innerHTML = output;
                modal.style.display = "block";
                lastTestResults = output;

            } else {
                console.error('Došlo k chybe pri spracovaní vašej požiadavky.');
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


