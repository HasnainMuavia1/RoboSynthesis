// Signup Page JavaScript with 3D effects and animations

document.addEventListener('DOMContentLoaded', function() {
    // Initialize AOS animations if available
    if (typeof AOS !== 'undefined') {
        AOS.init({
            duration: 1000,
            once: false,
            mirror: true,
            offset: 50
        });
    }

    // 3D Tilt effect for the signup wrapper
    const signupWrapper = document.querySelector('.signup-wrapper');
    const robotImage = document.querySelector('.signup-robot');
    const formContainer = document.querySelector('.signup-form-container');
    const titleLayers = document.querySelectorAll('.title-layer');
    
    // Create particles dynamically
    createParticles();
    
    // 3D mouse movement effect
    document.addEventListener('mousemove', function(e) {
        if (!signupWrapper) return;
        
        const xAxis = (window.innerWidth / 2 - e.pageX) / 35;
        const yAxis = (window.innerHeight / 2 - e.pageY) / 35;
        
        // Apply subtle 3D rotation to the card
        signupWrapper.style.transform = `perspective(1000px) rotateY(${xAxis}deg) rotateX(${-yAxis}deg)`;
        
        // Move robot image for parallax effect
        if (robotImage) {
            robotImage.style.transform = `translateZ(50px) translateX(${-xAxis * 2}px) translateY(${-yAxis * 2}px)`;
        }
        
        // Move title layers for 3D text effect
        if (titleLayers) {
            titleLayers.forEach((layer, index) => {
                const depth = (index + 1) * 5;
                layer.style.transform = `translateZ(${depth}px) translateX(${-xAxis * 0.5}px) translateY(${-yAxis * 0.5}px)`;
            });
        }
        
        // Animate particles based on mouse position
        animateParticles(e.pageX, e.pageY);
    });
    
    // Reset transforms when mouse leaves
    document.addEventListener('mouseleave', function() {
        if (signupWrapper) {
            signupWrapper.style.transform = `perspective(1000px) rotateY(0deg) rotateX(0deg)`;
        }
        
        if (robotImage) {
            robotImage.style.transform = 'translateZ(50px)';
        }
        
        if (titleLayers) {
            titleLayers.forEach((layer, index) => {
                const depth = (index + 1) * 5;
                layer.style.transform = `translateZ(${depth}px)`;
            });
        }
    });
    
    // Button hover effects
    const signupBtn = document.querySelector('.signup-btn');
    if (signupBtn) {
        signupBtn.addEventListener('mousemove', function(e) {
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const btnGlow = this.querySelector('.btn-glow');
            if (btnGlow) {
                btnGlow.style.width = '150px';
                btnGlow.style.height = '150px';
                btnGlow.style.left = `${x}px`;
                btnGlow.style.top = `${y}px`;
            }
        });
        
        signupBtn.addEventListener('mouseleave', function() {
            const btnGlow = this.querySelector('.btn-glow');
            if (btnGlow) {
                btnGlow.style.width = '0';
                btnGlow.style.height = '0';
            }
        });
    }
    
    // Form input focus effects
    const formInputs = document.querySelectorAll('.signup-form input');
    formInputs.forEach(input => {
        input.addEventListener('focus', function() {
            const iconWrapper = this.closest('.form-group').querySelector('.input-icon-wrapper');
            if (iconWrapper) {
                iconWrapper.style.backgroundColor = 'rgba(138, 43, 226, 0.4)';
                iconWrapper.style.boxShadow = '0 0 10px rgba(138, 43, 226, 0.5)';
            }
        });
        
        input.addEventListener('blur', function() {
            const iconWrapper = this.closest('.form-group').querySelector('.input-icon-wrapper');
            if (iconWrapper) {
                iconWrapper.style.backgroundColor = 'rgba(138, 43, 226, 0.2)';
                iconWrapper.style.boxShadow = 'none';
            }
        });
    });
    
    // Function to create particles dynamically
    function createParticles() {
        const particlesContainer = document.querySelector('.particles-container');
        if (!particlesContainer) return;
        
        // Clear existing particles
        particlesContainer.innerHTML = '';
        
        // Create new particles
        for (let i = 0; i < 20; i++) {
            const particle = document.createElement('div');
            particle.className = `particle particle-${i}`;
            
            // Random positions
            particle.style.top = `${Math.random() * 100}%`;
            particle.style.left = `${Math.random() * 100}%`;
            
            // Random sizes
            const size = Math.random() * 5 + 2;
            particle.style.width = `${size}px`;
            particle.style.height = `${size}px`;
            
            // Random colors between purple and cyan
            const hue = Math.random() * 60 + 240; // 240-300 range (blue to purple)
            particle.style.backgroundColor = `hsla(${hue}, 100%, 70%, ${Math.random() * 0.5 + 0.3})`;
            particle.style.boxShadow = `0 0 ${size * 2}px hsla(${hue}, 100%, 70%, 0.8)`;
            
            // Random animation durations and delays
            const duration = Math.random() * 20 + 10;
            const delay = Math.random() * -30;
            particle.style.animation = `particle-float ${duration}s ${delay}s infinite ease-in-out`;
            
            particlesContainer.appendChild(particle);
        }
    }
    
    // Function to animate particles based on mouse position
    function animateParticles(mouseX, mouseY) {
        const particles = document.querySelectorAll('.particle');
        const centerX = window.innerWidth / 2;
        const centerY = window.innerHeight / 2;
        
        const deltaX = (mouseX - centerX) / centerX;
        const deltaY = (mouseY - centerY) / centerY;
        
        particles.forEach((particle, index) => {
            const speed = (index % 5 + 1) * 0.4;
            const currentX = parseFloat(particle.style.left);
            const currentY = parseFloat(particle.style.top);
            
            // Add subtle movement based on mouse position
            particle.style.transform = `translate(${deltaX * speed * 20}px, ${deltaY * speed * 20}px)`;
        });
    }
    
    // Form validation enhancements
    const form = document.querySelector('.signup-form');
    if (form) {
        form.addEventListener('submit', function(e) {
            const usernameInput = document.getElementById('id_username');
            const password1Input = document.getElementById('id_password1');
            const password2Input = document.getElementById('id_password2');
            
            let isValid = true;
            
            // Clear previous error messages
            document.querySelectorAll('.error-message').forEach(el => {
                el.innerHTML = '';
            });
            
            // Simple client-side validation
            if (usernameInput && usernameInput.value.trim() === '') {
                const errorDiv = usernameInput.closest('.input-field-wrapper').querySelector('.error-message') || 
                                 createErrorElement(usernameInput.closest('.input-field-wrapper'));
                errorDiv.textContent = 'Username is required';
                isValid = false;
            }
            
            if (password1Input && password1Input.value.trim() === '') {
                const errorDiv = password1Input.closest('.input-field-wrapper').querySelector('.error-message') || 
                                 createErrorElement(password1Input.closest('.input-field-wrapper'));
                errorDiv.textContent = 'Password is required';
                isValid = false;
            }
            
            if (password1Input && password2Input && password1Input.value !== password2Input.value) {
                const errorDiv = password2Input.closest('.input-field-wrapper').querySelector('.error-message') || 
                                 createErrorElement(password2Input.closest('.input-field-wrapper'));
                errorDiv.textContent = 'Passwords do not match';
                isValid = false;
            }
            
            // Allow form submission if valid (server will handle full validation)
            if (!isValid) {
                e.preventDefault();
                shakeForm();
            }
        });
    }
    
    // Helper function to create error message element
    function createErrorElement(parent) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        parent.appendChild(errorDiv);
        return errorDiv;
    }
    
    // Add shake animation to form on validation error
    function shakeForm() {
        const form = document.querySelector('.signup-form');
        if (!form) return;
        
        form.classList.add('shake-animation');
        setTimeout(() => {
            form.classList.remove('shake-animation');
        }, 500);
    }
    
    // Add shake animation CSS
    const style = document.createElement('style');
    style.textContent = `
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
            20%, 40%, 60%, 80% { transform: translateX(5px); }
        }
        .shake-animation {
            animation: shake 0.5s cubic-bezier(.36,.07,.19,.97) both;
        }
    `;
    document.head.appendChild(style);
});
