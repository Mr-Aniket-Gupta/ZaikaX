# Contributing to ZaikaX

Thanks for your interest in contributing!

## Development Setup

1. Clone the repo:
   ```
   git clone https://github.com/yourusername/ZaikaX_Capstone.git
   cd ZaikaX_Capstone
   ```

2. Create virtual environment:
   ```
   python -m venv venv
   venv\\Scripts\\activate  # Windows
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt  # Create if missing: django, pillow, etc.
   ```

4. Apply migrations & seed:
   ```
   python manage.py makemigrations
   python manage.py migrate
   python seed_menu.py
   python cart/seed_orders.py
   ```

5. Run server:
   ```
   python manage.py runserver
   ```

6. Create superuser:
   ```
   python manage.py createsuperuser
   ```

## Development Workflow
- Branch: `feat/your-feature` or `fix/issue`
- Commit: Conventional (e.g., `feat: add user reviews`)
- Code style: Black (`pip install black; black .`), flake8
- Tests: `python manage.py test`
- PR: Describe changes, link issues

## Cashfree Payments
Uncomment & add your keys in `ZaikaX/settings.py`.

Happy contributing! 🚀
