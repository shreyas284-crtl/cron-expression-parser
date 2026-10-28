import io
import unittest
from contextlib import redirect_stderr, redirect_stdout

from cron_parser import expand_field, format_table, main, parse

SAMPLE = "*/15 0 1,15 * 1-5 /usr/bin/find"
EXPECTED = "\n".join([
    "minute".ljust(14) + "0 15 30 45",
    "hour".ljust(14) + "0",
    "day of month".ljust(14) + "1 15",
    "month".ljust(14) + "1 2 3 4 5 6 7 8 9 10 11 12",
    "day of week".ljust(14) + "1 2 3 4 5",
    "command".ljust(14) + "/usr/bin/find",
])


class ExpandFieldTests(unittest.TestCase):
    def test_star_expands_to_full_range(self):
        self.assertEqual(expand_field("*", "hour", 0, 23), list(range(24)))

    def test_single_number(self):
        self.assertEqual(expand_field("5", "minute", 0, 59), [5])

    def test_list(self):
        self.assertEqual(expand_field("1,15", "day of month", 1, 31), [1, 15])

    def test_range(self):
        self.assertEqual(expand_field("1-5", "day of week", 0, 6), [1, 2, 3, 4, 5])

    def test_step_over_star(self):
        self.assertEqual(expand_field("*/15", "minute", 0, 59), [0, 15, 30, 45])

    def test_step_over_range(self):
        self.assertEqual(expand_field("1-10/3", "minute", 0, 59), [1, 4, 7, 10])

    def test_start_with_step(self):
        self.assertEqual(expand_field("5/20", "minute", 0, 59), [5, 25, 45])

    def test_overlapping_parts_are_merged_and_sorted(self):
        self.assertEqual(expand_field("5,1-3,2-4", "minute", 0, 59), [1, 2, 3, 4, 5])

    def test_boundaries_are_allowed(self):
        self.assertEqual(expand_field("0,59", "minute", 0, 59), [0, 59])

    def test_invalid_values_raise(self):
        bad = ["60", "-1", "a", "", "1,,2", "5-1", "*/0", "*/", "1-",
               "1-2-3", "*-5", "0-61", "1.5"]
        for text in bad:
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    expand_field(text, "minute", 0, 59)

    def test_day_of_month_zero_is_invalid(self):
        with self.assertRaises(ValueError):
            expand_field("0", "day of month", 1, 31)


class ParseTests(unittest.TestCase):
    def test_sample_from_the_task(self):
        self.assertEqual(format_table(parse(SAMPLE)), EXPECTED)

    def test_values_start_at_column_15(self):
        for line in format_table(parse(SAMPLE)).splitlines():
            self.assertEqual(line[13], " ")
            self.assertNotEqual(line[14], " ")

    def test_command_keeps_its_spaces_and_arguments(self):
        rows = parse("0 12 * * 0 /usr/bin/backup --full /data")
        self.assertEqual(rows[-1], ("command", "/usr/bin/backup --full /data"))

    def test_extra_whitespace_is_ignored(self):
        rows = parse("  0   12 * *   0   run  ")
        self.assertEqual(rows[0], ("minute", "0"))
        self.assertEqual(rows[-1], ("command", "run"))

    def test_too_few_fields_raise(self):
        for text in ["", "* * * * *", "* * * *  cmd"]:
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse(text)

    def test_invalid_field_raises(self):
        with self.assertRaises(ValueError):
            parse("61 * * * * cmd")


class CommandLineTests(unittest.TestCase):
    def run_main(self, args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(args)
        return code, out.getvalue(), err.getvalue()

    def test_success_prints_table(self):
        code, out, err = self.run_main([SAMPLE])
        self.assertEqual(code, 0)
        self.assertEqual(out, EXPECTED + "\n")
        self.assertEqual(err, "")

    def test_invalid_expression_returns_1_and_message(self):
        code, out, err = self.run_main(["99 * * * * cmd"])
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("error", err)

    def test_wrong_argument_count_returns_2(self):
        for args in ([], ["a", "b"]):
            with self.subTest(args=args):
                code, _, err = self.run_main(args)
                self.assertEqual(code, 2)
                self.assertIn("usage", err)


if __name__ == "__main__":
    unittest.main()