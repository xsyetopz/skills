# logtail

logtail prints the last lines of a log file.

## Usage

Show the last five lines:

```sh
python3 logtail.py --limit 5 app.log
```

Show only errors:

```sh
python3 logtail.py --level error --limit 2 app.log
```
