document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('upload-form');
    const dropArea = document.getElementById('drop-area');
    const fileInput = document.getElementById('folder-input');
    const processingMessage = document.getElementById('processing-message');
    const successModal = document.getElementById('success-modal');
    const successMessage = document.getElementById('success-message');
    const closeBtn = document.querySelector('.close-btn');
    const downloadContainer = document.getElementById('download-container');
    const downloadLink = document.getElementById('download-link');
    const homeButton = document.getElementById('home-button');

    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    // Highlight drop area when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false);
    });

    function highlight(e) {
        dropArea.classList.add('highlight');
    }

    function unhighlight(e) {
        dropArea.classList.remove('highlight');
    }

    // Handle dropped files
    dropArea.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    }

    function handleFiles(files) {
        if (files.length > 0) {
            fileInput.files = files;
            updateDropAreaText(files);
        }
    }

    // Handle selected files via the file input
    fileInput.addEventListener('change', function(e) {
        handleFiles(this.files);
    });

    function updateDropAreaText(files) {
        const dragDropText = dropArea.querySelector('p:first-child');
        const orText = dropArea.querySelector('p:nth-child(2)');
        const label = dropArea.querySelector('label');

        if (files.length > 0) {
            const folderName = files[0].webkitRelativePath ? files[0].webkitRelativePath.split('/')[0] : 'Selected folder';
            dragDropText.textContent = `Selected folder: ${folderName}`;
            orText.style.display = 'none';
            label.style.display = 'none';
        } else {
            dragDropText.textContent = 'Drag and drop your folder here';
            orText.style.display = 'block';
            orText.textContent = 'or';
            label.style.display = 'inline-block';
        }
    }

    // Form submission
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        if (fileInput.files.length === 0) {
            alert('Please select a folder to upload.');
            return;
        }

        processingMessage.classList.remove('hidden');

        const formData = new FormData(form);

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            processingMessage.classList.add('hidden');
            if (data.success) {
                successMessage.textContent = data.message;
                downloadLink.href = data.download_url;
                downloadContainer.classList.remove('hidden');
                successModal.style.display = 'block';
            } else {
                alert('Error: ' + data.message);
            }
        })
        .catch(error => {
            processingMessage.classList.add('hidden');
            alert('An error occurred while uploading the folder.');
        });
    });

    // Close modal
    closeBtn.onclick = function() {
        successModal.style.display = 'none';
    }

    window.onclick = function(event) {
        if (event.target == successModal) {
            successModal.style.display = 'none';
        }
    }
});