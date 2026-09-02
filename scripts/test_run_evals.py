"""Characterisation + regression tests for scripts/run_evals.sh.

Runs the real script (a copy of it) against a temp git repo containing
synthetic evals/cases/*.yaml, so the tests exercise the actual bash
implementation rather than a re-description of it.
"""
import os, subprocess, tempfile, unittest

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


def _run(root, args=(), env=None):
    run_env = dict(os.environ)
    # Force the "no claude runner" path regardless of the host environment:
    # strip ANTHROPIC_API_KEY and use a PATH made only of standard system
    # directories, which still has bash/git/awk/etc but never a `claude`
    # binary (installers commonly put it in a language-toolchain bin dir).
    run_env.pop("ANTHROPIC_API_KEY", None)
    run_env["PATH"] = "/usr/bin:/bin"
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


if __name__ == "__main__":
    unittest.main()
