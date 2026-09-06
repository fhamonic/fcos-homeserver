#!/usr/bin/env python3
"""Prove build_adhoc_script.py reproduces a template's files byte for byte.

Generates the ad hoc shell script for <key>, runs it in a throwaway fake
root (sudo/user management stripped, absolute paths on command lines
redirected), then compares every written file with the contents rendered
from the template.

usage: adhoc_roundtrip.py <key> [metaconfig.yaml]
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import types

import yaml
from jinja2 import StrictUndefined, Template

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))


def render(key, meta):
    cfg = yaml.safe_load(open(meta))
    if key not in cfg:
        sys.exit(f"'{key}' has no block in {meta}")
    idx = list(cfg).index(key) + 1
    src = open(os.path.join(REPO, "templates", f"{key}.yaml.j2")).read()
    return yaml.safe_load(Template(src, undefined=StrictUndefined).render({key: cfg[key]}, id=idx))


def generate_script(key, meta):
    # build_adhoc_script.py prompts through questionary; answer it in-process.
    fake_q = types.ModuleType("questionary")

    class _Select:
        def __init__(self, *a, **k):
            pass

        def ask(self):
            return key

    fake_q.select = _Select
    code = (
        "import sys, types, runpy\n"
        "sys.modules['questionary'] = q\n"
        f"sys.argv = ['build_adhoc_script.py', {meta!r}]\n"
        "runpy.run_path('build_adhoc_script.py', run_name='__main__')\n"
    )
    import io, contextlib

    buf = io.StringIO()
    cwd = os.getcwd()
    os.chdir(REPO)
    try:
        with contextlib.redirect_stdout(buf):
            exec(code, {"q": fake_q})
    finally:
        os.chdir(cwd)
    return buf.getvalue()


def localize(script, root):
    """Point command-line paths at the fake root; heredoc bodies stay verbatim."""
    out = []
    for line in script.splitlines():
        if re.match(r"^sudo (groupadd|useradd|chown) ", line):
            continue
        if re.match(r"^sudo (mkdir|chmod|tee|ln|touch) ", line):
            line = line.replace(" /", f" {root}/").replace(f"{root}/dev/null", "/dev/null")
            line = line[len("sudo "):]
        out.append(line)
    return "\n".join(out) + "\n"


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    key = sys.argv[1]
    meta = os.path.abspath(sys.argv[2] if len(sys.argv) > 2 else os.path.join(REPO, "metaconfig.yaml"))

    data = render(key, meta)
    root = tempfile.mkdtemp(prefix=f"adhoc-{key}-", dir=os.environ.get("SCRATCHPAD"))
    os.makedirs(os.path.join(root, "var/lib/systemd/linger"))  # exists on a real host
    try:
        script = localize(generate_script(key, meta), root)
        subprocess.run(["bash", "-e"], input=script, text=True, check=True)

        bad = 0
        for f in data.get("storage", {}).get("files", []):
            if "contents" not in f:
                continue
            expected = f["contents"]["inline"]
            if not expected.endswith("\n"):
                expected += "\n"
            actual = open(root + f["path"]).read()
            ok = actual == expected
            bad += not ok
            print(("OK " if ok else "BAD"), f["path"])
        for link in data.get("storage", {}).get("links", []):
            ok = os.path.islink(root + link["path"])
            bad += not ok
            print(("OK " if ok else "BAD"), link["path"], "(link)")
        print("round trip:", "PASS" if not bad else f"FAIL ({bad} mismatches)")
        sys.exit(1 if bad else 0)
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    main()
