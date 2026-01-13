// Main JavaScript for TWINS MEDCARE INSTITUTE Platform

document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss alerts after 5 seconds
    setTimeout(() => {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Form validation enhancements
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
            }
        });
    });

    // File upload preview
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const fileName = this.files[0]?.name;
            if (fileName) {
                const label = this.nextElementSibling?.querySelector('.file-label');
                if (label) {
                    label.textContent = fileName;
                }
            }
        });
    });

    // Auto-update character counters
    const textareas = document.querySelectorAll('textarea[data-max-length]');
    textareas.forEach(textarea => {
        const maxLength = parseInt(textarea.dataset.maxLength);
        const counter = document.createElement('small');
        counter.className = 'form-text text-muted text-end d-block';
        counter.textContent = `0/${maxLength} characters`;
        
        textarea.parentNode.appendChild(counter);
        
        textarea.addEventListener('input', function() {
            const currentLength = this.value.length;
            counter.textContent = `${currentLength}/${maxLength} characters`;
            
            if (currentLength > maxLength) {
                counter.classList.add('text-danger');
                this.classList.add('is-invalid');
            } else {
                counter.classList.remove('text-danger');
                this.classList.remove('is-invalid');
            }
        });
    });

    // Timer for exams
    const examTimer = document.getElementById('exam-timer');
    if (examTimer) {
        let timeLeft = parseInt(examTimer.dataset.time) * 60; // Convert minutes to seconds
        
        const timerInterval = setInterval(() => {
            if (timeLeft <= 0) {
                clearInterval(timerInterval);
                examTimer.innerHTML = '<span class="badge bg-danger">Time\'s up!</span>';
                // Auto-submit form when time's up
                const examForm = document.querySelector('form');
                if (examForm) {
                    examForm.submit();
                }
                return;
            }
            
            const minutes = Math.floor(timeLeft / 60);
            const seconds = timeLeft % 60;
            
            examTimer.innerHTML = `
                <span class="badge bg-warning">
                    <i class="bi bi-clock"></i> 
                    ${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}
                </span>
            `;
            
            timeLeft--;
            
            // Warning when 5 minutes left
            if (timeLeft === 300) {
                showNotification('5 minutes remaining!', 'warning');
            }
        }, 1000);
    }

    // Markdown preview for descriptions
    const markdownPreviewToggles = document.querySelectorAll('.markdown-preview-toggle');
    markdownPreviewToggles.forEach(toggle => {
        toggle.addEventListener('click', function() {
            const textareaId = this.dataset.target;
            const textarea = document.getElementById(textareaId);
            const preview = document.getElementById(`${textareaId}-preview`);
            
            if (textarea && preview) {
                if (this.checked) {
                    // Convert markdown to HTML (simplified)
                    const text = textarea.value;
                    const html = text
                        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                        .replace(/\*(.*?)\*/g, '<em>$1</em>')
                        .replace(/^### (.*$)/gm, '<h3>$1</h3>')
                        .replace(/^## (.*$)/gm, '<h2>$1</h2>')
                        .replace(/^# (.*$)/gm, '<h1>$1</h1>')
                        .replace(/\n/g, '<br>');
                    
                    preview.innerHTML = html;
                    textarea.classList.add('d-none');
                    preview.classList.remove('d-none');
                } else {
                    textarea.classList.remove('d-none');
                    preview.classList.add('d-none');
                }
            }
        });
    });
});

// Notification function
function showNotification(message, type = 'info') {
    const alertClass = {
        'success': 'alert-success',
        'error': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info'
    }[type] || 'alert-info';
    
    const notification = document.createElement('div');
    notification.className = `alert ${alertClass} alert-dismissible fade show position-fixed`;
    notification.style.cssText = `
        top: 20px;
        right: 20px;
        z-index: 1050;
        min-width: 300px;
    `;
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

// Download file with progress
function downloadFileWithProgress(url, filename) {
    showNotification('Starting download...', 'info');
    
    const xhr = new XMLHttpRequest();
    xhr.open('GET', url, true);
    xhr.responseType = 'blob';
    
    xhr.onprogress = function(event) {
        if (event.lengthComputable) {
            const percentComplete = (event.loaded / event.total) * 100;
            showNotification(`Downloading... ${percentComplete.toFixed(1)}%`, 'info');
        }
    };
    
    xhr.onload = function() {
        if (this.status === 200) {
            const blob = this.response;
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            a.remove();
            showNotification('Download completed!', 'success');
        }
    };
    
    xhr.send();
}

// Auto-save exam answers
function setupAutoSave(formId, saveInterval = 30000) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    const saveData = () => {
        const formData = new FormData(form);
        const data = Object.fromEntries(formData);
        
        localStorage.setItem(`exam_${formId}_autosave`, JSON.stringify({
            data: data,
            timestamp: new Date().toISOString()
        }));
        
        showNotification('Answers auto-saved', 'info');
    };
    
    // Save on interval
    setInterval(saveData, saveInterval);
    
    // Save on visibility change
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            saveData();
        }
    });
    
    // Check for saved data on load
    const savedData = localStorage.getItem(`exam_${formId}_autosave`);
    if (savedData) {
        try {
            const { data, timestamp } = JSON.parse(savedData);
            Object.keys(data).forEach(key => {
                const input = form.querySelector(`[name="${key}"]`);
                if (input) {
                    if (input.type === 'radio' || input.type === 'checkbox') {
                        if (input.value === data[key]) {
                            input.checked = true;
                        }
                    } else {
                        input.value = data[key];
                    }
                }
            });
            
            const time = new Date(timestamp).toLocaleTimeString();
            showNotification(`Loaded auto-saved answers from ${time}`, 'warning');
        } catch (e) {
            console.error('Failed to load auto-saved data:', e);
        }
    }
}
