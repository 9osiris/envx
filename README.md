# watchrun

rerun a command whenever files under the given paths change. polls mtimes,
no dependencies, works anywhere python does.

## usage

```bash
# rerun the test suite when anything under src/ or tests/ changes
python watchrun.py src tests -- pytest

# rebuild when the markdown changes
python watchrun.py docs -- make site

# clear the screen between runs so output doesn't pile up
python watchrun.py --clear src -- python main.py
```

runs the command once at startup, then watches. ctrl-c to stop.

hidden files and dirs (anything starting with `.`) are ignored by default;
pass `--all` to watch them too.

## flags

- `--clear` — clear the screen between runs
- `--debounce SEC` — wait this long after a change before rerunning (default 0.5)
- `--interval SEC` — seconds between change checks (default 1.0)
- `--all` — also watch hidden files and dirs

## notes

- single file, stdlib only, no install
- new files, deleted files, and content changes all trigger a rerun

## license

do whatever you want with it
