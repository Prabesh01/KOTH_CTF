# KOTH_CTF -> netkoth.org-format conversion

## Why the reporter isn't inside the vulnbox

An earlier version of this patch ran the tag reporter as a background
process inside each vulnbox itself. That has a critical flaw: whoever
controls the box also has root over that same reporter process. A team
could kill it, replace it with one that hardcodes their own token
regardless of what `/opt/koth/tag` actually contains, and score forever
even after losing real control -- or never having control validated at
all. Same underlying problem as a spoofable `/health` endpoint in an
A/D checker: **never trust a self-report from inside the exact
trust boundary you're trying to measure.**

The fix is architectural, not a smarter check: the reporter now runs in
a separate `*-reporter` sidecar container per machine, sharing a Docker
named volume (`<machine>_koth_tag`) with its vulnbox at `/opt/koth`. The
vulnbox can still write `/opt/koth/tag` through it -- that's the actual
game, unchanged. But the sidecar:

- Has no exploitable surface at all (nothing installed but Python and
  the reporter script itself -- no SSH, no web app, nothing a player
  could ever get code execution into).
- Is a completely separate container/process/filesystem from the
  vulnbox, so gaining root on the vulnbox gives zero access to the
  sidecar.
- Is the ONLY thing `scorebot/machines.json` points at (`172.20.1.x`,
  not the vulnbox's own `172.20.0.x` address) -- ScoreBot never asks
  the vulnbox about itself.

So a team can still legitimately overwrite the tag (writing to a shared
volume is exactly the intended mechanic), but they can never lie about
what it currently contains, because the only thing capable of reporting
that lives somewhere they can't reach.

## What changed and why (scoring model itself)

The original repo had a real leaderboard (`scoreboard/app.py`), but it
scored **static, one-time flag capture** per individual player -- solve a
flag once, get fixed points forever, no team concept, nothing that
rewards *holding* a machine over time or *defending* it once you have it.
That's jeopardy scoring, not King of the Hill, regardless of the name.

This patch replaces that with the actual netkoth.org mechanic: an
always-on **tag reporter** on every machine, a **ScoreBot** that polls all
of them on a fixed interval, and a **team-based scoreboard** that credits
whoever currently holds each machine, continuously, automatically.

Nothing about the vulnerable machines themselves changed -- same bugs,
same Dockerfiles, same privesc chains. Only the *scoring layer* changed,
which is the whole point: this repo's actual strength (self-contained,
easy-to-author vulnerable machines) is untouched; what it lacked was hold-
based scoring, and that's now bolted on cleanly.

## What "defending" means here

There's no separate defender role or defender score -- see the earlier
critical-analysis discussion: holding *is* scoring. Once your team's
token is in `/opt/koth/tag` on a machine, every poll interval you still
hold it, you accrue that machine's points, automatically, with zero
action required. "Defense" is whatever you do to keep someone else from
overwriting that file via the same vulnerability you used to write it --
patch the vuln, harden creds, whatever. There's no manual "submit" step
and no reward for merely remembering to act; the reward tracks the
machine's actual state, checked independently every interval.

## How a team actually plays

1. Register a team on the scoreboard (`/register`). You get a token,
   shown exactly once -- save it.
2. VPN in (same `install_openvpn.sh`/`.bat` flow as before -- unchanged).
3. Exploit a machine using its existing vulnerability (SQLi, upload bug,
   shellshock, whatever -- unchanged).
4. Once you have code execution / a shell, plant your token:
   ```bash
   echo YOUR_TOKEN_HERE > /opt/koth/tag
   ```
5. From the next ScoreBot poll onward (every 30s by default), your team
   accrues that machine's points every interval, automatically, until
   someone overwrites `/opt/koth/tag` with their own token.
6. To defend it: use the access you already have to fix the vulnerability
   you came in through, so nobody else can repeat step 3-4 against you.

## How the pieces fit together

```
                              every 30s: GET /tag
  ┌───────────┐  ──────────────────────────────────────►  ┌───────────────┐
  │ ScoreBot  │                                             │ *-reporter    │
  │           │  ◄──────────────────────────────────────  │ (isolated,    │
  └─────┬─────┘         current tag content                │ no exploit    │
        │ POST /internal/poll_result                        │ surface)      │
        │ {results: {machine: {token, points}}}             └───────┬───────┘
        ▼                                                            │ shares a Docker
  ┌───────────┐                                                      │ named volume at
  │ Scoreboard│  resolves token -> team, credits points,             │ /opt/koth
  │ (Flask)   │  updates the live "Holding" table for display        ▼
  └───────────┘                                              ┌───────────────┐
                                                               │ vulnbox        │
                                                               │ (player has    │
                                                               │ root here --   │
                                                               │ can write the  │
                                                               │ tag, can't     │
                                                               │ touch the      │
                                                               │ reporter)      │
                                                               └───────────────┘
```

- `reporter-sidecar/koth_reporter.py` -- runs ONLY inside the isolated
  sidecar, never inside a vulnbox. Read-only, no dependencies.
- `<machine>_koth_tag` -- a Docker named volume shared between a vulnbox
  and its paired `*-reporter`, mounted at `/opt/koth` in both. Seeded
  with `unclaimed` at build time; the vulnbox's Dockerfile still creates
  this file world-writable (`chmod 666`) so the real vulnerability chain
  can overwrite it -- only the *reporting* moved out, not the writing.
- `scorebot/scorebot.py` -- polls every machine in `scorebot/machines.json`
  every `POLL_INTERVAL` seconds. Note the IPs there are the `*-reporter`
  sidecars' addresses (`172.20.1.x`), never the vulnboxes' own
  (`172.20.0.x`).
- `scoreboard/app.py` -- has a `Team` model with a secret `token`, and
  `/internal/poll_result` credits whichever team's token the ScoreBot
  saw reported by each machine's sidecar this round.

## Extending to a new machine

1. Copy the pattern from any existing machine: give it a Dockerfile step
   creating `/opt/koth/tag` (world-writable, seeded `unclaimed`) -- no
   Python or reporter script needed inside the vulnbox itself anymore.
2. Add a matching `<newmachine>-reporter` service to `docker-compose.yml`,
   built from `./reporter-sidecar` (reused as-is, no changes needed),
   sharing a new named volume `<newmachine>_koth_tag:/opt/koth` with
   the vulnbox.
3. Add the reporter's IP to `scorebot/machines.json` with a points weight
   (harder machines = higher weight, same idea as the original
   `flags.txt` point values, just per-interval now instead of one-time).

## What's still worth deciding before a real event

- **Point weighting per machine** is currently a flat guess in
  `machines.json` (1-2 points) -- tune this against how hard each box
  actually is to both take and hold.
- **Poll interval** (30s default) trades off scoring resolution against
  network/CPU load from N machines x however many are in the compose file.
  Shorter intervals reward fast retaking more; longer intervals reward
  patient defense more.
- **What counts as a legitimate patch vs. denial-of-service** (e.g. a
  team firewalling off the whole machine so nobody, including the
  ScoreBot, can reach it) needs a house rule -- real NetKotH events
  typically ban blocking the ScoreBot's own polling traffic specifically,
  while still allowing teams to patch/harden against actual attackers.
  Nothing here enforces that automatically; it has to be a stated rule
  plus manual review, same as any CTF's anti-cheat.
