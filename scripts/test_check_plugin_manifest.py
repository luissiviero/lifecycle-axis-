import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
CHECK = os.path.join(HERE, "check_plugin_manifest.py")

SKILL_MD = "---\nname: {name}\ndescription: d\n---\nbody\n"
AGENT_MD = "---\nname: {name}\ndescription: d\ntools: Read\n---\nbody\n"


def _write(root, rel, content):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def _run(root):
    return subprocess.run(
        [sys.executable, CHECK, "--root", root],
        capture_output=True,
        text=True,
    )


def _last_line(text):
    lines = [l for l in text.splitlines() if l.strip()]
    return lines[-1] if lines else ""


def _default_plugin(**overrides):
    plugin = {
        "name": "sample-plugin",
        "version": "0.1.0",
        "description": "d",
        "skills": "./.claude/skills",
        "agents": [
            "./.claude/agents/foo.md",
            "./.claude/agents/bar.md",
        ],
    }
    plugin.update(overrides)
    return plugin


def _default_marketplace(**overrides):
    marketplace = {
        "name": "sample-marketplace",
        "owner": {"name": "someone"},
        "plugins": [
            {"name": "sample-plugin", "source": "./", "description": "d", "version": "0.1.0"}
        ],
    }
    marketplace.update(overrides)
    return marketplace


def _make_tree(root, plugin=None, marketplace=None, skills=("foo", "bar"), agents=("foo", "bar")):
    """A minimal matching tree: two skills, two agents, a plugin.json listing
    both, and a marketplace.json naming the same plugin."""
    for name in skills:
        _write(root, f".claude/skills/{name}/SKILL.md", SKILL_MD.format(name=name))
    for name in agents:
        _write(root, f".claude/agents/{name}.md", AGENT_MD.format(name=name))
    _write(
        root,
        ".claude-plugin/plugin.json",
        json.dumps(plugin if plugin is not None else _default_plugin(), indent=2),
    )
    _write(
        root,
        ".claude-plugin/marketplace.json",
        json.dumps(marketplace if marketplace is not None else _default_marketplace(), indent=2),
    )


class MatchingManifest(unittest.TestCase):
    def test_matching_tree_passes(self):
        with tempfile.TemporaryDirectory() as root:
            _make_tree(root)
            result = _run(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(_last_line(result.stdout), "PLUGIN: ok")
            self.assertNotIn("DRIFT", result.stdout)


class RealRepo(unittest.TestCase):
    def test_real_repo_passes(self):
        result = _run(REPO_ROOT)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(_last_line(result.stdout), "PLUGIN: ok")


class SkillDirMissingFromManifest(unittest.TestCase):
    def test_skill_dir_not_listed_is_one_problem(self):
        with tempfile.TemporaryDirectory() as root:
            # skills is a list form; add a third skill dir without listing it.
            plugin = _default_plugin(
                skills=[
                    "./.claude/skills/foo",
                    "./.claude/skills/bar",
                ]
            )
            _make_tree(root, plugin=plugin, skills=("foo", "bar"))
            _write(root, ".claude/skills/baz/SKILL.md", SKILL_MD.format(name="baz"))
            result = _run(root)
            self.assertEqual(result.returncode, 1)
            drift_lines = [l for l in result.stdout.splitlines() if l.startswith("DRIFT")]
            self.assertEqual(len(drift_lines), 1, result.stdout)
            self.assertIn(".claude/skills/baz", drift_lines[0])
            self.assertEqual(_last_line(result.stdout), "PLUGIN: 1 problems")


class NonexistentAgentListed(unittest.TestCase):
    def test_agent_entry_that_does_not_exist_is_one_problem(self):
        with tempfile.TemporaryDirectory() as root:
            plugin = _default_plugin(
                agents=[
                    "./.claude/agents/foo.md",
                    "./.claude/agents/bar.md",
                    "./.claude/agents/ghost.md",
                ]
            )
            _make_tree(root, plugin=plugin)
            result = _run(root)
            self.assertEqual(result.returncode, 1)
            drift_lines = [l for l in result.stdout.splitlines() if l.startswith("DRIFT")]
            self.assertEqual(len(drift_lines), 1, result.stdout)
            self.assertIn("ghost.md", drift_lines[0])
            self.assertIn("does not exist", drift_lines[0])


class SkillNameDirMismatch(unittest.TestCase):
    def test_skill_front_matter_name_mismatch_is_one_problem(self):
        with tempfile.TemporaryDirectory() as root:
            _make_tree(root)
            # Overwrite foo/SKILL.md with a name that doesn't match its directory.
            _write(root, ".claude/skills/foo/SKILL.md", SKILL_MD.format(name="not-foo"))
            result = _run(root)
            self.assertEqual(result.returncode, 1)
            drift_lines = [l for l in result.stdout.splitlines() if l.startswith("DRIFT")]
            self.assertEqual(len(drift_lines), 1, result.stdout)
            self.assertIn("foo/SKILL.md", drift_lines[0])
            self.assertIn("not-foo", drift_lines[0])


class BadSemver(unittest.TestCase):
    def test_non_semver_version_is_one_problem(self):
        with tempfile.TemporaryDirectory() as root:
            plugin = _default_plugin(version="v1")
            _make_tree(root, plugin=plugin)
            result = _run(root)
            self.assertEqual(result.returncode, 1)
            drift_lines = [l for l in result.stdout.splitlines() if l.startswith("DRIFT")]
            self.assertEqual(len(drift_lines), 1, result.stdout)
            self.assertIn("semver", drift_lines[0])


class MarketplaceNameMismatch(unittest.TestCase):
    def test_marketplace_plugin_name_mismatch_is_one_problem(self):
        with tempfile.TemporaryDirectory() as root:
            marketplace = _default_marketplace(
                plugins=[{"name": "some-other-plugin", "source": "./", "version": "0.1.0"}]
            )
            _make_tree(root, marketplace=marketplace)
            result = _run(root)
            self.assertEqual(result.returncode, 1)
            drift_lines = [l for l in result.stdout.splitlines() if l.startswith("DRIFT")]
            self.assertEqual(len(drift_lines), 1, result.stdout)
            self.assertIn("marketplace.json", drift_lines[0])
            self.assertIn("sample-plugin", drift_lines[0])


class AgentNameStemMismatch(unittest.TestCase):
    def test_agent_front_matter_name_mismatch_is_one_problem(self):
        with tempfile.TemporaryDirectory() as root:
            _make_tree(root)
            _write(root, ".claude/agents/foo.md", AGENT_MD.format(name="not-foo"))
            result = _run(root)
            self.assertEqual(result.returncode, 1)
            drift_lines = [l for l in result.stdout.splitlines() if l.startswith("DRIFT")]
            self.assertEqual(len(drift_lines), 1, result.stdout)
            self.assertIn("foo.md", drift_lines[0])


class MissingManifest(unittest.TestCase):
    def test_missing_plugin_json_is_reported(self):
        with tempfile.TemporaryDirectory() as root:
            _write(
                root,
                ".claude-plugin/marketplace.json",
                json.dumps(_default_marketplace(), indent=2),
            )
            result = _run(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("plugin.json", result.stdout)
            self.assertNotEqual(_last_line(result.stdout), "PLUGIN: ok")


class HooksPathsCheck(unittest.TestCase):
    def test_hooks_command_referencing_missing_script_is_a_problem(self):
        with tempfile.TemporaryDirectory() as root:
            plugin = _default_plugin(
                hooks={
                    "PreToolUse": [
                        {
                            "matcher": "Edit",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": '"${CLAUDE_PLUGIN_ROOT}"/.claude/hooks/does-not-exist.sh',
                                }
                            ],
                        }
                    ]
                }
            )
            _make_tree(root, plugin=plugin)
            result = _run(root)
            self.assertEqual(result.returncode, 1)
            drift_lines = [l for l in result.stdout.splitlines() if l.startswith("DRIFT")]
            self.assertTrue(
                any("does-not-exist.sh" in l for l in drift_lines), result.stdout
            )

    def test_hooks_command_referencing_non_executable_script_is_a_problem(self):
        with tempfile.TemporaryDirectory() as root:
            plugin = _default_plugin(
                hooks={
                    "PreToolUse": [
                        {
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": '"${CLAUDE_PLUGIN_ROOT}"/.claude/hooks/nonexec.sh',
                                }
                            ]
                        }
                    ]
                }
            )
            _make_tree(root, plugin=plugin)
            hook_path = _write(root, ".claude/hooks/nonexec.sh", "#!/usr/bin/env bash\nexit 0\n")
            os.chmod(hook_path, 0o644)
            result = _run(root)
            self.assertEqual(result.returncode, 1)
            drift_lines = [l for l in result.stdout.splitlines() if l.startswith("DRIFT")]
            self.assertTrue(
                any("not executable" in l for l in drift_lines), result.stdout
            )

    def test_hooks_command_referencing_executable_script_passes(self):
        with tempfile.TemporaryDirectory() as root:
            plugin = _default_plugin(
                hooks={
                    "PreToolUse": [
                        {
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": '"${CLAUDE_PLUGIN_ROOT}"/.claude/hooks/ok.sh',
                                }
                            ]
                        }
                    ]
                }
            )
            _make_tree(root, plugin=plugin)
            hook_path = _write(root, ".claude/hooks/ok.sh", "#!/usr/bin/env bash\nexit 0\n")
            os.chmod(hook_path, 0o755)
            result = _run(root)
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertEqual(_last_line(result.stdout), "PLUGIN: ok")


if __name__ == "__main__":
    unittest.main()
