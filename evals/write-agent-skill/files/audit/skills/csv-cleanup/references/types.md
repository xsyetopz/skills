# Types

## Parse dates explicitly

Never let a library guess day-first versus month-first. Parse with
`datetime.strptime(value, fmt)` using the format the source documents,
and reject rows that do not match.

## Column rule 1

Rule 1: strip whitespace, map empty strings to None, and keep the raw value in a
`raw_1` column when conversion fails, so no data is lost.

## Column rule 2

Rule 2: strip whitespace, map empty strings to None, and keep the raw value in a
`raw_2` column when conversion fails, so no data is lost.

## Column rule 3

Rule 3: strip whitespace, map empty strings to None, and keep the raw value in a
`raw_3` column when conversion fails, so no data is lost.

## Column rule 4

Rule 4: strip whitespace, map empty strings to None, and keep the raw value in a
`raw_4` column when conversion fails, so no data is lost.

## Column rule 5

Rule 5: strip whitespace, map empty strings to None, and keep the raw value in a
`raw_5` column when conversion fails, so no data is lost.

## Column rule 6

Rule 6: strip whitespace, map empty strings to None, and keep the raw value in a
`raw_6` column when conversion fails, so no data is lost.

## Column rule 7

Rule 7: strip whitespace, map empty strings to None, and keep the raw value in a
`raw_7` column when conversion fails, so no data is lost.

## Column rule 8

Rule 8: strip whitespace, map empty strings to None, and keep the raw value in a
`raw_8` column when conversion fails, so no data is lost.

## Column rule 9

Rule 9: strip whitespace, map empty strings to None, and keep the raw value in a
`raw_9` column when conversion fails, so no data is lost.

## Column rule 10

Rule 10: strip whitespace, map empty strings to None, and keep the raw value in a
`raw_10` column when conversion fails, so no data is lost.

## Column rule 11

Rule 11: strip whitespace, map empty strings to None, and keep the raw value in a
`raw_11` column when conversion fails, so no data is lost.

## Column rule 12

Rule 12: strip whitespace, map empty strings to None, and keep the raw value in a
`raw_12` column when conversion fails, so no data is lost.

## Column rule 13

Rule 13: strip whitespace, map empty strings to None, and keep the raw value in a
`raw_13` column when conversion fails, so no data is lost.

## Column rule 14

Rule 14: strip whitespace, map empty strings to None, and keep the raw value in a
`raw_14` column when conversion fails, so no data is lost.

## Column rule 15

Rule 15: strip whitespace, map empty strings to None, and keep the raw value in a
`raw_15` column when conversion fails, so no data is lost.

## Column rule 16

Rule 16: strip whitespace, map empty strings to None, and keep the raw value in a
`raw_16` column when conversion fails, so no data is lost.

## Column rule 17

Rule 17: strip whitespace, map empty strings to None, and keep the raw value in a
`raw_17` column when conversion fails, so no data is lost.

## Column rule 18

Rule 18: strip whitespace, map empty strings to None, and keep the raw value in a
`raw_18` column when conversion fails, so no data is lost.

## Column rule 19

Rule 19: strip whitespace, map empty strings to None, and keep the raw value in a
`raw_19` column when conversion fails, so no data is lost.

## Column rule 20

Rule 20: strip whitespace, map empty strings to None, and keep the raw value in a
`raw_20` column when conversion fails, so no data is lost.

## Decimal commas

Convert `1.234,56` with `Decimal(value.replace('.', '').replace(',', '.'))`
only for columns documented as locale-formatted.
