#!/usr/bin/env python3
"""Setup test users (seller & partner), verify them and run schemathesis with tokens.

This script performs the sequence: signup -> generate verify token -> call verify -> login -> run schemathesis
It runs schemathesis twice: once with the seller token and once with the partner token, targeting all paths.

Usage:
  source venv/bin/activate
  python scripts/setup_and_run_schemathesis.py

Adjust `APP_URL` env var if your app runs on a different host/port.
"""
import os
import subprocess
import time
import uuid

import httpx

from app.utils import generate_url_safe_token


APP_URL = os.environ.get("APP_URL", "http://localhost:8000")


def unique_email(prefix: str) -> str:
    return f"{prefix}+{uuid.uuid4().hex[:8]}@example.com"


def signup_user(role: str, email: str, password: str) -> dict:
    """Sign up a seller or partner and return the created resource JSON."""
    url = f"{APP_URL}/{role}/signup"
    payload = {
        "name": "Test User",
        "email": email,
        "password": password,
    }
    # partner expects more fields; add defaults
    if role == "partner":
        payload.update({
            "max_handling_capacity": 5,
            "serviceable_zip_codes": [11001],
        })

    r = httpx.post(url, json=payload)
    r.raise_for_status()
    return r.json()


def verify_user(role: str, user_id: str, email: str) -> None:
    token = generate_url_safe_token({"email": email, "id": user_id})
    url = f"{APP_URL}/{role}/verify?token={token}"
    r = httpx.get(url)
    r.raise_for_status()


def login_user(role: str, email: str, password: str) -> str:
    url = f"{APP_URL}/{role}/token"
    # OAuth2PasswordRequestForm expects form-encoded fields: username & password
    r = httpx.post(url, data={"username": email, "password": password})
    r.raise_for_status()
    data = r.json()
    return data.get("access_token")


def run_schemathesis_with_token(token: str, label: str = "seller") -> None:
    cmd = [
        "schemathesis",
        "run",
        f"{APP_URL}/openapi.json",
        "--checks",
        "all",
        "--max-examples",
        "50",
        "--header",
        f"Authorization: Bearer {token}",
    ]
    print("Running schemathesis for", label)
    subprocess.run(cmd)


def main():
    seller_email = unique_email("seller")
    partner_email = unique_email("partner")
    password = "Password123!"

    print("Signing up seller...", seller_email)
    seller = signup_user("seller", seller_email, password)
    seller_id = seller.get("id")
    print("Seller created id=", seller_id)

    print("Signing up partner...", partner_email)
    partner = signup_user("partner", partner_email, password)
    partner_id = partner.get("id")
    print("Partner created id=", partner_id)

    # Give the app/worker a second to persist and for DB triggers
    time.sleep(1)

    print("Verifying seller...")
    verify_user("seller", seller_id, seller_email)
    print("Verifying partner...")
    verify_user("partner", partner_id, partner_email)

    print("Logging in seller...")
    seller_token = login_user("seller", seller_email, password)
    print("Seller token obtained")

    print("Logging in partner...")
    partner_token = login_user("partner", partner_email, password)
    print("Partner token obtained")

    # Run schemathesis per role to keep auth correct per endpoint group
    run_schemathesis_with_token(seller_token, label="seller")
    run_schemathesis_with_token(partner_token, label="partner")


if __name__ == "__main__":
    main()
