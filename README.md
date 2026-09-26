# envx

load a `.env` file and run a command with those vars set. like `dotenv`
but it's one file and it just runs the thing.

## usage

```bash
# run with vars from ./.env
python envx.py -- python app.py

# a different file
python envx.py --env .env.local -- npm start

# override a var on the command line (repeatable)
python envx.py -e PORT=8080 -e DEBUG=1 -- python app.py

# just show the resolved vars, run nothing
python envx.py --print
```

handles comments, quoted values, `export KEY=VAL` prefixes, and blank
lines. existing environment vars are kept unless the file overrides them.

values can reference other vars with `$VAR` or `${VAR}`. they resolve
against vars defined earlier in the file and the real environment:

```bash
BASE=/opt/app
BIN=$BASE/bin        # /opt/app/bin
CONF=${BASE}/conf    # /opt/app/conf
```

unknown refs are left alone, and a var referencing itself just stays
literal (no infinite loop).

exit code of the command is passed straight through, so this is fine in
scripts:

```bash
python envx.py -- pytest || echo "tests failed"
```

## notes

- single file, stdlib only, no install
- missing env file is an error (exit 1)
- lines that don't look like `KEY=VAL` are skipped with a warning
- if your command itself starts with a dash, use the `--` separator shown above

## license

do whatever you want with it
