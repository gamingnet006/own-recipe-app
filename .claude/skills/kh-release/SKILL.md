---
name: kh-release
description: Publishes a Küchenhelfer release and brings the Mac mini to it, step by step with checks. Only on the user's explicit request to release ("veröffentlichen").
disable-model-invocation: true
argument-hint: <version, e.g. v0.3>
---

Publish Küchenhelfer $ARGUMENTS. Releases happen only after the user explicitly said so; stop and ask if that is not clear.

1. **Main is ready.** `git checkout main`, clean tree, in sync with origin. The CHANGELOG (`docs/kh/CHANGELOG.md`) has a `## [$ARGUMENTS] - <today>` section instead of `[Unreleased]`, and `PLAN.md` ticks what the release delivers.
2. **Formatting like the CI.** `uvx ruff@<version from uv.lock> format . --check` passes; it also reads Python blocks in Markdown. Fix, commit and push before going on.
3. **CI green on main.** Wait for the KH CI run of main's head with `gh run watch <id> --exit-status` in the background; never release on red.
4. **Release.** `kh/ops/release.sh $ARGUMENTS` (builds arm64 here, tags, pushes). Then wait for the `kh-release.yml` run of the tag (amd64 build and upgrade test) to be green.
5. **Mac mini.** It has no git checkout; its automatic update takes stable releases at 4:00 and installs the ops files shipped in the new image. To update now, over Tailscale SSH (`ssh admin@mac-mini`, folder `~/homelab/kuechenhelfer`): `kh/ops/auto_update.sh check`, then `kh/ops/auto_update.sh run`, and read `kh/ops/auto_update.log`. Confirm https://kochbuch.example.org answers and the container runs `ghcr.io/gamingnet006/own-recipe-app:$ARGUMENTS-amd64`.
6. **Release extras.** Do what the release notes or the CHANGELOG say must happen on the mini (desktop links, notes files), and update the desktop start script if start or stop steps changed.
7. **Report.** Version, tag, image names, what the mini runs now, and anything left open.

Never put credentials anywhere, never use sudo, and never enter the user's passwords; ask the user for steps that need them.
