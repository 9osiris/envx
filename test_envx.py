#!/usr/bin/env python3
# tests for envx. run with: python3 test_envx.py

import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import envx

PY = sys.executable

passed = failed = 0


def check(name, cond):
    global passed, failed
    if cond:
        passed += 1
        print(f"ok - {name}")
    else:
        failed += 1
        print(f"FAIL - {name}")


def run_cli(*args, cwd=None, env=None):
    e = dict(os.environ)
    if env:
        e.update(env)
    return subprocess.run([PY, str(HERE / "envx.py"), *args],
                          capture_output=True, text=True, cwd=cwd, env=e)


def make_env_file(text):
    d = Path(tempfile.mkdtemp())
    f = d / ".env"
    f.write_text(text)
    return f


# unit: parse_env basics
e = envx.parse_env("A=1\nB=two\n")
check("parse_env simple", e == {"A": "1", "B": "two"})
e = envx.parse_env("# comment\n\nA=1 # trailing\n")
check("parse_env comments and blanks", e == {"A": "1"})
e = envx.parse_env('A="hello world"\nB=\'it\'s\'\n')
check("parse_env quoted values", e == {"A": "hello world", "B": "it's"})
e = envx.parse_env("export A=1\n")
check("parse_env export prefix", e == {"A": "1"})
e = envx.parse_env('A="a # not a comment"\n')
check("parse_env hash inside quotes kept", e == {"A": "a # not a comment"})
e = envx.parse_env("1BAD=x\nNOEQUALS\nOK=1\n")
check("parse_env skips bad lines", e == {"OK": "1"})

# unit: interpolate
check("interpolate dollar", envx.interpolate("$A/b", {"A": "x"}) == "x/b")
check("interpolate braces", envx.interpolate("${A}/b", {"A": "x"}) == "x/b")
check("interpolate unknown left alone",
      envx.interpolate("$NOPE/x", {}) == "$NOPE/x")
check("interpolate self ref stays literal",
      envx.interpolate("$A", {"A": "$A"}) == "$A")

# cli: --print shows resolved vars in file order, runs nothing
f = make_env_file("BASE=/opt/app\nBIN=$BASE/bin\n# ignored\nPORT=8080\n")
r = run_cli("--print", "--env", str(f))
check("--print exits 0", r.returncode == 0)
check("--print resolves interpolation",
      r.stdout.splitlines() == ["BASE=/opt/app", "BIN=/opt/app/bin", "PORT=8080"])

# cli: --print with -e override replaces and appends in order
r = run_cli("--print", "--env", str(f), "-e", "PORT=9090", "-e", "NEW=yes")
check("--print override replaces in place",
      r.stdout.splitlines() == ["BASE=/opt/app", "BIN=/opt/app/bin",
                                "PORT=9090", "NEW=yes"])

# cli: --print ignores any command given after --
r = run_cli("--print", "--env", str(f), "--",
            PY, "-c", "import sys; sys.exit(5)")
check("--print does not run the command", r.returncode == 0)
check("--print still prints with a command",
      "BASE=/opt/app" in r.stdout)

# cli: --print with a missing file is an error
r = run_cli("--print", "--env", "/nonexistent/.env")
check("--print missing file fails", r.returncode == 1)
check("--print missing file says why", "no such file" in r.stderr)

# cli: --print with a bad override is an error
r = run_cli("--print", "--env", str(f), "-e", "NOEQUALS")
check("--print bad override fails", r.returncode == 1)

# cli: run mode still works, env reaches the command
r = run_cli("--env", str(f), "--", PY, "-c",
            "import os; print(os.environ['BIN'])")
check("run mode sets vars", r.returncode == 0 and r.stdout.strip() == "/opt/app/bin")

# cli: exit code passes through
r = run_cli("--env", str(f), "--", PY, "-c", "import sys; sys.exit(3)")
check("exit code passes through", r.returncode == 3)

# cli: no command and no --print is still an error
r = run_cli("--env", str(f))
check("no command without --print fails", r.returncode != 0)

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
