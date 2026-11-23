# Previous repo details (archived 2026-11-23)

Archived before the repo-details refresh on 2026-11-23, which rewrote the repo About description, set the website field and refreshed README.md. Current details live in the repo About section and README.md.

## About description (before)

simak - IDSW 2026 companion: agenda, guide, stars, notes, reminders. Offline Android app + web companion from one schedule.json. AGPL-3.0.

## Website field (before)

(none set)

## README.md (before)

---

# simak

**simak** (Indonesian for "listen closely") is the companion for **IDSW 2026**
(Indonesia Software Developer Conference, 21-22 November, Usmar Ismail Hall,
Jakarta Selatan): the full two-day agenda, a guide to the topics, stars for
the sessions you care about, your own notes, and optional reminders.

It comes in two shapes from one source of truth (`schedule.json`):

- **Android app** (`app/`, package `com.vanipy.simak`) - fully offline. The
  agenda is built in; there are no accounts and no network code. Reminders
  use exact alarms ten minutes before a session and nothing else: no
  polling, no background services, no wake locks. A "speakers you may know"
  check compares speaker names with your contacts **on the phone only**;
  contact names never leave the device, and a name match is a hint, never
  proof of identity.
- **Web companion** (`docs/`, served by GitHub Pages) - day switching, stars
  and notes (kept in the browser's local storage), the same guide, and a
  service worker so it keeps working offline once opened.

AGPL-3.0. Direct APK download is on the [releases page](../../releases); each
release is signed with the simak key and ships its SHA-256 next to the APK.

## Honest limits

- The agenda is copied from [idsw.dev](https://idsw.dev) as checked on
  2026-11-21 morning WIB; the event states the schedule is subject to
  change. Late schedule changes need a data update (`schedule.json`), not
  just an app refresh.
- The Guide tab's themes and priorities are our interpretation for a
  developer who builds AI-assisted personal software - suggestions, not the
  organizers' descriptions. Indonesian talk titles are quoted as published,
  with our English glosses marked as ours.
- Reminders depend on the system alarm service. Where exact alarms are not
  granted, simak schedules an approximate alarm and tells you.
- Battery behavior is designed to be idle (no background work), but actual
  power use on a given phone has not been measured.
- The contacts check reads display names only, after you grant the
  permission; denying it keeps everything else working.

## Data flow

`schedule.json` at the repo root is the single source of truth.
`tools/make_data.py` generates both consumers from it:

- `app/src/main/java/com/vanipy/simak/ScheduleData.java` (Java literals, no
  runtime parsing)
- `docs/data.js` (the web companion's data)

Both are committed; CI fails if either drifts from `schedule.json`.

## Releases and checks

- Version: three numbers (major.minor.revision), badge strip on the launcher
  icon, APK named `simak-v<version>.apk`.
- `tools/badge_icon.py` generates the launcher icons deterministically
  (pinned Pillow + vendored font); `--check` proves committed icons match.
- `.github/workflows/release.yml` (manual): patuh source gate, generated-data
  and icon checks, unit tests, signed release build, signature/package/
  permission verification, pre-release publish, post-publish verification.
- `.github/workflows/patuh-gate.yml`: family consistency gate on every push
  to main.
- `ci/check_permissions.sh` fails the release if the APK requests anything
  beyond the five declared permissions.

## Design rules

- Everything the app needs is on the phone; nothing is uploaded.
- Stars, notes and reminder toggles survive restarts; finished reminders do
  not come back after firing.
- No tracker, no analytics, no ads.

