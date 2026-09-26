#!/usr/bin/env python3
"""envx - load a .env file and run a command with those vars set."""

import argparse
import os
import re
import subprocess
import sys


VAR_RE = re.compile(r"\$(\w+)|\$\{([^}]*)\}")


def interpolate(val, env):
    # expand $VAR and ${VAR} from env, leave unknown ones alone
    def sub(m):
        name = m.group(1) or m.group(2)
        return env.get(name, m.group(0))
    return VAR_RE.sub(sub, val)


def strip_inline_comment(line):
    # drop a # comment, but only when it's outside quotes
    quote = None
    for i, ch in enumerate(line):
        if ch in "\"'":
            if quote is None:
                quote = ch
            elif quote == ch:
                quote = None
        elif ch == "#" and quote is None:
            return line[:i]
    return line


def unquote(val):
    if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
        inner = val[1:-1]
        if val[0] == '"':
            inner = inner.replace("\\n", "\n").replace('\\"', '"').replace("\\\\", "\\")
        return inner
    return val


def parse_env(text):
    env = {}
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = strip_inline_comment(raw).strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            print(f"envx: line {lineno}: no '=' in {raw.strip()!r}, skipping", file=sys.stderr)
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        if key.startswith("export "):
            key = key[len("export "):].strip()
        if not key or key[0].isdigit() or not key.replace("_", "").isalnum():
            print(f"envx: line {lineno}: bad key {key!r}, skipping", file=sys.stderr)
            continue
        env[key] = unquote(val.strip())
    return env


def main():
    p = argparse.ArgumentParser(
        prog="envx",
        description="load a .env file, then run a command with those vars set",
    )
    p.add_argument("--env", default=".env", help="env file to load (default: .env)")
    p.add_argument("-e", action="append", default=[], metavar="KEY=VAL",
                   help="override a var on the command line, repeatable")
    p.add_argument("command", nargs=argparse.REMAINDER, help="command to run")
    args = p.parse_args()

    cmd = args.command
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    if not cmd:
        p.error("no command given")

    try:
        with open(args.env) as f:
            loaded = parse_env(f.read())
    except FileNotFoundError:
        print(f"envx: {args.env}: no such file", file=sys.stderr)
        return 1

    env = os.environ.copy()
    for key, val in loaded.items():
        env[key] = interpolate(val, env)
    for override in args.e:
        if "=" not in override:
            print(f"envx: bad override {override!r}, want KEY=VAL", file=sys.stderr)
            return 1
        key, _, val = override.partition("=")
        env[key.strip()] = interpolate(unquote(val.strip()), env)

    return subprocess.run(cmd, env=env).returncode


if __name__ == "__main__":
    sys.exit(main())
