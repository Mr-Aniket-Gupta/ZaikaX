# ZaikaX Capstone Presentation Notes

## 1. Project Overview
ZaikaX ek full-stack restaurant web application hai jahan user menu browse karta hai, cart me items add karta hai, checkout karta hai, aur payment flow complete karta hai.

Core idea: **restaurant operations + customer ordering + admin control** ek hi platform me.

---

## 2. Libraries and Tools Used

### Backend (Python)
1. **Django**
- MVC-style web framework (models, views, templates).
- Authentication, routing, ORM, admin support.

2. **Pillow**
- Image handling ke liye use hota hai (`ImageField` support for menu images).

3. **python-dotenv**
- `.env` se secrets/config load karne ke liye.

4. **requests**
- External payment API (Cashfree) ko call karne ke liye HTTP requests.

5. **gunicorn**
- Production WSGI server deployment ke liye.

6. **psycopg2-binary**
- PostgreSQL adapter (production DB option ke liye).

### Database
1. **SQLite** (development default)
2. **PostgreSQL** (production optional)

### Frontend
1. **Django Templates** (HTML rendering)
2. **Custom CSS + Vanilla JS**
3. **Bootstrap 5** (admin panel UI)
4. **Font Awesome** (icons)
5. **Chart.js** (admin analytics graph)

### Integration
1. **Cashfree Payment Gateway** (payment app)

---

## 3. Main Apps (Module-wise)
1. **main**
- Home, About, Contact, Login, Register, Profile pages.
- FAQ search/reply endpoint.

2. **menu**
- Menu listing by categories.
- Mood-based suggestions and menu visuals.

3. **cart**
- Add to cart, quantity update, remove item, checkout flow.

4. **payment**
- Cashfree order creation and payment confirmation.

5. **accounts**
- Address model and forms for user profile/address management.

6. **adminpanel**
- Custom admin dashboard (orders, users, menu management, sales chart).

7. **orders**
- Order-related model/view grouping.

---

## 4. How the Project Works (End-to-End Flow)

### User Flow
1. User register/login karta hai.
2. Menu page par categories ke through dishes explore karta hai.
3. Dish cart me add karta hai; quantity increase/decrease kar sakta hai.
4. Cart se checkout page par जाता hai.
5. Address select/add karta hai.
6. Payment flow initiate hota hai (Cashfree).
7. Successful payment ke baad order confirmation milti hai.
8. Profile page par user apna data aur addresses manage karta hai.

### Admin Flow
1. Admin login karta hai custom admin panel me.
2. Dashboard par pending/completed/cancelled orders aur analytics dekhta hai.
3. Menu items add/edit/delete karta hai.
4. Users aur orders monitor karta hai.

---

## 5. Data Model Summary
1. **User**
- Authentication and identity.

2. **Address**
- User ke multiple delivery addresses.
- Default address support.

3. **MenuItem**
- Dish info: name, category, price, image, veg/non-veg.

4. **CartItem**
- User + MenuItem + quantity.

5. **Order**
- Checkout ke baad final order snapshot and total.

6. **OrderItem**
- Order ke andar individual items and purchased price.

7. **PaymentSession**
- Cashfree order ID and payment status tracking.

---

## 6. Special Features You Can Mention in Presentation
1. Clean modern UI redesign for login/register/profile/menu/cart.
2. Profile section with address add/edit/delete/default.
3. Cart quantity controls (`+` / `-`) with live recalculation.
4. Image-aware menu seeding from media folder.
5. Admin sales analytics using Chart.js.
6. Payment gateway integration concept with external API.
7. Seed scripts for quick demo data setup.

---

## 7. Demo Script (Presentation Friendly)

### 3–5 minute demo sequence
1. Home page open करो.
2. Login/Register UI show करो.
3. Menu page pe cards aur categories show करो.
4. Cart me item add karke quantity +/− demonstrate करो.
5. Profile page me user info update + address add/edit/delete show करो.
6. Admin dashboard open karke analytics and order status cards show करो.

---

## 8. Commands for Live Demo Setup

```bash
python manage.py migrate
python seed_menu.py
python -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE','ZaikaX.settings'); django.setup(); from cart.seed_orders import create_sample_orders; create_sample_orders()"
python manage.py runserver
```

---

## 9. One-Line Pitch for Viva/Presentation
**"ZaikaX is a complete restaurant ordering platform built with Django that combines customer ordering, profile/address management, payment workflow, and admin analytics in one integrated system."**
