// cart.js — ZaikaX Cart Management
// This module handles all cart actions: add, remove, update, total, persistence

// --- INITIALIZE CART FROM LOCALSTORAGE ---
let cart = JSON.parse(localStorage.getItem("zaikax_cart") || "[]");

// Save cart to storage
function saveCart() {
  localStorage.setItem("zaikax_cart", JSON.stringify(cart));
}

// Add item
function addToCart(item) {
  cart.push(item);
  saveCart();
  updateCartUI();
}

// Remove item
function removeFromCart(index) {
  cart.splice(index, 1);
  saveCart();
  updateCartUI();
}

// Get total price
function getCartTotal() {
  return cart.reduce((sum, i) => sum + Number(i.price), 0);
}

// Render Cart UI
function updateCartUI() {
  const totalBar = document.getElementById("cartTotal");
  const modalTotal = document.getElementById("cartTotalModal");
  const itemsContainer = document.getElementById("cartItems");

  if (!totalBar || !modalTotal || !itemsContainer) return;

  // Update totals
  const total = getCartTotal();
  totalBar.textContent = `₹${total}`;
  modalTotal.textContent = `₹${total}`;

  // Render list
  itemsContainer.innerHTML = "";
  cart.forEach((item, index) => {
    const div = document.createElement("div");
    div.className = "cart-row";
    div.innerHTML = `
      <img src="${item.img}" class="cart-img" />
      <div class="cart-info">
        <strong>${item.name}</strong><br>
        <span>₹${item.price}</span>
      </div>
      <button class="cart-remove" data-index="${index}">Remove</button>
    `;
    itemsContainer.appendChild(div);
  });

  // Bind remove buttons
  document.querySelectorAll('.cart-remove').forEach(btn => {
    btn.onclick = () => {
      const idx = btn.getAttribute('data-index');
      removeFromCart(idx);
    };
  });
}

// Toggle cart modal
function toggleCart() {
  document.getElementById("cartModal").classList.toggle("show");
}

// Auto-render at load
document.addEventListener("DOMContentLoaded", updateCartUI);