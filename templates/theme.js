/* templates/theme.js - Theme switching and persistence logic */

const themeManager = {
    currentTheme: 'dark',

    init() {
        this.loadTheme();
        this.renderToggleButton();
    },

    async loadTheme() {
        try {
            const res = await fetch('/api/settings');
            if (res.ok) {
                const settings = await res.json();
                const theme = settings.theme || 'dark';
                this.setTheme(theme);
            }
        } catch (e) {
            console.error('Failed to load theme from settings:', e);
            this.setTheme('dark');
        }
    },

    setTheme(theme) {
        this.currentTheme = theme;
        document.documentElement.setAttribute('data-theme', theme);
        this.updateToggleButton();
    },

    async toggleTheme() {
        const newTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);

        // Save to backend
        try {
            // We need to fetch current settings first to merge
            const res = await fetch('/api/settings');
            const settings = await res.json();
            settings.theme = newTheme;

            await fetch('/api/settings', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            });
        } catch (e) {
            console.error('Failed to save theme to settings:', e);
        }
    },

    renderToggleButton() {
        // Find or create header-controls
        let controls = document.querySelector('.header-controls');
        if (!controls) return;

        const btn = document.createElement('button');
        btn.id = 'themeToggleBtn';
        btn.className = 'btn-secondary theme-toggle';
        btn.style.padding = '8px 12px';
        btn.style.fontSize = '18px';
        btn.onclick = () => this.toggleTheme();
        
        // Insert before language select or at start
        controls.insertBefore(btn, controls.firstChild);
        this.updateToggleButton();
    },

    updateToggleButton() {
        const btn = document.getElementById('themeToggleBtn');
        if (!btn) return;
        btn.innerHTML = this.currentTheme === 'dark' ? '☀️' : '🌙';
        btn.title = this.currentTheme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode';
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    themeManager.init();
});
