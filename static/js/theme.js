/* templates/theme.js - Theme and Style switching logic */

const themeManager = {
    currentTheme: 'dark',
    currentStyle: 'glass',

    init() {
        this.loadTheme();
        this.renderControls();
    },

    async loadTheme() {
        try {
            const res = await fetch('/api/settings');
            if (res.ok) {
                const settings = await res.json();
                const theme = settings.theme || 'dark';
                const style = settings.style || 'glass';
                this.setTheme(theme, style);
            }
        } catch (e) {
            console.error('Failed to load theme from settings:', e);
            this.setTheme('dark', 'glass');
        }
    },

    setTheme(theme, style) {
        this.currentTheme = theme;
        this.currentStyle = style;
        document.documentElement.setAttribute('data-theme', theme);
        document.documentElement.setAttribute('data-style', style);
        this.updateControls();
    },

    async toggleTheme() {
        const newTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme, this.currentStyle);
        this.saveSettings();
    },

    async changeStyle(newStyle) {
        this.setTheme(this.currentTheme, newStyle);
        this.saveSettings();
    },

    async saveSettings() {
        try {
            const res = await fetch('/api/settings');
            const settings = await res.json();
            settings.theme = this.currentTheme;
            settings.style = this.currentStyle;

            await fetch('/api/settings', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            });
        } catch (e) {
            console.error('Failed to save theme to settings:', e);
        }
    },

    renderControls() {
        let controls = document.querySelector('.header-controls');
        if (!controls) return;

        // Create style select dropdown
        const select = document.createElement('select');
        select.id = 'styleSelectBtn';
        select.className = 'language-select'; // Reuse styles
        select.style.marginRight = '5px';
        
        const options = [
            { value: 'glass', label: 'Glassmorphism' },
            { value: 'neumorphic', label: 'Neumorphism' },
            { value: 'cyberpunk', label: 'Cyberpunk' }
        ];

        options.forEach(opt => {
            const el = document.createElement('option');
            el.value = opt.value;
            el.textContent = opt.label;
            select.appendChild(el);
        });

        select.onchange = (e) => this.changeStyle(e.target.value);

        // Create mode toggle button
        const btn = document.createElement('button');
        btn.id = 'themeToggleBtn';
        btn.className = 'btn-secondary theme-toggle';
        btn.style.padding = '8px 12px';
        btn.style.fontSize = '18px';
        btn.onclick = () => this.toggleTheme();
        
        // Insert before language select
        controls.insertBefore(btn, controls.firstChild);
        controls.insertBefore(select, btn);
        
        this.updateControls();
    },

    updateControls() {
        const btn = document.getElementById('themeToggleBtn');
        if (btn) {
            btn.innerHTML = this.currentTheme === 'dark' ? '☀️' : '🌙';
            btn.title = this.currentTheme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode';
        }

        const select = document.getElementById('styleSelectBtn');
        if (select) {
            select.value = this.currentStyle;
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    themeManager.init();
});

