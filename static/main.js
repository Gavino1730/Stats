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
    
    // Reload data button handler
    const reloadBtn = document.getElementById('reload-data-btn');
    if (reloadBtn) {
        reloadBtn.addEventListener('click', async () => {
            reloadBtn.disabled = true;
            reloadBtn.textContent = '⏳ Reloading...';
            
            try {
                const response = await fetch('/api/reload-data', { method: 'POST' });
                const data = await response.json();
                
                if (response.ok) {
                    reloadBtn.textContent = '✓ Reloaded!';
                    // Reload the current page after 500ms to show new data
                    setTimeout(() => {
                        window.location.reload();
                    }, 500);
                } else {
                    throw new Error(data.error || 'Failed to reload data');
                }
            } catch (error) {
                console.error('Error reloading data:', error);
                reloadBtn.textContent = '✗ Error';
                setTimeout(() => {
                    reloadBtn.textContent = '🔄 Reload Data';
                    reloadBtn.disabled = false;
                }, 2000);
            }
        });
    }
});
