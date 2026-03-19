// Spotlight interactivity: scroll-to-dish and small confetti burst
document.addEventListener('DOMContentLoaded', function () {
  const btn = document.querySelector('.spotlight-cta');
  if (!btn) return;

  btn.addEventListener('click', function () {
    const name = this.dataset.name;
    // find first card with matching h3 text
    const cards = document.querySelectorAll('.menu-card');
    let target = null;
    cards.forEach(card => {
      const h3 = card.querySelector('h3');
      if (h3 && h3.textContent.trim() === name && !target) target = card;
    });

    if (target) {
      target.scrollIntoView({ behavior: 'smooth', block: 'center' });
      // subtle highlight
      target.style.transition = 'box-shadow 350ms ease, transform 350ms ease';
      target.style.boxShadow = '0 12px 30px rgba(16, 185, 129, 0.14)';
      target.style.transform = 'translateY(-4px)';
      setTimeout(() => { target.style.boxShadow = ''; target.style.transform = ''; }, 900);
      // small confetti burst
      confettiBurst(this.parentElement);
    } else {
      window.scrollTo({ top: 0, behavior: 'smooth' });
      confettiBurst(this.parentElement);
    }
  });

  function confettiBurst(container) {
    for (let i = 0; i < 12; i++) {
      const p = document.createElement('span');
      p.className = 'mini-confetti';
      p.style.left = (Math.random() * 80 + 10) + '%';
      p.style.background = ['#ff7a59','#ffd166','#06d6a0','#80ffdb','#ffd6a5'][Math.floor(Math.random()*5)];
      p.style.transform = `rotate(${Math.random()*360}deg)`;
      container.appendChild(p);
      setTimeout(() => { p.remove(); }, 900);
    }
  }
});

// add confetti CSS dynamically (keeps file minimal)
const style = document.createElement('style');
style.textContent = `
.mini-confetti{ position:absolute; top:8px; width:8px; height:14px; border-radius:2px; opacity:0.95; transform-origin:center; animation: confetti-fall 800ms cubic-bezier(.2,.8,.2,1); pointer-events:none; z-index:30; }
@keyframes confetti-fall { 0% { transform: translateY(0) scale(1); opacity:1 } 100% { transform: translateY(120px) scale(.7) rotate(240deg); opacity:0 } }
`;
document.head.appendChild(style);