---
type: doc
title: Bash write-guard bypass table
description: 100-row table of Bash command shapes against the protect-paths, require-plan and protect-tests hooks at 64bcb17.
tags: [sdlc, handoff, playbook-comparison]
timestamp: 2026-09-04T22:13:40Z
---

| # | technique | protect-paths.sh (.sdlc/config.env) | require-plan.sh (src/a.ts, plan in-review) | protect-tests.sh (src/foo.test.ts, kind: fix) | command sent (protect-paths variant) |
|---|---|---|---|---|---|
| 1 | redirect > | BLOCK | BLOCK | BLOCK | `echo x > .sdlc/config.env` |
| 2 | redirect >> append | BLOCK | BLOCK | BLOCK | `echo x >> .sdlc/config.env` |
| 3 | redirect no space | BLOCK | BLOCK | BLOCK | `echo x >.sdlc/config.env` |
| 4 | clobber >| | pass | pass | pass | `echo x >\| .sdlc/config.env` |
| 5 | stderr 2> (truncates file) | pass | pass | pass | `ls /nonexistent 2> .sdlc/config.env` |
| 6 | stderr 2>> append | BLOCK | BLOCK | BLOCK | `ls /nonexistent 2>> .sdlc/config.env` |
| 7 | both &>  | pass | pass | pass | `ls /nonexistent &> .sdlc/config.env` |
| 8 | both >&  | pass | pass | pass | `ls /nonexistent >& .sdlc/config.env` |
| 9 | fd 1> | BLOCK | BLOCK | BLOCK | `echo x 1> .sdlc/config.env` |
| 10 | fd 3>  | BLOCK | BLOCK | BLOCK | `echo x 3> .sdlc/config.env` |
| 11 | heredoc cat > X <<EOF | BLOCK | BLOCK | BLOCK | `cat > .sdlc/config.env <<'EOF'\nhi\nEOF` |
| 12 | heredoc cat <<EOF > X | BLOCK | BLOCK | BLOCK | `cat <<'EOF' > .sdlc/config.env\nhi\nEOF` |
| 13 | here-string | BLOCK | BLOCK | BLOCK | `cat > .sdlc/config.env <<< hi` |
| 14 | tee | BLOCK | BLOCK | BLOCK | `echo x \| tee .sdlc/config.env` |
| 15 | tee -a | BLOCK | BLOCK | BLOCK | `echo x \| tee -a .sdlc/config.env` |
| 16 | tee -- | BLOCK | BLOCK | BLOCK | `echo x \| tee -- .sdlc/config.env` |
| 17 | cp | BLOCK | BLOCK | BLOCK | `cp /tmp/f .sdlc/config.env` |
| 18 | cp -t dir | pass | pass | pass | `cp -t .sdlc /tmp/f` |
| 19 | cp -r dir into . | pass | pass | pass | `cp -r /tmp/stage/.sdlc .` |
| 20 | mv | BLOCK | BLOCK | BLOCK | `mv /tmp/f .sdlc/config.env` |
| 21 | mv away (delete) | pass | pass | pass | `mv .sdlc/config.env /tmp/gone` |
| 22 | rm | pass | pass | pass | `rm -f .sdlc/config.env` |
| 23 | rm -rf dir | pass | pass | pass | `rm -rf .sdlc` |
| 24 | git rm | pass | pass | pass | `git rm -q .sdlc/config.env` |
| 25 | chmod -x | pass | pass | pass | `chmod -x .sdlc/config.env` |
| 26 | python3 -c open | BLOCK | BLOCK | BLOCK | `python3 -c "open('.sdlc/config.env','w').write('1')"` |
| 27 | python3 -c shutil | BLOCK | BLOCK | pass | `python3 -c "import shutil; shutil.copy('/tmp/f','.sdlc/config.env')"` |
| 28 | python3 - heredoc | BLOCK | BLOCK | BLOCK | `python3 - <<'EOF'\nopen('.sdlc/config.env','w').write('1')\nEOF` |
| 29 | python3 script.py | pass | pass | pass | `python3 /tmp/w.py` |
| 30 | node -e | pass | pass | pass | `node -e "require('fs').writeFileSync('.sdlc/config.env','1')"` |
| 31 | perl -e | BLOCK | BLOCK | BLOCK | `perl -e 'open(F,">.sdlc/config.env");print F 1'` |
| 32 | ruby -e | pass | pass | pass | `ruby -e 'File.write(".sdlc/config.env","1")'` |
| 33 | sed -i | BLOCK | BLOCK | BLOCK | `sed -i s/a/b/ .sdlc/config.env` |
| 34 | sed -i.bak | BLOCK | BLOCK | BLOCK | `sed -i.bak s/a/b/ .sdlc/config.env` |
| 35 | sed --in-place | pass | pass | pass | `sed --in-place s/a/b/ .sdlc/config.env` |
| 36 | perl -i -pe | BLOCK | BLOCK | BLOCK | `perl -i -pe s/a/b/ .sdlc/config.env` |
| 37 | perl -pi -e | pass | pass | pass | `perl -pi -e s/a/b/ .sdlc/config.env` |
| 38 | perl -pi.bak | pass | pass | pass | `perl -pi.bak -e s/a/b/ .sdlc/config.env` |
| 39 | printf > | BLOCK | BLOCK | BLOCK | `printf x > .sdlc/config.env` |
| 40 | git apply inline heredoc naming path | BLOCK | BLOCK | pass | `git apply <<'EOF'\n--- a/.sdlc/config.env\n+++ b/.sdlc/config.env\nEOF` |
| 41 | git apply /tmp/p.diff (path only in file) | pass | BLOCK | pass | `git apply /tmp/p.diff` |
| 42 | patch -p1 < /tmp/p.diff | pass | pass | pass | `patch -p1 < /tmp/p.diff` |
| 43 | dd of= | BLOCK | BLOCK | BLOCK | `dd if=/tmp/f of=.sdlc/config.env` |
| 44 | install | BLOCK | BLOCK | BLOCK | `install /tmp/f .sdlc/config.env` |
| 45 | install -t | pass | pass | pass | `install -t .sdlc /tmp/f` |
| 46 | rsync | BLOCK | BLOCK | BLOCK | `rsync /tmp/f .sdlc/config.env` |
| 47 | rsync dir/ . | pass | pass | pass | `rsync -a /tmp/stage/ .` |
| 48 | ln -s target into X | BLOCK | BLOCK | BLOCK | `ln -s /tmp/f .sdlc/config.env` |
| 49 | ln -s X elsewhere | BLOCK | BLOCK | pass | `ln -s .sdlc work/link` |
| 50 | ln hard | BLOCK | BLOCK | BLOCK | `ln /tmp/f .sdlc/config.env` |
| 51 | tar extract | pass | pass | pass | `tar xf /tmp/a.tar` |
| 52 | unzip | pass | pass | pass | `unzip -o /tmp/a.zip` |
| 53 | cmd subst $(echo cp) | pass | pass | pass | `$(echo cp) /tmp/f .sdlc/config.env` |
| 54 | cmd subst path | BLOCK | BLOCK | BLOCK | `cp /tmp/f $(echo .sdlc/config.env)` |
| 55 | variable path | pass | pass | pass | `X=.sdlc/config.env; echo hi > $X` |
| 56 | variable path braces | pass | pass | pass | `X=.sdlc/config.env; echo hi > $.sdlc/config.env` |
| 57 | $PWD prefix | pass | pass | pass | `cp /tmp/f $PWD/.sdlc/config.env` |
| 58 | tilde prefix | pass | pass | BLOCK | `cp /tmp/f ~/repo/.sdlc/config.env` |
| 59 | ; chain | pass | pass | pass | `true; cp /tmp/f .sdlc/config.env` |
| 60 | && chain | BLOCK | BLOCK | BLOCK | `true && cp /tmp/f .sdlc/config.env` |
| 61 | || chain | BLOCK | BLOCK | BLOCK | `false \|\| cp /tmp/f .sdlc/config.env` |
| 62 | subshell (cp ...) | pass | pass | pass | `(cp /tmp/f .sdlc/config.env)` |
| 63 | subshell ( cp ...) | pass | pass | pass | `( cp /tmp/f .sdlc/config.env )` |
| 64 | group { cp; } | pass | pass | pass | `{ cp /tmp/f .sdlc/config.env; }` |
| 65 | subshell redirect | BLOCK | BLOCK | BLOCK | `(echo x > .sdlc/config.env)` |
| 66 | bash -c | pass | pass | pass | `bash -c "cp /tmp/f .sdlc/config.env"` |
| 67 | bash -c redirect | BLOCK | BLOCK | BLOCK | `bash -c "echo x > .sdlc/config.env"` |
| 68 | sh -c | pass | pass | pass | `sh -c 'cp /tmp/f .sdlc/config.env'` |
| 69 | eval | pass | pass | pass | `eval "cp /tmp/f .sdlc/config.env"` |
| 70 | env VAR= cmd | BLOCK | BLOCK | BLOCK | `env A=1 cp /tmp/f .sdlc/config.env` |
| 71 | VAR=1 cmd | BLOCK | BLOCK | BLOCK | `A=1 cp /tmp/f .sdlc/config.env` |
| 72 | sudo cmd | BLOCK | BLOCK | BLOCK | `sudo cp /tmp/f .sdlc/config.env` |
| 73 | nice cmd | pass | pass | pass | `nice cp /tmp/f .sdlc/config.env` |
| 74 | command cp | BLOCK | BLOCK | BLOCK | `command cp /tmp/f .sdlc/config.env` |
| 75 | relative .. | BLOCK | BLOCK | BLOCK | `cp /tmp/f work/../.sdlc/config.env` |
| 76 | ./ prefix | BLOCK | BLOCK | BLOCK | `cp /tmp/f ./.sdlc/config.env` |
| 77 | path with space (quoted) | pass | pass | pass | `cp /tmp/f ".sdlc/my file"` |
| 78 | redirect path with space | BLOCK | BLOCK | pass | `echo x > ".sdlc/my file"` |
| 79 | single-quoted path | BLOCK | BLOCK | BLOCK | `echo x > '.sdlc/config.env'` |
| 80 | xargs | pass | pass | pass | `echo .sdlc/config.env \| xargs -I{} cp /tmp/f {}` |
| 81 | xargs tee | BLOCK | BLOCK | BLOCK | `echo hi \| xargs -I{} sh -c 'echo {} > .sdlc/config.env'` |
| 82 | find -exec | pass | pass | pass | `find /tmp -name f -exec cp {} .sdlc/config.env \;` |
| 83 | awk > file | BLOCK | BLOCK | BLOCK | `awk '{print}' /tmp/f > .sdlc/config.env` |
| 84 | sort -o | pass | pass | pass | `sort -o .sdlc/config.env /tmp/f` |
| 85 | truncate | BLOCK | BLOCK | BLOCK | `truncate -s 0 .sdlc/config.env` |
| 86 | touch new file | pass | pass | pass | `touch .sdlc/config.env` |
| 87 | mkdir | pass | pass | pass | `mkdir -p .sdlc/sub` |
| 88 | git checkout -- path | BLOCK | BLOCK | BLOCK | `git checkout HEAD~1 -- .sdlc/config.env` |
| 89 | git restore path (no --) | pass | pass | pass | `git restore --source=HEAD~1 .sdlc/config.env` |
| 90 | git checkout -- . | pass | pass | pass | `git checkout -- .` |
| 91 | git stash pop | pass | pass | pass | `git stash pop` |
| 92 | pipe no spaces | pass | pass | pass | `echo x\|tee .sdlc/config.env` |
| 93 | cd then relative (same cmd) | pass | pass | pass | `cd .sdlc && echo x > $(basename .sdlc/config.env)` |
| 94 | cd two-step (cwd in payload, relative target) | pass | pass | BLOCK | `echo x > config.env` |
| 95 | exec > | BLOCK | BLOCK | BLOCK | `exec > .sdlc/config.env` |
| 96 | cat > with tab | BLOCK | BLOCK | BLOCK | `cat >	.sdlc/config.env <<'EOF'\nhi\nEOF` |
| 97 | crlf line | BLOCK | BLOCK | BLOCK | `echo x > .sdlc/config.env\r\n` |
| 98 | newline-separated | pass | pass | pass | `true\ncp /tmp/f .sdlc/config.env` |
| 99 | backslash-newline continuation | BLOCK | BLOCK | BLOCK | `cp /tmp/f \\n .sdlc/config.env` |
| 100 | uppercase (Windows case-insens.) | pass | pass | pass | `cp /tmp/f .SDLC/config.env` |
