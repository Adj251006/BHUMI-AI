"""Authentication and role-based access control module.

Submodules:
    security    — password hashing, JWT creation/verification
    schemas     — Pydantic request/response models
    dependencies — FastAPI dependencies (get_current_user, require_roles)
    router      — /auth endpoints (login, register, refresh, me)
"""
