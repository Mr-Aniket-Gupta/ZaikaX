// ZaikaX Script (script.js)

// --- Cart State ---
let cart = [];

// Utility to update UI totals
function updateCartUI() {
  const totalEl = document.querySelector('.cart-bar .total');
  const countEl = document.querySelector('.cart-bar .count');
  const modal = document.querySelector('.modal');

  const total = cart.reduce((sum, item) => sum + item.price, 0);
  totalEl.textContent = `$${total.toFixed(2)}`;
  countEl.textContent = cart.length;

  // Re-render modal items
  const itemsContainer = modal.querySelector('.items');
  itemsContainer.innerHTML = '';

  cart.forEach((item, index) => {
    const div = document.createElement('div');
    div.className = 'cart-item';
    div.innerHTML = `
      <img src="${item.img}" alt="item" />
      <div class="info">
        <strong>${item.name}</strong><br>
        <small>$${item.price.toFixed(2)}</small>
      </div>
      <button class="remove" data-index="${index}">✕</button>
    `;
    itemsContainer.appendChild(div);
  });

  // Bind remove buttons
  document.querySelectorAll('.remove').forEach(btn => {
    btn.onclick = () => {
      const i = btn.getAttribute('data-index');
      cart.splice(i, 1);
      updateCartUI();
    };
  });
}

// --- Add to Cart Buttons ---
document.addEventListener('click', function (e) {
  if (e.target.classList.contains('add')) {
    const card = e.target.closest('.card');
    const name = card.querySelector('h3').textContent;
    const img = card.querySelector('img').src;
    const price = parseFloat(card.querySelector('.cheapest strong').textContent.replace('$', ''));

    cart.push({ name, img, price });
    updateCartUI();
  }
});

// --- Toggle Cart Modal ---
document.querySelector('.cart-bar').addEventListener('click', () => {
  document.querySelector('.modal').classList.toggle('show');
});

// Initial UI render
updateCartUI();
