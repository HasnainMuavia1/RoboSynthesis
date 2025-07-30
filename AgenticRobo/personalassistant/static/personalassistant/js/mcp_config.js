/**
 * MCP Configuration JavaScript
 * Handles the interaction with Google Apps and GitHub integration
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize modals
    const googleModal = new bootstrap.Modal(document.getElementById('googleModal'), {
        backdrop: 'static',
        keyboard: true
    });
    
    const githubModal = new bootstrap.Modal(document.getElementById('githubModal'), {
        backdrop: 'static',
        keyboard: true
    });
    
    // Connect button click handlers
    const connectButtons = document.querySelectorAll('.connect-btn');
    connectButtons.forEach(button => {
        button.addEventListener('click', function() {
            const service = this.getAttribute('data-service');
            if (!service) return;
            
            const card = this.closest('.mcp-card');
            if (card) {
                const statusBadge = card.querySelector('.status-badge');
                
                // If already connected, disconnect
                if (statusBadge && statusBadge.classList.contains('status-connected')) {
                    if (confirm('Are you sure you want to disconnect from ' + service + '?')) {
                        disconnectService(service, card);
                    }
                } 
                // If disconnected, show the appropriate modal
                else if (statusBadge) {
                    if (service === 'google') {
                        googleModal.show();
                        // Focus on file input when modal is shown
                        document.getElementById('googleModal').addEventListener('shown.bs.modal', function () {
                            document.getElementById('googleConfigFile').focus();
                        }, { once: true });
                    } else if (service === 'github') {
                        githubModal.show();
                        // Focus on token input when modal is shown
                        document.getElementById('githubModal').addEventListener('shown.bs.modal', function () {
                            document.getElementById('githubToken').focus();
                        }, { once: true });
                    }
                }
            }
        });
    });
    
    // Google form submission
    document.getElementById('submitGoogleConnection').addEventListener('click', function() {
        const form = document.getElementById('googleConnectForm');
        const fileInput = document.getElementById('googleConfigFile');
        
        if (!fileInput.files[0]) {
            alert('Please upload a Google API credentials file.');
            return;
        }
        
        // Show loading state
        const submitBtn = this;
        const originalBtnText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Connecting...';
        submitBtn.disabled = true;
        
        // Create FormData and submit
        const formData = new FormData(form);
        
        fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.indexOf('application/json') !== -1) {
                    return response.json().then(data => {
                        throw new Error(data.error || 'Server error');
                    });
                } else {
                    throw new Error('Network response was not ok');
                }
            }
            return response.json();
        })
        .then(data => {
            // Hide form and show success message
            form.querySelector('.mb-3').style.display = 'none';
            form.querySelector('.alert').style.display = 'none';
            document.getElementById('googleUploadSuccess').style.display = 'flex';
            
            // Update card status
            updateCardStatus('google', true);
            
            // Reset button and close modal after delay
            setTimeout(() => {
                googleModal.hide();
                form.reset();
                form.querySelector('.mb-3').style.display = 'block';
                form.querySelector('.alert').style.display = 'block';
                document.getElementById('googleUploadSuccess').style.display = 'none';
                submitBtn.innerHTML = originalBtnText;
                submitBtn.disabled = false;
            }, 2000);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to connect: ' + error.message);
            
            // Reset button
            submitBtn.innerHTML = originalBtnText;
            submitBtn.disabled = false;
        });
    });
    
    // GitHub form submission
    document.getElementById('submitGithubConnection').addEventListener('click', function() {
        const form = document.getElementById('githubConnectForm');
        const tokenInput = document.getElementById('githubToken');
        
        if (!tokenInput.value) {
            alert('Please enter your GitHub Personal Access Token.');
            return;
        }
        
        // Show loading state
        const submitBtn = this;
        const originalBtnText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Connecting...';
        submitBtn.disabled = true;
        
        // Create FormData and submit
        const formData = new FormData(form);
        
        fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.indexOf('application/json') !== -1) {
                    return response.json().then(data => {
                        throw new Error(data.error || 'Server error');
                    });
                } else {
                    throw new Error('Network response was not ok');
                }
            }
            return response.json();
        })
        .then(data => {
            // Hide form and show success message
            form.querySelector('.mb-3').style.display = 'none';
            form.querySelector('.form-check').style.display = 'none';
            form.querySelector('.alert').style.display = 'none';
            document.getElementById('githubSuccess').style.display = 'flex';
            
            // Update card status
            updateCardStatus('github', true);
            
            // Reset button and close modal after delay
            setTimeout(() => {
                githubModal.hide();
                form.reset();
                form.querySelector('.mb-3').style.display = 'block';
                form.querySelector('.form-check').style.display = 'block';
                form.querySelector('.alert').style.display = 'block';
                document.getElementById('githubSuccess').style.display = 'none';
                submitBtn.innerHTML = originalBtnText;
                submitBtn.disabled = false;
            }, 2000);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to connect: ' + error.message);
            
            // Reset button
            submitBtn.innerHTML = originalBtnText;
            submitBtn.disabled = false;
        });
    });
    
    // Show/hide GitHub token
    document.getElementById('showToken').addEventListener('change', function() {
        const tokenInput = document.getElementById('githubToken');
        tokenInput.type = this.checked ? 'text' : 'password';
    });
    
    // Function to update card status
    function updateCardStatus(service, isConnected) {
        const card = document.querySelector(`.mcp-card[data-service="${service}"]`);
        if (!card) return;
        
        const statusBadge = card.querySelector('.status-badge');
        const connectBtn = card.querySelector('.connect-btn');
        
        if (isConnected) {
            statusBadge.classList.remove('status-disconnected');
            statusBadge.classList.add('status-connected');
            statusBadge.textContent = 'Connected';
            connectBtn.innerHTML = '<i class="fas fa-unlink me-2"></i> Disconnect';
        } else {
            statusBadge.classList.remove('status-connected');
            statusBadge.classList.add('status-disconnected');
            statusBadge.textContent = 'Disconnected';
            connectBtn.innerHTML = '<i class="fas fa-plug me-2"></i> Connect';
        }
    }
    
    // Function to disconnect a service
    function disconnectService(service, card) {
        // Get CSRF token from the page
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        fetch(`/personalassistant/disconnect_mcp/?service=${service}`, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken
            },
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to disconnect');
            }
            return response.json();
        })
        .then(data => {
            updateCardStatus(service, false);
            alert(`Successfully disconnected from ${service}.`);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to disconnect: ' + error.message);
        });
    }
    
    // Check connection status on page load
    fetch('/personalassistant/check_mcp_status/', {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.google_connected) {
            updateCardStatus('google', true);
        }
        if (data.github_connected) {
            updateCardStatus('github', true);
        }
    })
    .catch(error => console.error('Error checking connection status:', error));
});
