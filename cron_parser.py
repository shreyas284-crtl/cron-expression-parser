import sys

FIELDS = [
    ("minute", 0, 59),
    ("hour", 0, 23),
    ("day of month", 1, 31),
    ("month", 1, 12),
    ("day of week", 0, 6),
]
NAME_WIDTH = 14



def to_int(text, name):

    if not (text.isascii() and text.isdigit()):
        raise ValueError(f"{name}: '{text}' is not a valid number")
    return int(text)


def expand_part(part, name, low, high):

    range_text, slash, step_text = part.partition("/")

    step = 1
    if slash:
        step = to_int(step_text, name)
        if step < 1:
            raise ValueError(f"{name}: step must be at least 1 in '{part}'")

    if range_text == "*":
        start, end = low, high
    elif "-" in range_text:
        first, last = range_text.split("-", 1)
        start, end = to_int(first, name), to_int(last, name)
    else:
        start = to_int(range_text, name)
        end = high if slash else start  # '5/20' means 5, 25, 45, ...

    if start < low or end > high:
        raise ValueError(f"{name}: '{part}' is outside the range {low}-{high}")
    if start > end:
        raise ValueError(f"{name}: range start is after its end in '{part}'")

    return range(start, end + 1, step)


def expand_field(text, name, low, high):
    values = set()
    for part in text.split(","):
        values.update(expand_part(part, name, low, high))
    return sorted(values)



def parse(expression):
    parts = expression.split(None, 5)
    if len(parts) < 6:
        raise ValueError("expected five time fields followed by a command")

    rows = []
    for text, (name, low, high) in zip(parts[:5], FIELDS):
        values = expand_field(text, name, low, high)
        rows.append((name, " ".join(str(v) for v in values)))
    rows.append(("command", parts[5].rstrip()))
    return rows


def format_table(rows):
    return "\n".join(f"{label:<{NAME_WIDTH}}{text}" for label, text in rows)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print('usage: cron_parser.py "<minute> <hour> <day of month> '
              '<month> <day of week> <command>"', file=sys.stderr)
        return 2
    try:
        print(format_table(parse(argv[0])))
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())


