import subprocess
import sys
import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
BINUNICODE = REPOSITORY / "scripts" / "binunicode"


class BinunicodeCliTests(unittest.TestCase):
    def run_binunicode(
        self, *arguments: str, stdin: str = ""
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(BINUNICODE), *arguments],
            input=stdin,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_all_six_conversion_directions(self) -> None:
        cases = [
            (("-u", "luiz", "-o", "x"), "6c 75 69 7a\n"),
            (("-x", "6c 75 69 7a", "-o", "u"), "luiz\n"),
            (("-u", "A", "-o", "b"), "01000001\n"),
            (("-b", "01000001", "-o", "u"), "A\n"),
            (("-x", "41 ff", "-o", "b"), "01000001 11111111\n"),
            (("-b", "01000001 11111111", "-o", "x"), "41 ff\n"),
        ]

        for arguments, expected_stdout in cases:
            with self.subTest(arguments=arguments):
                result = self.run_binunicode(*arguments)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, expected_stdout)

    def test_unicode_uses_utf8_bytes(self) -> None:
        encoded = self.run_binunicode("-u", "Olá", "-o", "hex")
        decoded = self.run_binunicode("-x", "4f 6c c3 a1", "-o", "unicode")

        self.assertEqual(encoded.returncode, 0, encoded.stderr)
        self.assertEqual(encoded.stdout, "4f 6c c3 a1\n")
        self.assertEqual(decoded.returncode, 0, decoded.stderr)
        self.assertEqual(decoded.stdout, "Olá\n")

    def test_omitted_input_value_reads_stdin_verbatim(self) -> None:
        result = self.run_binunicode("-u", "-o", "x", stdin="A\n")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "41 0a\n")

    def test_output_accepts_full_names_and_to_alias(self) -> None:
        result = self.run_binunicode("--unicode", "A", "--to", "hexadecimal")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "41\n")

    def test_direct_input_may_start_with_a_hyphen_using_equals(self) -> None:
        result = self.run_binunicode("--unicode=-value", "-o", "x")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "2d 76 61 6c 75 65\n")

    def test_same_format_conversion_normalizes_hexadecimal(self) -> None:
        result = self.run_binunicode("-x", "4F\t6C", "-o", "x")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "4f 6c\n")

    def test_rejects_malformed_byte_groups(self) -> None:
        for arguments in [
            ("-b", "1", "-o", "x"),
            ("-x", "f", "-o", "b"),
        ]:
            with self.subTest(arguments=arguments):
                result = self.run_binunicode(*arguments)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("whitespace-separated", result.stderr)

    def test_rejects_invalid_utf8_for_unicode_output(self) -> None:
        result = self.run_binunicode("-x", "ff", "-o", "u")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("utf-8", result.stderr)

    def test_requires_input_and_output_formats(self) -> None:
        missing_input = self.run_binunicode("-o", "x")
        missing_output = self.run_binunicode("-u", "A")

        self.assertNotEqual(missing_input.returncode, 0)
        self.assertIn("one of the arguments", missing_input.stderr)
        self.assertNotEqual(missing_output.returncode, 0)
        self.assertIn("required", missing_output.stderr)


if __name__ == "__main__":
    unittest.main()
