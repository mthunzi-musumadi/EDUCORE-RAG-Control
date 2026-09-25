"""
Educore Enterprise RAG — User Migration / Sync Utility
Syncs users and bcrypt hashes from SQLite (webui.db) into LibreChat's MongoDB.
"""

import sqlite3
import os
import sys
import json

DB_PATH = os.path.abspath(r"data\openwebui\webui.db")

def read_webui_users():
    if not os.path.exists(DB_PATH):
        print(f"Error: webui.db not found at {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = """
    SELECT u.id, u.name, u.email, u.role, a.password 
    FROM user u
    LEFT JOIN auth a ON u.id = a.id OR u.email = a.email
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    users = []
    for r in rows:
        uid, name, email, role, pw_hash = r
        users.append({
            "educore_id": uid,
            "name": name,
            "username": email,
            "email": email,
            "role": "ADMIN" if role == "admin" else "USER",
            "password": pw_hash,
            "provider": "local"
        })
    return users

if __name__ == "__main__":
    users = read_webui_users()
    print("=" * 60)
    print(f" Extracted {len(users)} users from webui.db:")
    print("=" * 60)
    for u in users:
        pw_preview = (u['password'][:15] + "...") if u['password'] else "(no password set)"
        print(f" - {u['name']} <{u['email']}> | Role: {u['role']} | Hash: {pw_preview}")
    
    out_file = os.path.abspath(r"prototypes\librechat\data\exported_users.json")
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)
    print("=" * 60)
    print(f" Exported users to: {out_file}")
    print(" Ready for import into LibreChat MongoDB `users` collection.")
    print("=" * 60)
