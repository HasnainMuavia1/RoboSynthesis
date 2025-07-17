// Main JavaScript for PersonalAssistant App

document.addEventListener('DOMContentLoaded', function() {
    // Initialize AOS animations
    AOS.init({
        duration: 1000,
        once: false,
        mirror: true,
        offset: 50
    });
    
    // Navbar scroll effect with enhanced animation
    const navbar = document.querySelector('.navbar');
    window.addEventListener('scroll', function() {
        if (window.scrollY > 50) {
            navbar.classList.add('navbar-scrolled');
            navbar.style.background = 'rgba(18, 18, 18, 0.95)';
            navbar.style.boxShadow = '0 5px 20px rgba(0, 0, 0, 0.3)';
        } else {
            navbar.classList.remove('navbar-scrolled');
            navbar.style.background = 'rgba(18, 18, 18, 0.7)';
            navbar.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.1)';
        }
    });

    // Animated Logo Text
    const logoTextElements = document.querySelectorAll('.logo-text span');
    logoTextElements.forEach((span, index) => {
        span.style.setProperty('--i', index);
    });
    
    // Get all hero section elements
    const heroSection = document.querySelector('.hero-section');
    const heroContent = document.querySelector('.hero-content');
    const heroImage = document.querySelector('.robot-container');
    const heroImageFallback = document.querySelector('.hero-section .img-fluid');
    const heroTitle = document.querySelector('.hero-title');
    const heroTextContainer = document.querySelector('.hero-text-container');
    
    // 3D Parallax Effect for Hero Section
    if (heroSection) {
        heroSection.addEventListener('mousemove', (e) => {
            const xAxis = (window.innerWidth / 2 - e.pageX) / 25;
            const yAxis = (window.innerHeight / 2 - e.pageY) / 25;
            const mouseX = e.clientX / window.innerWidth;
            const mouseY = e.clientY / window.innerHeight;
            
            // Apply 3D rotation to hero content
            if (heroTextContainer) {
                heroTextContainer.style.transform = `rotateY(${xAxis * 0.5}deg) rotateX(${yAxis * 0.5}deg)`;
            } else if (heroContent) {
                heroContent.style.transform = `translateX(${-mouseX * 20 + 10}px) translateY(${-mouseY * 10 + 5}px)`;
                heroContent.style.transition = 'transform 0.2s ease-out';
            }
            
            // Move robot image in opposite direction for parallax
            const activeHeroImage = heroImage || heroImageFallback;
            if (activeHeroImage) {
                if (heroImage) {
                    heroImage.style.transform = `translateX(${-xAxis * 2}px) translateY(${-yAxis * 2}px) rotateY(${-xAxis * 0.5}deg) rotateX(${-yAxis * 0.5}deg)`;
                } else {
                    activeHeroImage.style.transform = `translateX(${mouseX * 30 - 15}px) translateY(${mouseY * 20 - 10}px) rotateY(${mouseX * 8 - 4}deg) scale(1.05)`;
                    activeHeroImage.style.transition = 'transform 0.2s ease-out';
                }
            }
            
            // Move hero title spans for depth effect
            if (heroTitle) {
                const spans = heroTitle.querySelectorAll('span');
                spans.forEach((span, index) => {
                    const depth = (index + 1) * 5;
                    span.style.transform = `translateZ(${depth}px) translateX(${-xAxis * 0.2 * depth}px) translateY(${-yAxis * 0.2 * depth}px)`;
                });
            }
            
            // Animate particles based on mouse position
            const particles = document.querySelectorAll('.particle');
            particles.forEach((particle, index) => {
                const speed = (index + 1) * 0.2;
                particle.style.transform = `translate(${-xAxis * speed}px, ${-yAxis * speed}px)`;
            });
        });
        
        // Reset on mouse leave
        heroSection.addEventListener('mouseleave', () => {
            if (heroTextContainer) {
                heroTextContainer.style.transform = 'rotateY(0deg) rotateX(0deg)';
            }
            
            if (heroImage) {
                heroImage.style.transform = 'translateX(0) translateY(0) rotateY(0deg) rotateX(0deg)';
            } else if (heroImageFallback) {
                heroImageFallback.style.transform = 'translateX(0) translateY(0) rotateY(0deg) scale(1)';
            }
            
            if (heroContent && !heroTextContainer) {
                heroContent.style.transform = 'translateX(0) translateY(0)';
            }
            
            if (heroTitle) {
                const spans = heroTitle.querySelectorAll('span');
                spans.forEach((span, index) => {
                    const depth = (index + 1) * 10;
                    span.style.transform = `translateZ(${depth}px)`;
                });
            }
        });
    }
    
    // Smooth scrolling for anchor links with enhanced easing
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                const headerOffset = 80;
                const elementPosition = targetElement.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - headerOffset;
                
                window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth'
                });
                
                // Update URL without page jump
                history.pushState(null, null, targetId);
            }
        });
    });

    // Enhanced Service Card 3D Tilt Effect
    const serviceCards = document.querySelectorAll('.service-card');
    serviceCards.forEach(card => {
        card.addEventListener('mousemove', function(e) {
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            const angleX = (y - centerY) / 10;
            const angleY = (centerX - x) / 10;
            
            this.style.transform = `perspective(1000px) rotateX(${angleX}deg) rotateY(${angleY}deg) scale3d(1.05, 1.05, 1.05)`;
            
            // Dynamic shadow based on tilt
            this.style.boxShadow = `
                ${-angleY}px ${angleX}px 20px rgba(0, 0, 0, 0.2),
                0 10px 20px rgba(138, 43, 226, 0.2)
            `;
            
            // Move icon for parallax effect
            const icon = this.querySelector('.service-icon');
            if (icon) {
                icon.style.transform = `translateX(${angleY * 2}px) translateY(${-angleX * 2}px)`;
            }
            
            // Adjust glow position
            const glowElement = this.querySelector('.card-glow');
            if (glowElement) {
                glowElement.style.background = `radial-gradient(circle at ${x}px ${y}px, rgba(138, 43, 226, 0.8), transparent 50%)`;
            }
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) scale3d(1, 1, 1)';
            this.style.boxShadow = '0 10px 20px rgba(0, 0, 0, 0.1), 0 6px 6px rgba(138, 43, 226, 0.1)';
            
            const icon = this.querySelector('.service-icon');
            if (icon) {
                icon.style.transform = 'translateX(0) translateY(0)';
            }
            
            const glowElement = this.querySelector('.card-glow');
            if (glowElement) {
                glowElement.style.background = 'radial-gradient(circle at center, rgba(138, 43, 226, 0.5), transparent 50%)';
            }
        });
    });
    
    // Button Glow Effect
    const buttons = document.querySelectorAll('.hero-btn, .btn');
    buttons.forEach(button => {
        button.addEventListener('mousemove', function(e) {
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const buttonGlow = this.querySelector('span:nth-child(2)');
            if (buttonGlow) {
                buttonGlow.style.transform = 'scale(2)';
                buttonGlow.style.left = `${x - rect.width / 2}px`;
                buttonGlow.style.top = `${y - rect.height / 2}px`;
            }
        });
        
        button.addEventListener('mouseleave', function() {
            const buttonGlow = this.querySelector('span:nth-child(2)');
            if (buttonGlow) {
                buttonGlow.style.transform = 'scale(0)';
            }
        });
    });
    
    // Navbar hover effects
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('mouseenter', function() {
            const hoverEffect = this.querySelector('.nav-hover-effect');
            if (hoverEffect) {
                hoverEffect.style.width = '80%';
            }
        });
        
        link.addEventListener('mouseleave', function() {
            const hoverEffect = this.querySelector('.nav-hover-effect');
            if (hoverEffect) {
                hoverEffect.style.width = '0';
            }
        });
    });
    
    // Footer Card Hover Effects
    const footerCards = document.querySelectorAll('.footer-card');
    footerCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
            this.style.boxShadow = '0 15px 30px rgba(0, 0, 0, 0.3)';
            this.style.borderColor = 'rgba(138, 43, 226, 0.5)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '0 10px 30px rgba(0, 0, 0, 0.2)';
            this.style.borderColor = 'rgba(138, 43, 226, 0.2)';
        });
    });
    
    // Social Icon Hover Effects
    const socialIcons = document.querySelectorAll('.social-icon');
    socialIcons.forEach(icon => {
        icon.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px) scale(1.1)';
            this.style.backgroundColor = 'rgba(138, 43, 226, 0.4)';
            this.style.boxShadow = '0 5px 15px rgba(138, 43, 226, 0.5)';
        });
        
        icon.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
            this.style.backgroundColor = 'rgba(138, 43, 226, 0.2)';
            this.style.boxShadow = 'none';
        });
    });
    
    // Animation for service cards on scroll with 3D effects
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate__animated', 'animate__fadeInUp');
                setTimeout(() => {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0) rotateX(5deg) rotateY(5deg)';
                }, 300);
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1
    });
    
    serviceCards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(50px)';
        observer.observe(card);
        
        // 3D tilt effect for service cards
        card.addEventListener('mousemove', function(e) {
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            const deltaX = (x - centerX) / centerX * 15;
            const deltaY = (y - centerY) / centerY * 15;
            
            this.style.transform = `translateY(-10px) rotateX(${-deltaY}deg) rotateY(${deltaX}deg)`;
            
            // Dynamic shadow based on position
            const shadowX = deltaX * 2;
            const shadowY = deltaY * 2;
            this.style.boxShadow = `${shadowX}px ${shadowY}px 30px rgba(0,0,0,0.4), 0 0 20px rgba(138, 43, 226, 0.6)`;
            
            // Move inner elements for depth effect
            const icon = this.querySelector('.service-icon');
            const title = this.querySelector('.service-title');
            
            if (icon) {
                icon.style.transform = `translateZ(30px) translateX(${deltaX * 0.5}px) translateY(${deltaY * 0.5}px)`;
            }
            
            if (title) {
                title.style.transform = `translateZ(20px) translateX(${deltaX * 0.3}px) translateY(${deltaY * 0.3}px)`;
            }
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(-10px) rotateX(5deg) rotateY(5deg)';
            this.style.boxShadow = '0 20px 40px rgba(0, 0, 0, 0.4), 0 0 15px rgba(138, 43, 226, 0.6)';
            
            const icon = this.querySelector('.service-icon');
            const title = this.querySelector('.service-title');
            
            if (icon) {
                icon.style.transform = 'translateZ(20px)';
            }
            
            if (title) {
                title.style.transform = 'translateZ(10px)';
            }
        });
    });

    // This section has been merged with the main hero section animation above
    
    // Typing animation for hero title
    if (heroTitle) {
        // Store the original text content
        const originalText = heroTitle.textContent;
        
        // Only run the typing animation if we haven't already applied 3D effects
        // (which would mean there are span elements inside)
        if (!heroTitle.querySelector('span')) {
            heroTitle.textContent = '';
            
            let i = 0;
            const typeWriter = () => {
                if (i < originalText.length) {
                    heroTitle.textContent += originalText.charAt(i);
                    i++;
                    setTimeout(typeWriter, 100);
                }
            };
            
            // Enable typing animation
            typeWriter();
        }
        
        // Add glow effect to buttons
        const buttons = document.querySelectorAll('.btn');
        buttons.forEach(btn => {
            btn.addEventListener('mousemove', function(e) {
                const rect = this.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                this.style.setProperty('--x', `${x}px`);
                this.style.setProperty('--y', `${y}px`);
                this.style.background = `radial-gradient(circle at var(--x) var(--y), rgba(138, 43, 226, 0.8), var(--accent-color) 50%)`;
            });
            
            btn.addEventListener('mouseleave', function() {
                this.style.background = '';
            });
        });
        
        // Add 3D depth to page sections
        const sections = document.querySelectorAll('section');
        sections.forEach(section => {
            section.style.transformStyle = 'preserve-3d';
            section.style.perspective = '1000px';
        });
    }

    // Parallax effect for blobs
    document.addEventListener('mousemove', function(e) {
        const blob1 = document.querySelector('.blob-1');
        const blob2 = document.querySelector('.blob-2');
        
        if (blob1 && blob2) {
            const x = e.clientX / window.innerWidth;
            const y = e.clientY / window.innerHeight;
            
            blob1.style.transform = `translate(${x * 30}px, ${y * 30}px)`;
            blob2.style.transform = `translate(${-x * 30}px, ${-y * 30}px)`;
        }
    });
});
