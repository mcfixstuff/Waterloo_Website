/**
 * User Management Application - Main JavaScript
 * Provides common functionality for the user management application
 */

// Wait until the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initFormValidation();
    initUIEnhancements();
    initAjaxHandlers();
    
    console.log('User Management JS initialized');
});

/**
 * Form Validation Functions
 */
function initFormValidation() {
    // Get all forms that need validation
    const forms = document.querySelectorAll('.needs-validation');
    
    // Add validation event listeners to each form
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!validateForm(form)) {
                event.preventDefault();
                event.stopPropagation();
            }
        });
        
        // Add input event listeners for real-time validation
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(function(input) {
            input.addEventListener('input', function() {
                validateInput(input);
            });
            
            input.addEventListener('blur', function() {
                validateInput(input);
            });
        });
    });
}

// Validate an entire form
function validateForm(form) {
    let isValid = true;
    
    // Validate each input in the form
    const inputs = form.querySelectorAll('input, select, textarea');
    inputs.forEach(function(input) {
        if (!validateInput(input)) {
            isValid = false;
        }
    });
    
    // Special validation for password confirmation
    const password = form.querySelector('input[name="password"]');
    const confirmPassword = form.querySelector('input[name="confirm_password"]');
    
    if (password && confirmPassword) {
        if (password.value !== confirmPassword.value) {
            setInvalid(confirmPassword, 'Passwords do not match');
            isValid = false;
        }
    }
    
    return isValid;
}

// Validate a single input
function validateInput(input) {
    // Reset validation state
    input.classList.remove('is-invalid');
    input.classList.remove('is-valid');
    
    // Skip disabled inputs
    if (input.disabled) return true;
    
    let isValid = true;
    const value = input.value.trim();
    
    // Required field validation
    if (input.hasAttribute('required') && value === '') {
        setInvalid(input, 'This field is required');
        isValid = false;
    }
    
    // Email validation
    if (input.type === 'email' && value !== '') {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            setInvalid(input, 'Please enter a valid email address');
            isValid = false;
        }
    }
    
    // Password validation
    if (input.type === 'password' && input.dataset.validateStrength === 'true' && value !== '') {
        if (value.length < 8) {
            setInvalid(input, 'Password must be at least 8 characters long');
            isValid = false;
        } else if (!/[A-Z]/.test(value) || !/[a-z]/.test(value) || !/[0-9]/.test(value)) {
            setInvalid(input, 'Password must include uppercase, lowercase, and numbers');
            isValid = false;
        }
    }
    
    // If valid, add valid class
    if (isValid && value !== '') {
        input.classList.add('is-valid');
    }
    
    return isValid;
}

// Set input as invalid with feedback message
function setInvalid(input, message) {
    input.classList.add('is-invalid');
    
    // Find or create feedback element
    let feedback = input.nextElementSibling;
    if (!feedback || !feedback.classList.contains('invalid-feedback')) {
        feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        input.parentNode.insertBefore(feedback, input.nextSibling);
    }
    
    feedback.textContent = message;
}

/**
 * UI Enhancement Functions
 */
function initUIEnhancements() {
    // Password visibility toggle
    const passwordToggles = document.querySelectorAll('.password-toggle');
    
    passwordToggles.forEach(function(toggle) {
        toggle.addEventListener('click', function() {
            const passwordField = document.querySelector(toggle.dataset.target);
            
            if (passwordField) {
                if (passwordField.type === 'password') {
                    passwordField.type = 'text';
                    toggle.innerHTML = '<i class="fa fa-eye-slash"></i>';
                } else {
                    passwordField.type = 'password';
                    toggle.innerHTML = '<i class="fa fa-eye"></i>';
                }
            }
        });
    });
    
    // Initialize tooltips if using Bootstrap
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltips.forEach(tooltip => new bootstrap.Tooltip(tooltip));
    }
    
    // Add active class to current page in navigation
    highlightCurrentPage();
}

// Highlight current page in navigation
function highlightCurrentPage() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(function(link) {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
}

/**
 * AJAX Request Handlers
 */
function initAjaxHandlers() {
    // User deletion confirmation
    const deleteButtons = document.querySelectorAll('.delete-user');
    
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            
            if (confirm('Are you sure you want to delete this user?')) {
                const userId = this.dataset.userId;
                deleteUser(userId);
            }
        });
    });
}

// Delete user via AJAX
function deleteUser(userId) {
    fetch(`/api/users/${userId}`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken() // For Flask CSRF protection
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        // Remove user from DOM or reload page
        const userElement = document.querySelector(`.user-item[data-user-id="${userId}"]`);
        if (userElement) {
            userElement.remove();
            showNotification('User successfully deleted', 'success');
        } else {
            window.location.reload();
        }
    })
    .catch(error => {
        console.error('Error deleting user:', error);
        showNotification('Error deleting user', 'error');
    });
}

// Get CSRF token from meta tag
function getCsrfToken() {
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    return metaTag ? metaTag.getAttribute('content') : '';
}

// Display notification/toast message
function showNotification(message, type = 'info') {
    // Check if we have a notification container
    let container = document.getElementById('notification-container');
    
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        container.style.position = 'fixed';
        container.style.top = '20px';
        container.style.right = '20px';
        container.style.zIndex = '1050';
        document.body.appendChild(container);
    }
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show`;
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add to container
    container.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 150);
    }, 7070);
}

