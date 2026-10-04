"""Account creation, login and logout.

Passwords are hashed with Argon2id and only the hash is stored in users.password_hash.
Neither the password nor the hash is ever returned, logged, or echoed in errors.
The logged-in user's id is kept in a signed session cookie (see main.py).
"""

import hashlib
import hmac
import re
import sqlite3

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from db import get_connection

router = APIRouter(prefix="/api/auth")

hasher = PasswordHasher()  # Argon2id with argon2-cffi's recommended parameters

# Hashed once at startup so a login with an unknown email still costs one full
# verification, which keeps response times from revealing which emails exist.
DUMMY_HASH = hasher.hash("campus-customs-dummy-password")

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 8
INVALID_CREDENTIALS = "Invalid email or password."

# The accounts seeded into the original database use "pbkdf2_sha256$<salt>$<hex digest>",
# hashed with 120,000 iterations (the count is not stored in the hash itself).
LEGACY_PREFIX = "pbkdf2_sha256$"
LEGACY_ITERATIONS = 120_000


class CreateAccountRequest(BaseModel):
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    password: str = ""
    confirm_password: str = ""


class LoginRequest(BaseModel):
    email: str = ""
    password: str = ""


def normalize_email(email: str) -> str:
    return email.strip().lower()


def public_user(row: sqlite3.Row) -> dict:
    """The only user fields the API ever returns."""
    return {
        "id": row["id"],
        "first_name": row["first_name"],
        "last_name": row["last_name"],
        "email": row["email"],
    }


def verify_legacy_password(password_hash: str, password: str) -> bool:
    try:
        _, salt, expected = password_hash.split("$")
    except ValueError:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), LEGACY_ITERATIONS)
    return hmac.compare_digest(digest.hex(), expected)


def is_legacy_hash(password_hash: str) -> bool:
    return password_hash.startswith(LEGACY_PREFIX)


def verify_password(password_hash: str, password: str) -> bool:
    if is_legacy_hash(password_hash):
        return verify_legacy_password(password_hash, password)
    try:
        return hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


@router.post("/register", status_code=201)
def register(body: CreateAccountRequest, request: Request) -> dict:
    first_name = body.first_name.strip()
    last_name = body.last_name.strip()
    email = normalize_email(body.email)

    errors: dict[str, str] = {}
    if not first_name:
        errors["first_name"] = "First name is required."
    if not last_name:
        errors["last_name"] = "Last name is required."
    if not email:
        errors["email"] = "Email is required."
    elif not EMAIL_PATTERN.match(email):
        errors["email"] = "Enter a valid email address."
    if not body.password:
        errors["password"] = "Password is required."
    elif len(body.password) < MIN_PASSWORD_LENGTH:
        errors["password"] = f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
    if not body.confirm_password:
        errors["confirm_password"] = "Please confirm your password."
    elif body.password != body.confirm_password:
        errors["confirm_password"] = "Passwords do not match."
    if errors:
        raise HTTPException(status_code=400, detail={"errors": errors})

    password_hash = hasher.hash(body.password)
    with get_connection() as conn:
        if conn.execute("SELECT 1 FROM users WHERE lower(email) = ?", (email,)).fetchone():
            raise HTTPException(
                status_code=409,
                detail={"errors": {"email": "An account with this email already exists."}},
            )
        try:
            cursor = conn.execute(
                "INSERT INTO users (name, first_name, last_name, email, password_hash)"
                " VALUES (?, ?, ?, ?, ?)",
                (f"{first_name} {last_name}", first_name, last_name, email, password_hash),
            )
        except sqlite3.IntegrityError:
            # Another request registered the same email between the check and the insert.
            raise HTTPException(
                status_code=409,
                detail={"errors": {"email": "An account with this email already exists."}},
            )
        row = conn.execute("SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone()

    request.session.clear()
    request.session["user_id"] = row["id"]
    return public_user(row)


@router.post("/login")
def login(body: LoginRequest, request: Request) -> dict:
    email = normalize_email(body.email)
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE lower(email) = ?", (email,)).fetchone()

    if row is None:
        verify_password(DUMMY_HASH, body.password)
        raise HTTPException(status_code=401, detail=INVALID_CREDENTIALS)
    if not verify_password(row["password_hash"], body.password):
        raise HTTPException(status_code=401, detail=INVALID_CREDENTIALS)

    # Upgrade legacy pbkdf2 hashes (and Argon2 hashes with outdated settings) to
    # current Argon2id now that the plaintext password is known to be correct.
    if is_legacy_hash(row["password_hash"]) or hasher.check_needs_rehash(row["password_hash"]):
        with get_connection() as conn:
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (hasher.hash(body.password), row["id"]),
            )

    request.session.clear()
    request.session["user_id"] = row["id"]
    return public_user(row)


@router.post("/logout")
def logout(request: Request) -> dict:
    request.session.clear()
    return {"ok": True}


def current_user(request: Request) -> sqlite3.Row | None:
    """The logged-in user's row, from the signed session cookie, or None for a guest.

    The single source of truth for "who is this?" across the API: the cookie holds
    only the user id, signed by the server, so the browser cannot claim to be
    someone else.
    """
    user_id = request.session.get("user_id")
    if user_id is None:
        return None
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if row is None:  # account no longer exists
        request.session.clear()
    return row


@router.get("/me")
def me(request: Request) -> dict | None:
    """Returns the logged-in user, or null when nobody is logged in."""
    row = current_user(request)
    return public_user(row) if row else None
