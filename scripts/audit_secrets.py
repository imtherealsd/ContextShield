"""Pre-deployment secret exposure audit script.

Scans all non-ignored project files for sensitive credentials.
DOES NOT PRINT ANY SECRET VALUES.
"""

import os
import re
from pathlib import Path
from dotenv import dotenv_values

WORKSPACE = Path("D:/YC-Moss")

# Load values from local secret files to test against
SENSITIVE_VARS = {"GEMINI_API_KEY", "MOSS_PROJECT_KEY", "LIVEKIT_API_SECRET", "LIVEKIT_API_KEY"}
secret_values = set()
for env_file in [WORKSPACE / ".env", WORKSPACE / ".env.local", WORKSPACE / "frontend/.env.local"]:
    if env_file.exists():
        vals = dotenv_values(env_file)
        for k, v in vals.items():
            if k in SENSITIVE_VARS and v and len(v.strip()) > 8:
                secret_values.add(v.strip())

# Ignore patterns
EXCLUDED_DIRS = {".git", ".next", "node_modules", "__pycache__", ".pytest_cache", "brain", ".gemini", "scratch"}
EXCLUDED_FILES = {".env", ".env.local", ".env.example"}

jwt_pattern = re.compile(r"eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}")

violations = []

for root, dirs, files in os.walk(WORKSPACE):
    dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
    for file in files:
        if file in EXCLUDED_FILES or file.endswith((".pyc", ".png", ".webp", ".log")):
            continue
        filepath = Path(root) / file
        relpath = filepath.relative_to(WORKSPACE)
        try:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
            # 1. Check for literal secrets from .env
            for s in secret_values:
                if s in content:
                    violations.append(f"Secret value match in: {relpath}")
                    break
            # 2. Check for JWT tokens
            if jwt_pattern.search(content):
                # Check if it's not in tests or example
                if not str(relpath).startswith("tests"):
                    violations.append(f"JWT pattern match in: {relpath}")
        except Exception:
            pass

print("=" * 60)
print("PRE-DEPLOYMENT REPOSITORY SECURITY AUDIT")
print("=" * 60)
if violations:
    print("secret exposure found = true")
    print("Violations:")
    for v in violations:
        print(f"  - {v}")
else:
    print("secret exposure found = false")
print("=" * 60)
