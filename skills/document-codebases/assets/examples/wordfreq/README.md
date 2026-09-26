# wordfreq

wordfreq prints the most frequent words in text files, one count and
word per line.

## Quick start

Requires Python 3.10 or later. From this directory:

```sh
python3 wordfreq.py --top 2 sample.txt
```

Expected output:

```text
3 the
2 dog
```

## Usage

Read from standard input when no file is given:

```sh
printf 'b a b\n' | python3 wordfreq.py -n 1
```

Expected output:

```text
2 b
```

See [the options](#options) and the [contributing guide](CONTRIBUTING.md).

## Options

| Option | Default | Meaning |
| --- | --- | --- |
| `-n`, `--top` | 3 | Number of words to print |
