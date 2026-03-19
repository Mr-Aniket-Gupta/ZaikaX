# Security Policy

## Supported Versions

We currently support the latest version of ZaikaX.

| Version | Supported          |
|---------|--------------------|
| Latest  | ✅                  |

## Reporting a Vulnerability

If you discover a security vulnerability within ZaikaX, please report it responsibly.

**Email:** [your-email@example.com] (replace with your contact)

We aim to respond within 48 hours and fix critical issues within 7 days.

### What to include:
- Description of the vulnerability
- Steps to reproduce
- Impact assessment
- Proposed fix (optional)

## Security Practices
- Use environment variables for secrets (Cashfree API keys, DATABASE_URL)
- HTTPS enforced in production
- Dependencies scanned regularly
- User input sanitized (Django forms/CSRF)
- Rate limiting on login/payment endpoints recommended

Thanks for helping keep ZaikaX safe!
