// Main navigation functionality
document.addEventListener('DOMContentLoaded', () => {
    const navLinks = document.querySelectorAll('.nav-link');
    
    // Remove active class from all links first
    navLinks.forEach(link => link.classList.remove('active'));
    
    // Set active nav based on current page
    const currentPath = window.location.pathname;
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        // Match the current path with the link href
        if (currentPath === href || (currentPath === '/' && href === '/')) {
            link.classList.add('active');
        } else if (currentPath.includes('/') && href !== '/' && currentPath.startsWith(href)) {
            link.classList.add('active');
        }
    });
    
    // Add click handler for smooth navigation
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            // Update active navigation state
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
        });
    });
});
