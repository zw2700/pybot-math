"""Tests for the command line in pybot.py. Run from the repository root:

    python -m unittest discover -s tests

They check the command line only, not what PyBot says: the bot's own tests live in the swarm's
repository.
"""
import argparse
import contextlib
import io
import os
import subprocess
import sys
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pybot  # noqa: E402


def run(args, stdin=None):
    return subprocess.run([sys.executable, "-m", "pybot"] + args, input=stdin, capture_output=True,
                          text=True, cwd=ROOT, timeout=600)


class Terminal(io.StringIO):
    """Captured output that says it is a terminal, as the chat sees a real one."""

    def isatty(self):
        return True


def chat(typed, **options):
    """Run the interactive chat on these typed lines; return (the prompts shown, the lines printed)."""
    prompts, text = chat_output(typed, **options)
    return prompts, text.splitlines()


def chat_output(typed, terminal=False, **options):
    """Run the interactive chat; return (the prompts shown, everything printed, as one string)."""
    args = argparse.Namespace(prompt=None, interactive=False, seed=None, verbose=False)
    for name, value in options.items():
        setattr(args, name, value)
    typed = iter(typed)
    prompts = []

    def typing(prompt=""):
        prompts.append(prompt)
        try:
            return next(typed)
        except StopIteration:
            raise EOFError

    out = Terminal() if terminal else io.StringIO()
    with mock.patch("builtins.input", typing), contextlib.redirect_stdout(out):
        pybot.chat(pybot.load_bot(), args)
    return prompts, out.getvalue()


class ChatOpening(unittest.TestCase):
    def test_the_chat_opens_with_the_name_in_ascii_art_then_what_pybot_is(self):
        _, lines = chat(["/exit"])
        logo = pybot.LOGO.split("\n")
        self.assertEqual(lines[:len(logo)], logo)
        self.assertEqual(lines[len(logo)], "")
        self.assertEqual(lines[len(logo) + 1],
                         "A chatbot written in plain Python. No weights, no training, just rules.")
        self.assertIn("/reset", lines[len(logo) + 2])

    def test_the_art_is_plain_ascii_and_fits_a_narrow_terminal(self):
        logo = pybot.LOGO.split("\n")
        self.assertEqual(len(logo), 6)
        for line in logo:
            self.assertLessEqual(len(line), 80)
            self.assertEqual(line, line.rstrip())
            self.assertTrue(all(ord(character) < 128 for character in line))


class ChatTurnsAreLabelled(unittest.TestCase):
    def test_the_prompt_is_user_and_every_reply_starts_with_pybot(self):
        prompts, lines = chat(["hello", "how do i descale a kettle", "/exit"])
        self.assertEqual(prompts, ["user: "] * 3)
        replies = [line for line in lines if line.startswith("pybot: ")]
        self.assertEqual(len(replies), 2)
        for reply in replies:
            self.assertGreater(len(reply), len("pybot: "))

    def test_a_first_message_given_with_p_is_shown_as_the_users_turn(self):
        prompts, lines = chat(["/exit"], prompt="hello", interactive=True)
        self.assertIn("user: hello", lines)
        self.assertEqual(sum(line.startswith("pybot: ") for line in lines), 1)
        self.assertEqual(prompts, ["user: "])

    def test_commands_and_empty_lines_get_no_reply(self):
        prompts, lines = chat(["", "/help", "/reset", "/exit"])
        self.assertEqual(len(prompts), 4)
        self.assertFalse(any(line.startswith("pybot: ") for line in lines))
        self.assertIn("New conversation.", lines)

    def test_the_chat_ends_when_input_ends(self):
        prompts, lines = chat(["hello"])
        self.assertEqual(sum(line.startswith("pybot: ") for line in lines), 1)

    def test_verbose_names_the_module_under_the_reply(self):
        _, lines = chat(["hello", "/exit"], verbose=True)
        index = next(i for i, line in enumerate(lines) if line.startswith("pybot: "))
        self.assertRegex(lines[index + 1], r"^\[module: \S+ \| \d+ ms\]$")


class ResetClearsTheConversation(unittest.TestCase):
    @unittest.skipIf(os.name == "nt", "Windows clears the screen with cls, not an escape sequence")
    def test_in_a_terminal_reset_wipes_the_screen_and_shows_the_opening_again(self):
        _, text = chat_output(["hello", "/reset", "/exit"], terminal=True)
        before, wipe, after = text.partition("\033[H\033[2J\033[3J")
        self.assertTrue(wipe)
        self.assertIn("pybot: ", before)
        self.assertTrue(after.startswith(pybot.LOGO))
        self.assertNotIn("pybot: ", after)
        self.assertNotIn("New conversation.", text)

    def test_reset_makes_pybot_forget_what_was_said(self):
        turns_remembered = []
        real = pybot.answer

        def watching(runtime, text, memory):
            turns_remembered.append(len(memory.get("turns", [])))
            return real(runtime, text, memory)

        with mock.patch.object(pybot, "answer", watching):
            chat(["hello", "how are you", "/reset", "hello", "/exit"])
        self.assertEqual(turns_remembered, [0, 1, 0])

    def test_when_output_is_not_a_terminal_reset_prints_one_plain_line(self):
        _, text = chat_output(["hello", "/reset", "/exit"])
        self.assertIn("New conversation.", text.splitlines())
        self.assertNotIn("\033", text)


class OneShotAndPipeStayPlain(unittest.TestCase):
    def test_p_prints_the_reply_alone(self):
        result = run(["-p", "hello"])
        self.assertEqual(result.returncode, 0)
        lines = result.stdout.splitlines()
        self.assertEqual(len(lines), 1)
        self.assertFalse(lines[0].startswith("pybot: "))

    def test_piped_input_matches_the_bots_own_loop(self):
        typed = "hello\nhow do i descale a kettle\nhow long does that take\n\nthanks\n"
        mine = run(["-s", "0"], stdin=typed)
        theirs = subprocess.run(
            [sys.executable, "-c", "import random; random.seed(0); from bot.__main__ import main; main()"],
            input=typed, capture_output=True, text=True, cwd=ROOT, timeout=600)
        self.assertEqual(mine.returncode, 0)
        self.assertEqual(mine.stdout, theirs.stdout)
        self.assertEqual(len(mine.stdout.splitlines()), 5)


if __name__ == "__main__":
    unittest.main()
