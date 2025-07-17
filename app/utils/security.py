# app/utils/security.py

"""
This module is kept for compatibility but is no longer used.

⚠️ Authentik now handles:
- Password hashing & verification
- JWT creation & signing (RS256)

If local JWT creation or password hashing is ever needed again,
you can restore the original implementation.
"""

# No-op stub — Authentik handles authentication & tokens.

def create_access_token(*args, **kwargs):
    raise NotImplementedError("JWTs are now issued by Authentik.")

def hash_password(*args, **kwargs):
    raise NotImplementedError("Passwords are handled by Authentik.")

def verify_password(*args, **kwargs):
    raise NotImplementedError("Passwords are handled by Authentik.")