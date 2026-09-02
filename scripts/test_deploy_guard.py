import os, subprocess, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEPLOY_SH = os.path.join(HERE, "deploy.sh")
ENVIRONMENTS_YAML = os.path.join(ROOT, ".sdlc", "environments.yaml")


def _read(path):
    with open(path) as f:
        return f.read()


def _make_repo(root):
    """Temp git repo with one commit and a copy of .sdlc/environments.yaml and
    scripts/deploy.sh, so the guard can read git HEAD and the environments file
    without touching the real repo."""
    subprocess.run(["git", "init", "-q", root], check=True)
    subprocess.run(["git", "-C", root, "config", "user.email", "t@example.com"], check=True)
    subprocess.run(["git", "-C", root, "config", "user.name", "test"], check=True)
    os.makedirs(os.path.join(root, ".sdlc"), exist_ok=True)
    with open(os.path.join(root, ".sdlc", "environments.yaml"), "w") as f:
        f.write(_read(ENVIRONMENTS_YAML))
    os.makedirs(os.path.join(root, "scripts"), exist_ok=True)
    deploy_copy = os.path.join(root, "scripts", "deploy.sh")
    with open(deploy_copy, "w") as f:
        f.write(_read(DEPLOY_SH))
    os.chmod(deploy_copy, 0o755)
    with open(os.path.join(root, "README.md"), "w") as f:
        f.write("placeholder\n")
    subprocess.run(["git", "-C", root, "add", "-A"], check=True)
    subprocess.run(["git", "-C", root, "commit", "-q", "-m", "init"], check=True)
    sha = subprocess.run(
        ["git", "-C", root, "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    return deploy_copy, sha


def _run(deploy_copy, root, args, env_overrides=None):
    env = {"PATH": os.environ.get("PATH", "")}
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        ["bash", deploy_copy] + args,
        cwd=root,
        capture_output=True,
        text=True,
        env=env,
    )


class DeployGuard(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        self.deploy_copy, self.sha = _make_repo(self.root)

    def tearDown(self):
        self._tmp.cleanup()

    def test_no_args_is_usage_error(self):
        result = _run(self.deploy_copy, self.root, [])
        self.assertEqual(result.returncode, 2)
        self.assertIn("Usage", result.stderr)

    def test_release_approval_unset_refuses(self):
        result = _run(
            self.deploy_copy, self.root, ["staging"], {"CI": "1"}
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("RELEASE_APPROVAL", result.stderr)

    def test_wrong_sha_refuses_and_names_both(self):
        result = _run(
            self.deploy_copy,
            self.root,
            ["staging"],
            {"CI": "1", "RELEASE_APPROVAL": "deadbeef"},
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("deadbeef", result.stderr)
        self.assertIn(self.sha, result.stderr)

    def test_ci_unset_refuses_with_ci_only_message(self):
        result = _run(
            self.deploy_copy, self.root, ["staging"], {"RELEASE_APPROVAL": self.sha}
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("CI only", result.stderr)

    def test_unknown_environment_lists_valid_ones(self):
        result = _run(
            self.deploy_copy,
            self.root,
            ["bogus"],
            {"CI": "1", "RELEASE_APPROVAL": self.sha},
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("development", result.stderr)
        self.assertIn("staging", result.stderr)
        self.assertIn("production", result.stderr)

    def test_production_without_github_actions_refuses(self):
        result = _run(
            self.deploy_copy,
            self.root,
            ["production"],
            {"CI": "1", "RELEASE_APPROVAL": self.sha},
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("release-manager", result.stderr)

    def test_production_with_github_actions_succeeds(self):
        result = _run(
            self.deploy_copy,
            self.root,
            ["production"],
            {"CI": "1", "GITHUB_ACTIONS": "true", "RELEASE_APPROVAL": self.sha},
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("DEPLOY: would run", result.stdout)

    def test_success_path_deploys_nothing(self):
        marker = os.path.join(self.root, "side-effect-marker")
        self.assertFalse(os.path.exists(marker))
        result = _run(
            self.deploy_copy,
            self.root,
            ["staging"],
            {"CI": "1", "RELEASE_APPROVAL": self.sha},
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("DEPLOY: would run", result.stdout)
        self.assertFalse(
            os.path.exists(marker),
            "deploy.sh must never execute the deploy command, only print it",
        )


if __name__ == "__main__":
    unittest.main()
