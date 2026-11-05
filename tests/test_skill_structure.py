#!/usr/bin/env python3
"""Offline checks for Signingflow agent skills. No API key is required."""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
NAME = re.compile(r"^signingflow-[a-z0-9]+(?:-[a-z0-9]+)*$")
FENCE = re.compile(r"```(json|python)\n(.*?)```", re.S)
SECRET_ARG = re.compile(r"add_argument\(\s*[\"']--(?:secret|api-key|password|token|signature)[\"']")
IDEMPOTENCY_UUID = re.compile(
    r'"idempotencyKey"\s*:\s*"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})"'
)
KNOWN_KEY = "550e8400-e29b-41d4-a716-446655440000"


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        fail("SKILL.md is missing frontmatter")
    end = text.find("\n---\n", 4)
    if end < 0:
        fail("SKILL.md frontmatter is not closed")
    block = text[4:end]
    found: dict[str, str] = {}
    for line in block.splitlines():
        if line.startswith("name:"):
            found["name"] = line.split(":", 1)[1].strip()
        elif line.startswith("version:"):
            found["version"] = line.split(":", 1)[1].strip()
        elif line.startswith("description:"):
            found["description"] = line.split(":", 1)[1].strip()
    if "description" not in found and "description: >" in block:
        found["description"] = "folded"
    return found


def main() -> None:
    readme = README.read_text()
    skills = sorted(path for path in ROOT.iterdir() if (path / "SKILL.md").is_file())
    if len(skills) != 5:
        fail(f"expected 5 skills, found {len(skills)}")
    for skill in skills:
        text = (skill / "SKILL.md").read_text()
        meta = frontmatter(text)
        if meta.get("name") != skill.name or not NAME.match(skill.name):
            fail(f"{skill.name} has a bad skill name")
        if not re.match(r"^\d+\.\d+\.\d+$", meta.get("version", "")):
            fail(f"{skill.name} has a bad version")
        if not meta.get("description"):
            fail(f"{skill.name} has no description")
        if "primaryEnv: SIGNINGFLOW_API_KEY" not in text:
            fail(f"{skill.name} is missing primaryEnv")
        if f"`{skill.name}`" not in readme and skill.name not in readme:
            fail(f"README does not list {skill.name}")
        if KNOWN_KEY in text or IDEMPOTENCY_UUID.search(text):
            fail(f"{skill.name} contains a reusable idempotency key")
        for kind, body in FENCE.findall(text):
            if kind == "json":
                json.loads(body)
            else:
                ast.parse(body)
        for script in skill.glob("scripts/*.py"):
            if script.name not in text and f"scripts/{script.name}" not in text:
                fail(f"{skill.name} does not reference {script.name}")
            source = script.read_text()
            if SECRET_ARG.search(source):
                fail(f"{script} accepts a secret on the command line")
            ast.parse(source)
    print(f"structure ok ({len(skills)} skills)")


if __name__ == "__main__":
    main()
