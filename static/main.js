// Main navigation functionality

// XSS Protection: Escape HTML special characters
function escapeHtml(text) {
    if (typeof text !== 'string') return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Error handling helper
function showError(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `<div class="error-message">⚠️ ${escapeHtml(message)}</div>`;
    } else {
        console.error('Error:', message);
    }
}

// Loading spinner helper
function showLoader(elementId, message = 'Loading...') {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="loader-container">
                <div class="spinner"></div>
                <p class="loader-text">${escapeHtml(message)}</p>
            </div>
        `;
    }
}

// Empty state helper
function showEmptyState(elementId, message = 'No data available', icon = '📭') {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">${icon}</div>
                <p class="empty-message">${escapeHtml(message)}</p>
            </div>
        `;
    }
}

// Clear element
function clearElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = '';
    }
}

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
    
    // Add click and keyboard handler for smooth navigation
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            // Update active navigation state
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
        });
        
        // Add keyboard support (Enter/Space to activate link)
        link.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                link.click();
            }
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
    
    // Modal accessibility - Handle Escape key and focus management
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            const modals = document.querySelectorAll('.modal.show');
            modals.forEach(modal => {
                const closeBtn = modal.querySelector('.close');
                if (closeBtn) closeBtn.click();
            });
        }
    });
    
    // Improve close button accessibility
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('close')) {
            const modal = e.target.closest('.modal');
            if (modal) {
                modal.classList.remove('show');
            }
        }
    });
});
