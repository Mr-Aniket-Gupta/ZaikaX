# ZaikaX Django Project

This is a backup of the **ZaikaX Django restaurant web application**.

---

## Push Issue & Secret Key

During development, GitHub push protection blocked a commit because a **Cashfree API key** was exposed in `ZaikaX/settings.py`.  
To allow the push, the secret key was temporarily allowed.  

**Important:** The API key in `settings.py` is **commented out**. To run the project:

1. Uncomment the lines related to Cashfree API in `ZaikaX/settings.py`.
2. Add your **own Cashfree API key and ID**.

Example in `settings.py`:

```python
# CASHFREE_API_KEY = "your_api_key_here"
# CASHFREE_APP_ID = "your_app_id_here"
