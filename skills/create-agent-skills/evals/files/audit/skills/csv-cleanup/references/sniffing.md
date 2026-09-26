# Sniffing

## Detect the dialect

Use `csv.Sniffer().sniff(sample, delimiters=",;\t|")` on the first 64 KiB,
and fall back to a comma when it raises `csv.Error`. Excel exports in
European locales use a semicolon.

## Byte order marks

Open files with `encoding="utf-8-sig"` so a UTF-8 BOM does not end up in
the first header name.
