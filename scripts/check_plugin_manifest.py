#!/usr/bin/env python3
"""Fail when .claude-plugin/plugin.json drifts from the components it describes.

Per docs/sdlc/spikes/plugin-packaging.md (authoritative on the schema and the
default decision: the plugin ships skills, agents, commands, templates and
scripts; hooks stay repo-local, installed by `scripts/adopt.sh --with-hooks`):
the plugin root is the repo root, and because this repo keeps its components
under `.claude/skills` and `.claude/agents` (for dogfooding) rather than at
the plugin root's `skills/`/`agents/`, plugin.json must point at them
explicitly with relative `./`-prefixed paths.

Checks against .claude-plugin/plugin.json:
  - `name` present and kebab-case.
  - `version` present and valid semver (`X.Y.Z`).
  - custom component paths (`skills`, `commands`, `agents`, `hooks` when a
    string) start with `./`, stay inside the plugin root, and do not sit
    inside `.claude-plugin/` itself.
  - `skills`: a directory path (string) that resolves to `.claude/skills` and
    covers every `.claude/skills/*/SKILL.md` directory found on disk, or (if
    a list) names each such directory explicitly, one entry each way.
  - `agents`: every `.claude/agents/*.md` file is listed, and every listed
    entry exists on disk -- this is the drift-prone field since `skills` is
    one directory.
  - each `.claude/skills/<dir>/SKILL.md` front-matter `name` equals `<dir>`.
  - each `.claude/agents/<name>.md` front-matter `name` equals `<name>`.
  - any `hooks` paths referenced (a JSON file path, or `command` strings
    inside an inline hooks object) resolve to a file that exists and, for
    shell script targets, is executable.

Checks against .claude-plugin/marketplace.json:
  - `name`, `owner.name` present.
  - `plugins` is a non-empty list; each entry has `name` and `source`.
  - one `plugins[]` entry's `name` matches plugin.json's `name`.

Unknown extra keys in either file are tolerated -- only the keys above are
inspected.

Output: one `DRIFT <detail>` line per problem, then a final
`PLUGIN: <ok|N problems>` line. Exit 1 if any problem was found, 0 otherwise.
"""
import argparse
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_artifact_chain as cac  # noqa: E402  (reuses front_matter())

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
PLUGIN_ROOT_VAR_RE = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}")
SCRIPT_EXTENSIONS = (".sh", ".py", ".js", ".mjs", ".ts")


def repo_root():
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except OSError:
        pass
    return os.getcwd()


def load_json(path):
    """Return (value, error). error is None on success; a string otherwise.
    A missing file is reported as an error, never a silent None."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f), None
    except FileNotFoundError:
        return None, f"{path} does not exist"
    except json.JSONDecodeError as e:
        return None, f"{path} is not valid JSON: {e}"


def skill_dirs(root):
    """Sorted directory names under .claude/skills/ that contain SKILL.md."""
    base = os.path.join(root, ".claude", "skills")
    out = []
    if os.path.isdir(base):
        for name in sorted(os.listdir(base)):
            d = os.path.join(base, name)
            if os.path.isdir(d) and os.path.isfile(os.path.join(d, "SKILL.md")):
                out.append(name)
    return out


def agent_files(root):
    """Sorted *.md filenames directly under .claude/agents/."""
    base = os.path.join(root, ".claude", "agents")
    out = []
    if os.path.isdir(base):
        for name in sorted(os.listdir(base)):
            if name.endswith(".md") and os.path.isfile(os.path.join(base, name)):
                out.append(name)
    return out


def last_path_segment(p):
    return p.rstrip("/").split("/")[-1]


def resolve_under(root, rel):
    return os.path.normpath(os.path.join(root, rel))


def path_safety_problems(rel, field, root):
    """Return a list of problem strings for a `./`-relative component path."""
    problems = []
    if not isinstance(rel, str):
        return [f"plugin.json {field} entry {rel!r} is not a string"]
    if not rel.startswith("./"):
        problems.append(f"plugin.json {field} path {rel!r} must start with './'")
        return problems  # nothing safe to resolve further
    resolved = resolve_under(root, rel)
    if resolved != root and not resolved.startswith(root + os.sep):
        problems.append(f"plugin.json {field} path {rel!r} escapes the plugin root")
        return problems
    plugin_dir = os.path.join(root, ".claude-plugin")
    if resolved == plugin_dir or resolved.startswith(plugin_dir + os.sep):
        problems.append(f"plugin.json {field} path {rel!r} must not sit inside .claude-plugin/")
    return problems


def check_skills(plugin, root, real_dirs):
    problems = []
    field = plugin.get("skills")
    if field is None:
        problems.append("plugin.json: skills field is missing")
        return problems

    if isinstance(field, str):
        problems += path_safety_problems(field, "skills", root)
        resolved = resolve_under(root, field)
        expected = os.path.join(root, ".claude", "skills")
        if os.path.isdir(resolved) and os.path.normpath(resolved) != os.path.normpath(expected):
            problems.append(f"plugin.json skills path {field!r} does not point at .claude/skills")
        elif not os.path.isdir(resolved):
            problems.append(f"plugin.json skills path {field!r} does not exist")
    elif isinstance(field, list):
        listed = set()
        for entry in field:
            problems += path_safety_problems(entry, "skills", root)
            if isinstance(entry, str):
                name = last_path_segment(entry)
                listed.add(name)
                resolved = resolve_under(root, entry)
                if not os.path.isfile(os.path.join(resolved, "SKILL.md")):
                    problems.append(
                        f"plugin.json skills entry {entry!r} has no SKILL.md"
                    )
        for d in real_dirs:
            if d not in listed:
                problems.append(
                    f"skill directory .claude/skills/{d} (has SKILL.md) is not listed under plugin.json skills"
                )
    else:
        problems.append("plugin.json: skills must be a string directory path or a list of paths")
    return problems


def check_agents(plugin, root, real_files):
    problems = []
    field = plugin.get("agents")
    if not isinstance(field, list):
        problems.append("plugin.json: agents must be a list of './.claude/agents/<name>.md' paths")
        field = []

    listed_names = []
    for entry in field:
        problems += path_safety_problems(entry, "agents", root)
        if not isinstance(entry, str):
            continue
        resolved = resolve_under(root, entry)
        name = os.path.basename(resolved)
        if not os.path.isfile(resolved):
            problems.append(f"plugin.json agents entry {entry!r} does not exist")
        else:
            listed_names.append(name)

    for name in real_files:
        if name not in listed_names:
            problems.append(
                f"agent file .claude/agents/{name} is not listed under plugin.json agents"
            )
    for name in listed_names:
        if name not in real_files:
            problems.append(
                f"plugin.json agents lists .claude/agents/{name} which does not exist as a real agent file"
            )
    return problems


def check_skill_names(root, real_dirs):
    problems = []
    for d in real_dirs:
        skill_path = os.path.join(root, ".claude", "skills", d, "SKILL.md")
        fm = cac.front_matter(skill_path) or {}
        name = fm.get("name")
        if name != d:
            problems.append(
                f"{skill_path}: front-matter name {name!r} does not equal its directory name {d!r}"
            )
    return problems


def check_agent_names(root, real_files):
    problems = []
    for filename in real_files:
        agent_path = os.path.join(root, ".claude", "agents", filename)
        stem = filename[: -len(".md")]
        fm = cac.front_matter(agent_path) or {}
        name = fm.get("name")
        if name != stem:
            problems.append(
                f"{agent_path}: front-matter name {name!r} does not equal its filename stem {stem!r}"
            )
    return problems


def _extract_hook_commands(obj):
    """Walk a decoded hooks object/list and return every string found under a
    `command` key."""
    commands = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "command" and isinstance(v, str):
                commands.append(v)
            else:
                commands.extend(_extract_hook_commands(v))
    elif isinstance(obj, list):
        for item in obj:
            commands.extend(_extract_hook_commands(item))
    return commands


def _command_to_relpath(command):
    """Best-effort extraction of a script path from a hook command string
    like `"${CLAUDE_PLUGIN_ROOT}"/.claude/hooks/foo.sh` or a bare path."""
    s = PLUGIN_ROOT_VAR_RE.sub("", command)
    s = s.replace('"', "").replace("'", "").strip()
    if not s:
        return None
    token = s.split()[0]
    return token.lstrip("/")


def check_hooks(plugin, root):
    problems = []
    field = plugin.get("hooks")
    if field is None:
        return problems

    if isinstance(field, str):
        problems += path_safety_problems(field, "hooks", root)
        resolved = resolve_under(root, field)
        if not os.path.isfile(resolved):
            problems.append(f"plugin.json hooks path {field!r} does not exist")
            return problems
        obj, err = load_json(resolved)
        if err:
            problems.append(f"plugin.json hooks file {field!r}: {err}")
            return problems
    elif isinstance(field, dict):
        obj = field
    else:
        problems.append("plugin.json: hooks must be a string path or an inline object")
        return problems

    for command in _extract_hook_commands(obj):
        rel = _command_to_relpath(command)
        if not rel:
            continue
        resolved = resolve_under(root, rel)
        if not os.path.isfile(resolved):
            problems.append(f"hooks command references {rel!r}, which does not exist")
            continue
        if resolved.endswith(SCRIPT_EXTENSIONS) and not os.access(resolved, os.X_OK):
            problems.append(f"hooks command references {rel!r}, which is not executable")
    return problems


def check_marketplace(root, plugin):
    problems = []
    path = os.path.join(root, ".claude-plugin", "marketplace.json")
    marketplace, err = load_json(path)
    if err:
        return [err]

    name = marketplace.get("name")
    if not name:
        problems.append(f"{path}: name is required")

    owner = marketplace.get("owner")
    if not isinstance(owner, dict) or not owner.get("name"):
        problems.append(f"{path}: owner.name is required")

    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        problems.append(f"{path}: plugins must be a non-empty list")
        plugins = []

    plugin_names = []
    for i, entry in enumerate(plugins):
        if not isinstance(entry, dict):
            problems.append(f"{path}: plugins[{i}] is not an object")
            continue
        if not entry.get("name"):
            problems.append(f"{path}: plugins[{i}] is missing name")
        else:
            plugin_names.append(entry["name"])
        if not entry.get("source"):
            problems.append(f"{path}: plugins[{i}] is missing source")

    plugin_name = plugin.get("name") if isinstance(plugin, dict) else None
    if plugin_name and plugin_names and plugin_name not in plugin_names:
        problems.append(
            f"{path}: no plugins[] entry named {plugin_name!r} (plugin.json name); found {plugin_names}"
        )
    return problems


def check(root):
    problems = []
    plugin_path = os.path.join(root, ".claude-plugin", "plugin.json")
    plugin, err = load_json(plugin_path)
    if err:
        problems.append(err)
        plugin = None

    if plugin is not None:
        if not isinstance(plugin, dict):
            problems.append(f"{plugin_path}: top level must be a JSON object")
            plugin = {}

        name = plugin.get("name")
        if not name:
            problems.append(f"{plugin_path}: name is required")
        elif not KEBAB_RE.match(name):
            problems.append(f"{plugin_path}: name {name!r} is not kebab-case")

        version = plugin.get("version")
        if not version:
            problems.append(f"{plugin_path}: version is required")
        elif not SEMVER_RE.match(str(version)):
            problems.append(f"{plugin_path}: version {version!r} is not valid semver (X.Y.Z)")

        real_skill_dirs = skill_dirs(root)
        real_agent_files = agent_files(root)

        problems += check_skills(plugin, root, real_skill_dirs)
        problems += check_agents(plugin, root, real_agent_files)
        problems += check_skill_names(root, real_skill_dirs)
        problems += check_agent_names(root, real_agent_files)
        problems += check_hooks(plugin, root)
        problems += check_marketplace(root, plugin)
    else:
        # Still check marketplace on its own so a broken plugin.json doesn't
        # hide a broken marketplace.json.
        problems += check_marketplace(root, {})

    return problems


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", help="repo root (default: git toplevel, else cwd)")
    return ap.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    root = os.path.abspath(args.root) if args.root else repo_root()

    problems = check(root)
    for detail in problems:
        print(f"DRIFT {detail}")

    status = "ok" if not problems else f"{len(problems)} problems"
    print(f"PLUGIN: {status}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
