"""Characterisation + regression tests for scripts/run_evals.sh.

Runs the real script (a copy of it) against a temp git repo containing
synthetic evals/cases/*.yaml, so the tests exercise the actual bash
implementation rather than a re-description of it.
"""
import os, re, subprocess, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
RUN_EVALS_SH = os.path.join(HERE, "run_evals.sh")


def _read(path):
    with open(path) as f:
        return f.read()


def _make_repo(root):
    """Build a minimal git repo containing scripts/run_evals.sh, a minimal
    .sdlc/config.env, and an empty evals/cases/ directory."""
    subprocess.run(["git", "init", "-q", root], check=True)
    os.makedirs(os.path.join(root, ".sdlc"), exist_ok=True)
    with open(os.path.join(root, ".sdlc", "config.env"), "w") as f:
        f.write('VERIFY_CMDS="true"\n')
    os.makedirs(os.path.join(root, "scripts"), exist_ok=True)
    with open(os.path.join(root, "scripts", "run_evals.sh"), "w") as f:
        f.write(_read(RUN_EVALS_SH))
    os.chmod(os.path.join(root, "scripts", "run_evals.sh"), 0o755)
    os.makedirs(os.path.join(root, "evals", "cases"), exist_ok=True)


def _write_case(root, name, body):
    path = os.path.join(root, "evals", "cases", f"{name}.yaml")
    with open(path, "w") as f:
        f.write(body)
    return path


def _add_synthetic_cases(root):
    """Three cases: a passing hook case, a failing hook case, and a
    prompt-only skill case with no check (skipped without a Claude runner)."""
    _write_case(
        root,
        "pass-case",
        "name: pass-case\n"
        "kind: hook\n"
        'check: "true"\n',
    )
    _write_case(
        root,
        "fail-case",
        "name: fail-case\n"
        "kind: hook\n"
        'check: "false"\n',
    )
    _write_case(
        root,
        "prompt-case",
        "name: prompt-case\n"
        "kind: skill\n"
        'prompt: "do something"\n',
    )


def _no_claude_path():
    """A PATH that still has the tools run_evals.sh needs, but never a `claude` binary.

    On POSIX the standard system directories are exactly that. Git Bash on Windows keeps
    git in .../mingw64/bin, not /usr/bin, so that pair left run_evals.sh without git
    ("git: command not found") and all of these tests failed on empty output rather than
    testing anything (roadmap item 19b). There, keep the real PATH and drop only the
    directories that actually hold a claude executable, which preserves the point of the
    sanitised value.
    """
    if os.name != "nt":
        return "/usr/bin:/bin"
    names = ("claude", "claude.exe", "claude.cmd", "claude.bat", "claude.ps1")
    keep = [
        d
        for d in os.environ.get("PATH", "").split(os.pathsep)
        if d and not any(os.path.exists(os.path.join(d, n)) for n in names)
    ]
    return os.pathsep.join(keep)


def _run(root, args=(), env=None):
    run_env = dict(os.environ)
    # Force the "no claude runner" path regardless of the host environment:
    # strip both Claude credentials and use a PATH made only of standard system
    # directories, which still has bash/git/awk/etc but never a `claude`
    # binary (installers commonly put it in a language-toolchain bin dir).
    run_env.pop("ANTHROPIC_API_KEY", None)
    run_env.pop("CLAUDE_CODE_OAUTH_TOKEN", None)
    run_env["PATH"] = _no_claude_path()
    if env:
        run_env.update(env)
    return subprocess.run(
        ["bash", os.path.join(root, "scripts", "run_evals.sh"), *args],
        cwd=root,
        capture_output=True,
        text=True,
        env=run_env,
    )


def _last_line(text):
    lines = [l for l in text.splitlines() if l.strip()]
    return lines[-1] if lines else ""


class RunEvalsScript(unittest.TestCase):
    def test_counts_and_exit_code(self):
        with tempfile.TemporaryDirectory() as root:
            _make_repo(root)
            _add_synthetic_cases(root)
            result = _run(root)
            self.assertEqual(
                _last_line(result.stdout), "EVALS: 1 pass, 1 fail, 1 skipped"
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("prompt-case (skipped: prompt case, no Claude runner)", result.stdout)

    def test_only_selects_one_case_by_glob(self):
        with tempfile.TemporaryDirectory() as root:
            _make_repo(root)
            _add_synthetic_cases(root)
            result = _run(root, ["--only", "pass*"])
            self.assertEqual(
                _last_line(result.stdout), "EVALS: 1 pass, 0 fail, 0 skipped"
            )
            self.assertEqual(result.returncode, 0)
            self.assertIn("pass-case", result.stdout)
            self.assertNotIn("fail-case", result.stdout)
            self.assertNotIn("prompt-case", result.stdout)

    def test_kind_filters_to_hook_cases(self):
        with tempfile.TemporaryDirectory() as root:
            _make_repo(root)
            _add_synthetic_cases(root)
            result = _run(root, ["--kind", "hook"])
            # only pass-case and fail-case are kind: hook; prompt-case (skill) excluded
            self.assertEqual(
                _last_line(result.stdout), "EVALS: 1 pass, 1 fail, 0 skipped"
            )
            self.assertEqual(result.returncode, 1)
            self.assertNotIn("prompt-case", result.stdout)

    def test_kind_matching_nothing_is_zero_pass_zero_fail_exit_0(self):
        with tempfile.TemporaryDirectory() as root:
            _make_repo(root)
            _add_synthetic_cases(root)
            result = _run(root, ["--kind", "e2e"])
            self.assertEqual(
                _last_line(result.stdout), "EVALS: 0 pass, 0 fail, 0 skipped"
            )
            self.assertEqual(result.returncode, 0)

    def test_list_prints_names_and_kinds_and_exits_0(self):
        with tempfile.TemporaryDirectory() as root:
            _make_repo(root)
            _add_synthetic_cases(root)
            result = _run(root, ["--list"])
            self.assertEqual(result.returncode, 0)
            self.assertNotIn("EVALS:", result.stdout)
            lines = [l for l in result.stdout.splitlines() if l.strip()]
            names_and_kinds = {tuple(l.split()) for l in lines}
            self.assertEqual(
                names_and_kinds,
                {
                    ("pass-case", "hook"),
                    ("fail-case", "hook"),
                    ("prompt-case", "skill"),
                },
            )

    def test_list_honours_only_and_kind(self):
        with tempfile.TemporaryDirectory() as root:
            _make_repo(root)
            _add_synthetic_cases(root)
            result = _run(root, ["--kind", "hook", "--list"])
            lines = [l for l in result.stdout.splitlines() if l.strip()]
            self.assertEqual(sorted(l.split()[0] for l in lines), ["fail-case", "pass-case"])
            self.assertEqual(result.returncode, 0)

    def test_unknown_flag_prints_usage_to_stderr_and_exits_2(self):
        with tempfile.TemporaryDirectory() as root:
            _make_repo(root)
            _add_synthetic_cases(root)
            result = _run(root, ["--nope"])
            self.assertEqual(result.returncode, 2)
            self.assertIn("Usage:", result.stderr)
            self.assertEqual(result.stdout, "")

    def test_help_flag_prints_usage_to_stdout_and_exits_0(self):
        with tempfile.TemporaryDirectory() as root:
            _make_repo(root)
            _add_synthetic_cases(root)
            result = _run(root, ["-h"])
            self.assertEqual(result.returncode, 0)
            self.assertIn("Usage:", result.stdout)

    def test_prompt_only_case_is_skipped_without_claude_runner(self):
        with tempfile.TemporaryDirectory() as root:
            _make_repo(root)
            _add_synthetic_cases(root)
            result = _run(root, ["--only", "prompt-case"])
            self.assertEqual(
                _last_line(result.stdout), "EVALS: 0 pass, 0 fail, 1 skipped"
            )
            self.assertEqual(result.returncode, 0)

    def test_failing_check_prints_its_output(self):
        """work/loop-protection R-9: a red eval says why; a green one prints nothing extra."""
        with tempfile.TemporaryDirectory() as root:
            _make_repo(root)
            _write_case(
                root,
                "loud-fail",
                "name: loud-fail\nkind: hook\ncheck: |\n  echo boom-out; echo boom-err >&2; false\n",
            )
            _write_case(root, "quiet-pass", "name: quiet-pass\nkind: hook\ncheck: |\n  echo not-shown\n")
            result = _run(root)
            lines = result.stdout.splitlines()
            self.assertIn("✘ loud-fail", lines)
            i = lines.index("✘ loud-fail")
            self.assertEqual(lines[i + 1:i + 3], ["    boom-out", "    boom-err"])
            self.assertIn("✔ quiet-pass", lines)
            self.assertNotIn("not-shown", result.stdout)
            self.assertEqual(_last_line(result.stdout), "EVALS: 1 pass, 1 fail, 0 skipped")
            self.assertEqual(result.returncode, 1)

    def test_multiline_check_with_pipe_inside_a_string_runs_verbatim(self):
        """Pins that field() reads a `check: |` block verbatim even when its
        content contains the literal string "a | b" (regression for the
        risk that a future rewrite of the flag parsing mis-splits on `|`)."""
        with tempfile.TemporaryDirectory() as root:
            _make_repo(root)
            _write_case(
                root,
                "pipe-in-string",
                "name: pipe-in-string\n"
                "kind: hook\n"
                "check: |\n"
                "  printf '%s' 'a | b' | grep -q 'a | b'\n",
            )
            result = _run(root, ["--only", "pipe-in-string"])
            self.assertEqual(
                _last_line(result.stdout), "EVALS: 1 pass, 0 fail, 0 skipped"
            )
            self.assertEqual(result.returncode, 0)

    def test_require_claude_fails_a_skipped_prompt_case(self):
        """Nightly CI passes --require-claude so an expired credential is a red run, not a skip."""
        with tempfile.TemporaryDirectory() as root:
            _make_repo(root)
            _add_synthetic_cases(root)
            result = _run(root, ["--require-claude"])
            self.assertEqual(_last_line(result.stdout), "EVALS: 1 pass, 2 fail, 0 skipped")
            self.assertEqual(result.returncode, 1)
            self.assertIn("prompt-case (prompt case, no Claude runner; --require-claude)", result.stdout)
            self.assertNotIn("skipped:", result.stdout)
            result = _run(root, ["-h"])
            self.assertIn("--require-claude", result.stdout)

    def test_setup_runs_before_check(self):
        """A case may stage a fixture in `setup:`; it runs before the prompt and before the check."""
        with tempfile.TemporaryDirectory() as root:
            _make_repo(root)
            _write_case(
                root,
                "setup-case",
                "name: setup-case\n"
                "kind: hook\n"
                "setup: |\n"
                "  echo staged > staged.txt\n"
                'check: "test -f staged.txt && rm staged.txt"\n',
            )
            result = _run(root, ["--only", "setup-case"])
            self.assertEqual(_last_line(result.stdout), "EVALS: 1 pass, 0 fail, 0 skipped", result.stdout)
            self.assertEqual(result.returncode, 0)

    def test_failing_setup_fails_the_case(self):
        with tempfile.TemporaryDirectory() as root:
            _make_repo(root)
            _write_case(
                root,
                "bad-setup",
                "name: bad-setup\n"
                "kind: hook\n"
                "setup: |\n"
                "  echo fixture missing >&2; false\n"
                'check: "true"\n',
            )
            result = _run(root, ["--only", "bad-setup"])
            self.assertEqual(_last_line(result.stdout), "EVALS: 0 pass, 1 fail, 0 skipped", result.stdout)
            self.assertEqual(result.returncode, 1)
            self.assertIn("bad-setup (setup failed)", result.stdout)
            self.assertIn("fixture missing", result.stdout)


class AgentEvalsWorkflow(unittest.TestCase):
    """The suite runs nightly and by hand; per commit it runs inside the gate's own verify step.

    work/ci-budget R-4. The `hook-cases` job ran `--kind hook` on every pull request whose diff
    touched `scripts/**`, `.claude/**`, `.sdlc/**` or `evals/**`, which is nearly every pull request
    here, while `sdlc-gate` was already running `scripts/run_evals.sh` through `VERIFY_CMDS` on the
    same commit. Ninety-two runs bought nothing the gate had not proved, and each one also woke the
    merge script. What must not be lost with it: the nightly credential check (work/agent-evals R-4,
    R-6) and the deterministic cases on every gated commit.
    """

    WORKFLOW = os.path.join(os.path.dirname(HERE), ".github", "workflows", "agent-evals.yml")
    CONFIG = os.path.join(os.path.dirname(HERE), ".sdlc", "config.env")

    def setUp(self):
        self.text = _read(self.WORKFLOW)

    def test_no_pull_request_trigger_and_no_hook_cases_job(self):
        self.assertNotIn("pull_request:", self.text)
        self.assertNotIn("hook-cases", self.text)
        self.assertNotIn("--kind hook", self.text)
        # The paths filter goes with the trigger; a leftover one would be the only thing standing
        # between this workflow and a required-check that never reports.
        self.assertNotIn("paths:", self.text)

    def test_runs_nightly_and_can_be_started_by_hand(self):
        self.assertIn("schedule:", self.text)
        self.assertIn("cron:", self.text)
        self.assertIn("workflow_dispatch:", self.text)
        # `full-suite` no longer needs to ask which event it is: there is only one kind left.
        self.assertNotIn("github.event_name != 'pull_request'", self.text)

    def test_nightly_requires_claude(self):
        self.assertIn("scripts/run_evals.sh --require-claude", self.text)

    def test_nightly_trusts_the_checkout(self):
        self.assertIn("hasTrustDialogAccepted", self.text)

    def test_the_deterministic_cases_still_run_on_every_gated_commit(self):
        # This is the compensating control for dropping the per-pull-request job: the gate's Verify
        # step runs VERIFY_CMDS, which runs the same cases on the same commit.
        self.assertIn("scripts/run_evals.sh", _read(self.CONFIG))


class CaseBlocksAreWhole(unittest.TestCase):
    """work/run-queue, review round 0: an oracle that cannot fail is worse than no oracle.

    `field()` in run_evals.sh ends a `key: |` block at the first line that is not indented, and a
    BLANK line is not indented -- so a blank line inside a `check:` silently truncates it, and every
    assertion below the blank is never run. The case still reports a pass, because whatever command
    happened to land last exited 0. This scans the real cases so the trap cannot come back; it is the
    second time in this repository an oracle was written that could not fail (the first was a grep in
    work/approve-by-dispatch R-10 that nothing ran), which is why it is pinned in code rather than
    left to a lesson (rule 7).
    """

    CASES = os.path.join(os.path.dirname(HERE), "evals", "cases")

    def _blocks(self, text):
        """Yield (key, [lines]) for every `key: |` block, reading exactly as field() does."""
        key, lines = None, []
        for line in text.splitlines():
            if key is not None:
                if line.strip() == "" or not line[:1].isspace():
                    yield key, lines
                    key, lines = None, []
                    # fall through so this same line can open a new block
                else:
                    lines.append(line)
                    continue
            m = re.match(r"^(check|setup):\s*\|\s*$", line)
            if m:
                key, lines = m.group(1), []
        if key is not None:
            yield key, lines

    def test_no_case_has_a_blank_line_inside_a_check_or_setup_block(self):
        offenders = []
        for name in sorted(os.listdir(self.CASES)):
            if not name.endswith(".yaml"):
                continue
            path = os.path.join(self.CASES, name)
            text = _read(path)
            for key in ("check", "setup"):
                m = re.search(r"^%s:\s*\|\s*$" % key, text, re.M)
                if not m:
                    continue
                body = text[m.end():].split("\n")[1:]
                for line in body:
                    if line.strip() == "":
                        # A blank line ends the block. Anything indented after it is dead text.
                        rest = body[body.index(line) + 1:]
                        if any(l[:1].isspace() and l.strip() for l in rest):
                            offenders.append("%s: %s block is truncated at a blank line" % (name, key))
                        break
                    if not line[:1].isspace():
                        break
        self.assertEqual(offenders, [], "\n".join(offenders))


if __name__ == "__main__":
    unittest.main()
