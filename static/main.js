// Page state persistence functionality
const PageStateManager = {
    STORAGE_KEY: 'vc_stats_current_page',
    
    // Save the current page to localStorage
    savePage: function(path) {
        try {
            localStorage.setItem(this.STORAGE_KEY, path);
        } catch (e) {
            console.warn('Failed to save page state:', e);
        }
    },
    
    // Get the saved page from localStorage
    getSavedPage: function() {
        try {
            return localStorage.getItem(this.STORAGE_KEY);
        } catch (e) {
            console.warn('Failed to retrieve page state:', e);
            return null;
        }
    },
    
    // Clear the saved page state
    clearPage: function() {
        try {
            localStorage.removeItem(this.STORAGE_KEY);
        } catch (e) {
            console.warn('Failed to clear page state:', e);
        }
    },
    
    // Check if we should redirect to a saved page
    checkForSavedPage: function() {
        // Disabled: Always stay on the current page
        return false;
    }
};

// Main navigation functionality
document.addEventListener('DOMContentLoaded', () => {
    const navLinks = document.querySelectorAll('.nav-link');
    
    // Check for saved page state and redirect if needed
    const shouldRedirect = PageStateManager.checkForSavedPage();
    
    // If we're redirecting, don't set up navigation yet
    if (shouldRedirect) {
        return;
    }
    
    // Save current page immediately
    PageStateManager.savePage(window.location.pathname);
    
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
    
    // Add click handler for smooth navigation and page state saving
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            const targetPath = link.getAttribute('href');
            
            // Save the target page to localStorage
            PageStateManager.savePage(targetPath);
            
            // Update active navigation state
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
        });
    });
    
    // Save page state whenever the URL changes (for browser back/forward)
    window.addEventListener('popstate', () => {
        PageStateManager.savePage(window.location.pathname);
    });
});
