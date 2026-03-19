// Minimal admin JS: handle sidebar toggle, search filtering helpers
document.addEventListener('DOMContentLoaded', function(){
    // Optional: collapse sidebar on small screens
    const toggles = document.querySelectorAll('.sidebar-toggle');
    toggles.forEach(t=> t.addEventListener('click', () => {
        document.querySelector('.sidebar').classList.toggle('collapsed');
    }));

    // Simple client-side table search for pages with input[data-search-for]
    document.querySelectorAll('input[data-search-for]').forEach(input => {
        const selector = input.getAttribute('data-search-for');
        input.addEventListener('input', () => {
            const q = input.value.toLowerCase();
            document.querySelectorAll(selector).forEach(row => {
                const text = row.innerText.toLowerCase();
                row.style.display = text.includes(q) ? '' : 'none';
            });
        });
    });
});
