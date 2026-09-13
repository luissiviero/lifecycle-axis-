---
type: doc
title: "Evidence: delegated-merge workflow runs"
description: "The newest 100 completed runs of .github/workflows/delegated-merge.yml as returned by the GitHub Actions API on 2026-09-10, with their conclusions; the source of finding 1 in the step review."
tags: [sdlc, revision, evidence, actions]
timestamp: 2026-09-10T16:30:00Z
---
# Evidence: delegated-merge workflow runs

Queried on 2026-09-10 through the GitHub Actions API (`GET /repos/luissiviero/lifecycle-axis-/actions/workflows/delegated-merge.yml/runs?status=completed&per_page=100`).
The workflow had 215 runs in total at query time; this is the newest 100 completed.

| Conclusion | Runs |
|---|---|
| success | 8 |
| failure | 38 |
| skipped | 54 |

Every run's `event` is `workflow_run` and every `head_branch` is `main`, as the workflow is designed.
The eight successful runs all follow an approval-tap commit or a merge commit on `main`, not a delegated merge of a pull request;
`git log origin/main --grep='Advance .sdlc/active'` returns nothing, so no advance commit has ever landed.

| Run id | Created (UTC) | Conclusion | Head sha | Head commit subject |
|---|---|---|---|---|
| 34469147943 | 2026-09-10T11:02:01Z | failure | ca8dd32 | Merge pull request #64 from luissiviero/claude/pr-63-plan-review-ekiuva |
| 34469110654 | 2026-09-10T11:01:37Z | skipped | ca8dd32 | Merge pull request #64 from luissiviero/claude/pr-63-plan-review-ekiuva |
| 34456838339 | 2026-09-10T08:44:56Z | failure | ca8dd32 | Merge pull request #64 from luissiviero/claude/pr-63-plan-review-ekiuva |
| 34453891485 | 2026-09-10T08:12:10Z | failure | ca8dd32 | Merge pull request #64 from luissiviero/claude/pr-63-plan-review-ekiuva |
| 34453686220 | 2026-09-10T08:09:51Z | skipped | ca8dd32 | Merge pull request #64 from luissiviero/claude/pr-63-plan-review-ekiuva |
| 34453645753 | 2026-09-10T08:09:22Z | failure | 0e9d160 | [ci-budget] Approve intent.md as luissiviero |
| 34453591221 | 2026-09-10T08:08:45Z | skipped | 0e9d160 | [ci-budget] Approve intent.md as luissiviero |
| 34447193354 | 2026-09-10T06:52:23Z | skipped | 894e11c | Change status to superseded and mode to supervised |
| 34376612824 | 2026-09-09T16:25:18Z | skipped | 894e11c | Change status to superseded and mode to supervised |
| 34376548977 | 2026-09-09T16:24:41Z | failure | 894e11c | Change status to superseded and mode to supervised |
| 34376542970 | 2026-09-09T16:24:38Z | failure | 894e11c | Change status to superseded and mode to supervised |
| 34376540865 | 2026-09-09T16:24:37Z | skipped | 894e11c | Change status to superseded and mode to supervised |
| 34376536457 | 2026-09-09T16:24:35Z | skipped | 894e11c | Change status to superseded and mode to supervised |
| 34376526157 | 2026-09-09T16:24:29Z | skipped | 894e11c | Change status to superseded and mode to supervised |
| 34376017243 | 2026-09-09T16:19:41Z | skipped | 894e11c | Change status to superseded and mode to supervised |
| 34375664697 | 2026-09-09T16:16:21Z | skipped | 894e11c | Change status to superseded and mode to supervised |
| 34373232560 | 2026-09-09T15:53:39Z | failure | bce2a43 | Merge pull request #63 from luissiviero/claude/github-scheduled-task-emails-96b6 |
| 34372925210 | 2026-09-09T15:50:50Z | skipped | bce2a43 | Merge pull request #63 from luissiviero/claude/github-scheduled-task-emails-96b6 |
| 34371488399 | 2026-09-09T15:37:47Z | failure | 308f1a2 | Replace 'run-queue-followups' with 'ci-budget' |
| 34371444813 | 2026-09-09T15:37:22Z | failure | 308f1a2 | Replace 'run-queue-followups' with 'ci-budget' |
| 34371404731 | 2026-09-09T15:37:00Z | skipped | 308f1a2 | Replace 'run-queue-followups' with 'ci-budget' |
| 34368328583 | 2026-09-09T15:09:01Z | skipped | 4fa4f7a | Merge pull request #58 from luissiviero/claude/sdlc-queue-pointer-checks-m2yh7y |
| 34368131471 | 2026-09-09T15:07:11Z | failure | 4fa4f7a | Merge pull request #58 from luissiviero/claude/sdlc-queue-pointer-checks-m2yh7y |
| 34368067971 | 2026-09-09T15:06:37Z | skipped | 4fa4f7a | Merge pull request #58 from luissiviero/claude/sdlc-queue-pointer-checks-m2yh7y |
| 34367819113 | 2026-09-09T15:04:23Z | skipped | 4fa4f7a | Merge pull request #58 from luissiviero/claude/sdlc-queue-pointer-checks-m2yh7y |
| 34352116586 | 2026-09-09T12:37:37Z | failure | 4fa4f7a | Merge pull request #58 from luissiviero/claude/sdlc-queue-pointer-checks-m2yh7y |
| 34352099801 | 2026-09-09T12:37:26Z | failure | 4fa4f7a | Merge pull request #58 from luissiviero/claude/sdlc-queue-pointer-checks-m2yh7y |
| 34352053587 | 2026-09-09T12:36:59Z | skipped | 4fa4f7a | Merge pull request #58 from luissiviero/claude/sdlc-queue-pointer-checks-m2yh7y |
| 34333839946 | 2026-09-09T09:17:08Z | skipped | 4fa4f7a | Merge pull request #58 from luissiviero/claude/sdlc-queue-pointer-checks-m2yh7y |
| 34333833695 | 2026-09-09T09:17:04Z | skipped | 4fa4f7a | Merge pull request #58 from luissiviero/claude/sdlc-queue-pointer-checks-m2yh7y |
| 34320826686 | 2026-09-09T06:49:26Z | skipped | 4fa4f7a | Merge pull request #58 from luissiviero/claude/sdlc-queue-pointer-checks-m2yh7y |
| 34288302687 | 2026-09-08T22:56:02Z | skipped | 4fa4f7a | Merge pull request #58 from luissiviero/claude/sdlc-queue-pointer-checks-m2yh7y |
| 34288301744 | 2026-09-08T22:56:01Z | skipped | 4fa4f7a | Merge pull request #58 from luissiviero/claude/sdlc-queue-pointer-checks-m2yh7y |
| 34287339907 | 2026-09-08T22:43:45Z | skipped | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34287306453 | 2026-09-08T22:43:19Z | skipped | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34287306868 | 2026-09-08T22:43:19Z | skipped | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34285082457 | 2026-09-08T22:16:53Z | skipped | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34285081585 | 2026-09-08T22:16:52Z | skipped | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34282120737 | 2026-09-08T21:43:02Z | skipped | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34281904096 | 2026-09-08T21:40:33Z | skipped | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34281836722 | 2026-09-08T21:39:50Z | skipped | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34281763572 | 2026-09-08T21:39:00Z | failure | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34281694921 | 2026-09-08T21:38:16Z | failure | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34281667947 | 2026-09-08T21:37:56Z | skipped | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34281663957 | 2026-09-08T21:37:53Z | skipped | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34281661761 | 2026-09-08T21:37:52Z | skipped | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34281659677 | 2026-09-08T21:37:50Z | failure | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34281546275 | 2026-09-08T21:36:34Z | skipped | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34281542997 | 2026-09-08T21:36:32Z | skipped | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34281528706 | 2026-09-08T21:36:22Z | skipped | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34279662447 | 2026-09-08T21:16:30Z | failure | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34279644926 | 2026-09-08T21:16:20Z | skipped | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34279621541 | 2026-09-08T21:16:05Z | failure | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34279597847 | 2026-09-08T21:15:50Z | skipped | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34279574041 | 2026-09-08T21:15:35Z | failure | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34279557407 | 2026-09-08T21:15:24Z | skipped | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34279357932 | 2026-09-08T21:13:23Z | skipped | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34279351201 | 2026-09-08T21:13:18Z | skipped | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34279348446 | 2026-09-08T21:13:17Z | skipped | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34269456656 | 2026-09-08T19:31:26Z | failure | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34269355070 | 2026-09-08T19:30:25Z | success | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34269323846 | 2026-09-08T19:30:07Z | failure | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34269169619 | 2026-09-08T19:28:28Z | success | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34269114044 | 2026-09-08T19:27:56Z | skipped | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34269109340 | 2026-09-08T19:27:53Z | success | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34269064062 | 2026-09-08T19:27:25Z | failure | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34269051509 | 2026-09-08T19:27:19Z | failure | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34269015472 | 2026-09-08T19:26:58Z | skipped | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34268994709 | 2026-09-08T19:26:44Z | success | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34268966474 | 2026-09-08T19:26:26Z | skipped | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34268775947 | 2026-09-08T19:24:30Z | failure | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34268723366 | 2026-09-08T19:23:59Z | failure | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34268700082 | 2026-09-08T19:23:44Z | skipped | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34267796280 | 2026-09-08T19:14:29Z | failure | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34267714717 | 2026-09-08T19:13:40Z | skipped | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34266902606 | 2026-09-08T19:05:21Z | failure | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34266829772 | 2026-09-08T19:04:37Z | skipped | c0aa58c | [run-queue-followups] Approve intent.md as luissiviero |
| 34265540190 | 2026-09-08T18:51:36Z | failure | a83c8e4 | Merge pull request #57 from luissiviero/claude/delegate-mode-next-steps-szrg8d |
| 34265475809 | 2026-09-08T18:50:57Z | failure | a83c8e4 | Merge pull request #57 from luissiviero/claude/delegate-mode-next-steps-szrg8d |
| 34265405578 | 2026-09-08T18:50:14Z | failure | a83c8e4 | Merge pull request #57 from luissiviero/claude/delegate-mode-next-steps-szrg8d |
| 34265346671 | 2026-09-08T18:49:39Z | skipped | a83c8e4 | Merge pull request #57 from luissiviero/claude/delegate-mode-next-steps-szrg8d |
| 34265160473 | 2026-09-08T18:47:45Z | failure | a83c8e4 | Merge pull request #57 from luissiviero/claude/delegate-mode-next-steps-szrg8d |
| 34264852510 | 2026-09-08T18:44:38Z | failure | a83c8e4 | Merge pull request #57 from luissiviero/claude/delegate-mode-next-steps-szrg8d |
| 34264793724 | 2026-09-08T18:44:04Z | failure | a83c8e4 | Merge pull request #57 from luissiviero/claude/delegate-mode-next-steps-szrg8d |
| 34264747470 | 2026-09-08T18:43:35Z | skipped | a83c8e4 | Merge pull request #57 from luissiviero/claude/delegate-mode-next-steps-szrg8d |
| 34263633667 | 2026-09-08T18:32:25Z | failure | a83c8e4 | Merge pull request #57 from luissiviero/claude/delegate-mode-next-steps-szrg8d |
| 34263003328 | 2026-09-08T18:26:03Z | success | 44cac9d | Merge pull request #55 from luissiviero/claude/delegate-mode-next-steps-szrg8d |
| 34262966006 | 2026-09-08T18:25:40Z | success | 44cac9d | Merge pull request #55 from luissiviero/claude/delegate-mode-next-steps-szrg8d |
| 34262960167 | 2026-09-08T18:25:36Z | skipped | 44cac9d | Merge pull request #55 from luissiviero/claude/delegate-mode-next-steps-szrg8d |
| 34262578195 | 2026-09-08T18:21:46Z | failure | 44cac9d | Merge pull request #55 from luissiviero/claude/delegate-mode-next-steps-szrg8d |
| 34262399269 | 2026-09-08T18:19:58Z | skipped | 44cac9d | Merge pull request #55 from luissiviero/claude/delegate-mode-next-steps-szrg8d |
| 34260577250 | 2026-09-08T18:01:35Z | failure | 44cac9d | Merge pull request #55 from luissiviero/claude/delegate-mode-next-steps-szrg8d |
| 34260509952 | 2026-09-08T18:00:54Z | skipped | 44cac9d | Merge pull request #55 from luissiviero/claude/delegate-mode-next-steps-szrg8d |
| 34258713505 | 2026-09-08T17:42:29Z | failure | 44cac9d | Merge pull request #55 from luissiviero/claude/delegate-mode-next-steps-szrg8d |
| 34258351372 | 2026-09-08T17:38:43Z | failure | 44cac9d | Merge pull request #55 from luissiviero/claude/delegate-mode-next-steps-szrg8d |
| 34257711878 | 2026-09-08T17:32:25Z | success | 3da8bb6 | [run-queue] Approve intent.md as luissiviero |
| 34257650956 | 2026-09-08T17:31:49Z | skipped | 3da8bb6 | [run-queue] Approve intent.md as luissiviero |
| 34257650778 | 2026-09-08T17:31:49Z | success | 3da8bb6 | [run-queue] Approve intent.md as luissiviero |
| 34257563925 | 2026-09-08T17:30:58Z | skipped | 3da8bb6 | [run-queue] Approve intent.md as luissiviero |
| 34257563217 | 2026-09-08T17:30:57Z | failure | 3da8bb6 | [run-queue] Approve intent.md as luissiviero |
