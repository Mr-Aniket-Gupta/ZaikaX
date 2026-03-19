document.addEventListener('DOMContentLoaded', function () {
  const slider = document.getElementById('reviews-slider');
  if (!slider) return;
  const prev = document.querySelector('.reviews-prev');
  const next = document.querySelector('.reviews-next');

  // show small auto-scroll
  let idx = 0;
  const cards = slider.querySelectorAll('.review-card');
  function scrollToIndex(i){
    if (!cards[i]) return;
    cards[i].scrollIntoView({ behavior: 'smooth', inline: 'center' });
    idx = i;
  }

  prev.addEventListener('click', () => { scrollToIndex(Math.max(0, idx - 1)); });
  next.addEventListener('click', () => { scrollToIndex(Math.min(cards.length - 1, idx + 1)); });
});