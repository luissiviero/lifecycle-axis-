import os, stat, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
VERIFY_SH = os.path.join(HERE, "verify.sh")


def _read(path):
    with open(path) as f:
        return f.read()


def _make_repo(root):
    """Build a minimal git repo containing scripts/verify.sh and a
    minimal .sdlc/config.env with VERIFY_CMDS="true"."""
    subprocess.run(["git", "init", "-q", root], check=True)
    os.makedirs(os.path.join(root, ".sdlc"), exist_ok=True)
    with open(os.path.join(root, ".sdlc", "config.env"), "w") as f:
        f.write('VERIFY_CMDS="true"\n')
    os.makedirs(os.path.join(root, "scripts", "checks"), exist_ok=True)
    with open(os.path.join(root, "scripts", "verify.sh"), "w") as f:
        f.write(_read(VERIFY_SH))
    os.chmod(os.path.join(root, "scripts", "verify.sh"), 0o755)


def _write_check(root, name, body, executable=True):
    path = os.path.join(root, "scripts", "checks", name)
    with open(path, "w") as f:
        f.write(body)
    mode = 0o755 if executable else 0o644
    os.chmod(path, mode)
    return path


def _run_verify(root):
    return subprocess.run(
        ["bash", os.path.join(root, "scripts", "verify.sh")],
        cwd=root,
        capture_output=True,
        text=True,
    )


def _last_line(text):
    lines = [l for l in text.splitlines() if l.strip()]
    return lines[-1] if lines else ""


class VerifyScript(unittest.TestCase):
    def test_passes_with_no_checks(self):
        with tempfile.TemporaryDirectory() as root:
            _make_repo(root)
            result = _run_verify(root)
            self.assertEqual(result.returncode, 0)
            self.assertRegex(_last_line(result.stdout), r"^VERIFY: PASS")

    def test_failing_check_fails_verify(self):
        with tempfile.TemporaryDirectory() as root:
            _make_repo(root)
            _write_check(root, "zz-fail.sh", "#!/usr/bin/env bash\nexit 1\n")
            result = _run_verify(root)
            self.assertEqual(_last_line(result.stdout), "VERIFY: FAIL")
            self.assertEqual(result.returncode, 1)

    def test_non_executable_check_is_skipped(self):
        with tempfile.TemporaryDirectory() as root:
            _make_repo(root)
            _write_check(
                root, "zz-fail.sh", "#!/usr/bin/env bash\nexit 1\n", executable=False
            )
            result = _run_verify(root)
            self.assertEqual(result.returncode, 0)
            self.assertRegex(_last_line(result.stdout), r"^VERIFY: PASS")

    def test_empty_checks_dir_passes(self):
        with tempfile.TemporaryDirectory() as root:
            _make_repo(root)
            self.assertEqual(
                os.listdir(os.path.join(root, "scripts", "checks")), []
            )
            result = _run_verify(root)
            self.assertEqual(result.returncode, 0)
            self.assertRegex(_last_line(result.stdout), r"^VERIFY: PASS")


if __name__ == "__main__":
    unittest.main()
