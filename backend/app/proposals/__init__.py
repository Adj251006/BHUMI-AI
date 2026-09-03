"""Proposals module — manages land acquisition proposal lifecycle and approvals.

Submodules:
    schemas — Pydantic models for request validation and response formatting
    service — Core state machine, RBAC checks, and database queries
    router  — FastAPI endpoints for /proposals
"""
