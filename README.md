
python3 --version       
git clone https://github.com/shreyas284-crtl/cron-expression-parser.git
cd cron-expression-parser
python3 cron_parser.py "*/15 0 1,15 * 1-5 /usr/bin/find"

Output (field name in the first 14 columns, then the values):

minute        0 15 30 45
hour          0
day of month  1 15
month         1 2 3 4 5 6 7 8 9 10 11 12
day of week   1 2 3 4 5
command       /usr/bin/find

Exit codes: `0` success, `1` invalid cron string (message on stderr), `2` wrong usage.

Test
bash
python3 -m unittest -v


Project Files Layout (Blueprint) -

- `cron_parser.py`: the whole program
- `test_cron_parser.py`: unit tests (expansion, parsing, CLI)

Approach -

1. `parse` splits the input into five time fields plus the command. The command
   keeps its own spaces and arguments.
2. Each field is split on commas. `expand_part` handles one piece: `*`, `N`,
   `A-B`, each with an optional `/step`.
3. Values are validated against the field's range, merged, de-duplicated and sorted.
4. `format_table` prints each label padded to 14 columns.

Field names and valid ranges live in the `FIELDS` table, so changing a range or
adding a field is a one-line change.

Syntax -

| Syntax | Meaning | Example |
|---|---|---|
| `*` | every value | `*` |
| `N` | one value | `5` |
| `A-B` | inclusive range | `1-5` |
| `*/S`, `A-B/S` | every S-th value | `*/15`, `1-10/3` |
| `N/S` | from N to the maximum, every S | `5/20` |
| `a,b,c` | list of any of the above | `1,15`, `1-3,10` |

Ranges: minute 0-59, hour 0-23, day of month 1-31, month 1-12, day of week 0-6 (0 = Sunday).

Assumptions and limitations
- Numbers only: no names such as `JAN` or `MON`, and `7` is not accepted for Sunday.
- No special strings (`@yearly`) and no `?`, `L`, `W`, `#`.
- Day of month is not checked against the month (for example 31 Feb is accepted).
- It only expands the fields. It does not compute the next run time or run the command.