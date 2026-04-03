// ---- Theme Toggle ----
const themeToggle = document.getElementById('themeToggle');
if (themeToggle) {
    const buttons = themeToggle.querySelectorAll('button');

    function setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('om-theme', theme);
        buttons.forEach(btn => btn.classList.toggle('active', btn.dataset.theme === theme));
    }

    const savedTheme = localStorage.getItem('om-theme') || 'auto';
    setTheme(savedTheme);

    buttons.forEach(btn => btn.addEventListener('click', () => setTheme(btn.dataset.theme)));
}

// ---- Scroll Reveal ----
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) entry.target.classList.add('visible');
    });
}, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

document.querySelectorAll('.reveal').forEach(el => observer.observe(el));

// ---- Nav scroll state ----
const nav = document.getElementById('nav');
if (nav) {
    window.addEventListener('scroll', () => nav.classList.toggle('scrolled', window.scrollY > 20));
}
