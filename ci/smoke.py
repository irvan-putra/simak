"""Synthetic-data smoke test for simak on an emulator.

Drives the real published APK over adb and saves screenshots into ci/shots.
Covers: launcher icon + header, day tabs with the real agenda (incl. the
Kresna session on Day 2), star and note persistence across a force stop,
the guide tab, contacts permission denial, the synthetic contacts match,
and reminder scheduling through the notification permission dialog.
Only synthetic data is used: one made-up contact, one typed note.
"""
import re, subprocess, sys, time
import xml.etree.ElementTree as ET

PKG = "com.vanipy.simak"
OUT = "ci/shots"
subprocess.run(["mkdir", "-p", OUT])


def adb(*a, **k):
    return subprocess.run(["adb", *a], capture_output=True, **k)


def shot(name):
    time.sleep(1.0)
    data = adb("exec-out", "screencap", "-p").stdout
    open(f"{OUT}/{name}.png", "wb").write(data)


def nodes():
    last = ""
    for attempt in range(15):
        adb("shell", "rm", "-f", "/sdcard/ui.xml")
        dump = adb("shell", "uiautomator", "dump", "/sdcard/ui.xml")
        raw = adb("exec-out", "cat", "/sdcard/ui.xml")
        xml = raw.stdout.decode("utf-8", "replace")
        try:
            if dump.returncode or raw.returncode:
                raise ET.ParseError("UI dump command failed")
            return [n.attrib for n in ET.fromstring(xml).iter("node")]
        except ET.ParseError:
            last = repr(xml) + "\n" + dump.stdout.decode("utf-8", "replace") + dump.stderr.decode("utf-8", "replace")
            time.sleep(2)
    open(f"{OUT}/ui-dump-failure.txt", "w").write(last)
    shot("FAILED-ui-dump")
    raise RuntimeError("No valid UIAutomator XML after fifteen attempts; raw diagnostic saved")


def center(b):
    m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", b)
    x1, y1, x2, y2 = map(int, m.groups())
    return (x1 + x2) // 2, (y1 + y2) // 2


def find(text, exact=False):
    for n in nodes():
        t = ((n.get("text") or "") + " " + (n.get("content-desc") or "")).strip().lower()
        if (t == text.lower()) if exact else (text.lower() in t):
            return n
    return None


def present(text, exact=False):
    return find(text, exact) is not None


def tap_node(n):
    x, y = center(n["bounds"])
    adb("shell", "input", "tap", str(x), str(y))
    time.sleep(0.8)


def tap(text, exact=False, tries=6):
    for _ in range(tries):
        n = find(text, exact)
        if n:
            tap_node(n)
            return
        adb("shell", "input", "swipe", "540", "1700", "540", "700", "300")
        time.sleep(1)
    shot("FAILED-" + re.sub(r"\W+", "_", text)[:30])
    print("NOT FOUND:", text)
    sys.exit(1)


def need(text, exact=False):
    for i in range(10):
        if present(text, exact):
            return
        if i >= 2:
            # finger moves up so the list advances forward (toward later items)
            adb("shell", "input", "swipe", "540", "1700", "540", "700", "300")
        time.sleep(1)
    shot("FAILED-need-" + re.sub(r"\W+", "_", text)[:30])
    print("EXPECTED ON SCREEN:", text)
    sys.exit(1)


def wait_present(text, exact=False, tries=8):
    for _ in range(tries):
        if present(text, exact):
            return True
        time.sleep(1)
    return False


def launch():
    adb("shell", "am", "start", "-n", PKG + "/.MainActivity")
    time.sleep(3)


def insert_synthetic_contact(name):
    """One made-up contact via the real contacts provider."""
    adb("shell", "content", "insert", "--uri", "content://com.android.contacts/raw_contacts",
        "--bind", "account_type:s:local", "--bind", "account_name:s:simak-fixture")
    q = adb("shell", "content", "query", "--uri", "content://com.android.contacts/raw_contacts",
            "--projection", "_id")
    ids = re.findall(r"_id=(\d+)", q.stdout.decode())
    if not ids:
        print("raw contact insert failed:", q.stdout, q.stderr)
        sys.exit(1)
    rid = str(max(int(i) for i in ids))
    r2 = adb("shell", "content", "insert", "--uri", "content://com.android.contacts/data",
             "--bind", "raw_contact_id:i:" + rid,
             "--bind", "mimetype:s:vnd.android.cursor.item/name",
             "--bind", "data1:s:'" + name + "'")
    print("synthetic contact:", name, "->", r2.stdout.decode().strip())


def perm_dialog_button(label_variants):
    for v in label_variants:
        n = find(v, exact=True)
        if n:
            tap_node(n)
            return True
    return False


# --- pre. legacy state migration (only when ci/run.sh installed a base
# APK first): seed a note on the old combined lightning card, upgrade in
# place (same signer, data preserved), and confirm the kept whole-block
# card still carries the note with its legacy label.
import glob
base_apks = glob.glob("/tmp/base/simak-v*.apk")
if base_apks:
    launch()
    tap("Day 2", exact=True)
    if wait_present("Lightning talks:", tries=4):
        # pre-split base: the combined card carries the seeded note
        tap("Lightning talks:")
        seed_title = "Lightning talks:"
        migrated_title = "whole block (saved before the split)"
    else:
        # post-split base (e.g. 0.3.0): seed on one split card instead;
        # post-upgrade the same card must keep it (id-keyed state)
        need("Everything Has an API If You're Willing to Prompt")
        tap("Everything Has an API If You're Willing to Prompt")
        seed_title = "Everything Has an API If You're Willing to Prompt"
        migrated_title = seed_title
    need("Your note for this session")
    tap("Your note for this session")
    adb("shell", "input", "text", "legacy%sblock%snote")
    time.sleep(1)
    need("legacy block note")
    shot("00a-base-block-note")
    adb("shell", "input", "keyevent", "4")  # dismiss the IME
    time.sleep(1)
    rel_apks = glob.glob("/tmp/rel/simak-v*.apk")
    if not rel_apks:
        print("release APK missing under /tmp/rel")
        sys.exit(1)
    r = adb("install", "-r", rel_apks[0])
    print("upgrade install:", r.stdout.decode().strip())
    if r.returncode:
        print(r.stderr.decode())
        sys.exit(1)
    time.sleep(2)
    launch()
    tap("Day 2", exact=True)
    need(migrated_title)
    tap(migrated_title)
    need("legacy block note")
    if migrated_title != seed_title:
        need("kept as-is")
    shot("00b-legacy-state-migrated")
    adb("shell", "input", "keyevent", "4")
    adb("shell", "am", "force-stop", PKG)  # fresh, collapsed list for step 1
    time.sleep(1)

# --- 0. synthetic fixture: one made-up contact sharing a long name token
# with a Day 2 speaker ("kresna"), to prove fuzzy matching without any real
# contact data.
# Synthetic contacts, one per card shape the highlight must join: a plain
# speaker field (fuzzy token match), org-suffixed fields on both days, and
# a multi-speaker lightning card.
insert_synthetic_contact("Kresna Wijaya")
insert_synthetic_contact("Zain Fathoni")
insert_synthetic_contact("Bagas Wastu")
insert_synthetic_contact("Bagas Wastu Junior")
insert_synthetic_contact("Thomas Edwin Santosa")
insert_synthetic_contact("Eko Kurniawan Khannedy")

# --- 1. launcher icon pixels (family icon with the version badge)
adb("shell", "input", "keyevent", "3")  # HOME
time.sleep(2)
adb("shell", "input", "swipe", "540", "2000", "540", "500", "600")  # app drawer (gesture nav)
time.sleep(2)
adb("shell", "input", "swipe", "540", "2000", "540", "500", "600")
time.sleep(2)
if wait_present("simak", exact=True, tries=6):
    shot("01-launcher-icon")
else:
    print("WARN: simak icon not visible in drawer; continuing")

# --- 2. Day 1 home
launch()
need("Day 1", exact=True)
need("Day 2", exact=True)
need("Guide", exact=True)
need("simak - IDSW 2026")
need("Registration")
shot("02-day1")

# --- 3. Day 2 tab: star and note the first card while it is at the top,
# then scroll forward to the Kresna session.
tap("Day 2", exact=True)
need("Registration")
tap("\u2606", exact=True)  # outlined star on the first card
if not wait_present("\u2605", exact=True, tries=4):
    shot("FAILED-star-toggle")
    print("star did not toggle to filled")
    sys.exit(1)
shot("03-starred")
tap("Registration")
if not wait_present("Your note for this session", tries=4):
    shot("FAILED-note-expand")
    print("note field did not expand")
    sys.exit(1)
tap("Your note for this session")
adb("shell", "input", "text", "meet%sfriends%safter")
time.sleep(1)
need("meet friends after")
shot("04-note")
adb("shell", "input", "keyevent", "4")  # dismiss the IME before scrolling
time.sleep(1)
need("Building a Browser Engine with AI Is Harder Than You Think")
need("Kresna Satya")
shot("05-day2-kresna")

# --- 6. persistence across a force stop
adb("shell", "am", "force-stop", PKG)
time.sleep(1)
launch()
tap("Day 2", exact=True)
need("\u2605", exact=True)
tap("Registration")
need("meet friends after")
shot("06-persistence")

# --- 7. guide tab
tap("Guide", exact=True)
need("Speakers you may know")
shot("07-guide")

# --- 8. contacts permission DENIAL path
tap("Speakers you may know (uses your contacts, on this phone only)")
if not perm_dialog_button(["Don\u2019t allow", "Don't allow", "Deny"]):
    shot("FAILED-contacts-dialog")
    print("contacts permission dialog did not appear")
    sys.exit(1)
time.sleep(2)
shot("08-contacts-denied")
if present("Speakers who look like your contacts"):
    shot("FAILED-denial-showed-matches")
    print("matches shown despite denial")
    sys.exit(1)

# --- 9. contacts ALLOW path with the synthetic contact
tap("Speakers you may know (uses your contacts, on this phone only)")
if not perm_dialog_button(["Allow"]):
    shot("FAILED-contacts-dialog-2")
    print("contacts permission dialog did not reappear")
    sys.exit(1)
need("Speakers who look like your contacts")
need("Kresna Satya")
need("Kresna Wijaya")  # the synthetic contact surfaced as a hint
need("not proof it is the same person")
shot("09-contacts-match")

# --- 9b. the matched contact name shows on each talk's agenda card:
# org-suffixed, plain, per-talk lightning and affiliation cards, on both
# days. The \u2248 prefix pins the assertion to the hint line, not the
# speaker line.
tap("Day 2", exact=True)
need("(Human) Attention is All You Need")
need("\u2248 Zain Fathoni")
need("name similarity only")
need("Building a Browser Engine with AI Is Harder Than You Think")
need("\u2248 Kresna Wijaya")
# lightning talks are split into one card per talk, sharing the window;
# the hint line also proves strongest-first ordering (exact before
# containment)
need("Everything Has an API If You're Willing to Prompt")
need("\u2248 Bagas Wastu, Bagas Wastu Junior - name similarity only")
need("Tokenomics of Testing")  # the last split lightning card
# affiliation containing a ";" must stay one speaker, not fake names
need("Keynote: title to be announced")
need("\u2248 Eko Kurniawan Khannedy")
shot("09b-day2-highlight")
tap("Day 1", exact=True)
# the Day 2 scroll position carries over; go back to the top first
for _ in range(15):
    if present("Registration"):
        break
    adb("shell", "input", "swipe", "540", "700", "540", "1700", "300")
    time.sleep(1)
need("Registration")
need("\u2248 Thomas Edwin Santosa")
shot("09c-day1-highlight")

# --- 10. reminder through the notification permission dialog (Day 2 card,
# session is tomorrow so it schedules in the future)
tap("Day 2", exact=True)
# step 9b scrolled down to the Kresna card; go back to the top so the
# first bell in the tree is Registration's - the firing test moves the
# clock to just before the Registration reminder
for _ in range(15):
    if present("Registration"):
        break
    adb("shell", "input", "swipe", "540", "700", "540", "1700", "300")
    time.sleep(1)
need("Registration")
tap("\U0001F515", exact=True)  # bell, no-reminder state
if not perm_dialog_button(["Allow"]):
    shot("FAILED-notif-dialog")
    print("notification permission dialog did not appear")
    sys.exit(1)
if not wait_present("\U0001F514", exact=True, tries=6):
    shot("FAILED-bell-on")
    print("bell did not switch to reminder-on")
    sys.exit(1)
shot("10-reminder-set")

# --- 11. the alarm is really scheduled with the OS
alarm = adb("shell", "dumpsys", "alarm").stdout.decode("utf-8", "replace")
hits = [l for l in alarm.splitlines() if PKG in l]
open(f"{OUT}/11-alarm-dumpsys.txt", "w").write("\n".join(hits[:40]))
if not hits:
    shot("FAILED-alarm-dumpsys")
    print("no alarm registered for", PKG)
    sys.exit(1)

# --- 12. boot re-arm: reboot with the reminder pending; BootReceiver must
# re-arm it. Done BEFORE the firing test because firing consumes the stored
# toggle by design.
boot_count = adb("shell", "getprop", "sys.boot_count").stdout.decode().strip()
adb("shell", "reboot")
time.sleep(15)  # let the device actually go down: wait-for-device returns instantly otherwise
subprocess.run(["adb", "wait-for-device"], check=True)
for _ in range(80):
    done = adb("shell", "getprop", "sys.boot_completed").stdout.decode().strip()
    cnt = adb("shell", "getprop", "sys.boot_count").stdout.decode().strip()
    if done == "1" and cnt and cnt != boot_count:
        break
    time.sleep(3)
time.sleep(15)  # let BootReceiver run under post-boot churn
hits2 = []
for _ in range(3):
    alarm2 = adb("shell", "dumpsys", "alarm").stdout.decode("utf-8", "replace")
    hits2 = [l for l in alarm2.splitlines() if PKG in l]
    if hits2:
        break
    time.sleep(10)
open(f"{OUT}/12-boot-rearm-dumpsys.txt", "w").write("\n".join(hits2[:40]))
if not hits2:
    logcat = adb("logcat", "-d", "-t", "2000").stdout.decode("utf-8", "replace")
    open(f"{OUT}/12-boot-logcat.txt", "w").write(
        "\n".join(l for l in logcat.splitlines() if "simak" in l.lower() or "Boot" in l)[:6000])
    shot("FAILED-boot-rearm")
    print("no alarm re-armed for", PKG, "after reboot")
    sys.exit(1)

# --- 13. reminder actually fires: emulator is userdebug, so move the clock
# to just before 08:50 WIB on Day 2 and watch for the notification.
root = adb("root")
time.sleep(4)
subprocess.run(["adb", "wait-for-device"], check=True)
whoami = adb("shell", "id").stdout.decode()
if "uid=0" not in whoami:
    print("SKIP firing test: adb root unavailable:", whoami.strip())
else:
    adb("shell", "settings", "put", "global", "auto_time", "0")
    adb("shell", "setprop", "persist.sys.timezone", "Asia/Jakarta")
    time.sleep(2)
    adb("shell", "date", "1122084926.30")  # 2026-11-22 08:49:30 device-local
    time.sleep(1)
    open(f"{OUT}/13-clock.txt", "w").write(
        adb("shell", "date").stdout.decode()
        + adb("shell", "getprop", "persist.sys.timezone").stdout.decode())
    alarm3 = adb("shell", "dumpsys", "alarm").stdout.decode("utf-8", "replace")
    open(f"{OUT}/13-alarm-after-clockmove.txt", "w").write(
        "\n".join(l for l in alarm3.splitlines() if PKG in l))
    fired = False
    for _ in range(40):  # up to ~100 s; alarm due at 08:50:00
        dn = adb("shell", "dumpsys", "notification", "--noredact").stdout.decode("utf-8", "replace")
        # an actual posted notification is a NotificationRecord naming the
        # package; the AppSettings section mentions the package always
        if re.search(r"NotificationRecord\([^)]*pkg=" + PKG, dn):
            fired = True
            open(f"{OUT}/13-notification-dumpsys.txt", "w").write(
                "\n".join(l for l in dn.splitlines() if PKG in l or "Starting at" in l or "Registration" in l or "android.title" in l)[:4000])
            break
        time.sleep(2.5)
    if not fired:
        open(f"{OUT}/13-fail-diagnostics.txt", "w").write(
            "== date ==\n" + adb("shell", "date").stdout.decode()
            + "== notification ==\n" + adb("shell", "dumpsys", "notification", "--noredact").stdout.decode("utf-8", "replace")[-4000:]
            + "== alarm ==\n" + adb("shell", "dumpsys", "alarm").stdout.decode("utf-8", "replace")[-3000:]
            + "== logcat (simak + AndroidRuntime) ==\n" + "\n".join(
                l for l in adb("logcat", "-d").stdout.decode("utf-8", "replace").splitlines()
                if "simak" in l.lower() or "AndroidRuntime" in l or "NotificationManager" in l)[:6000])
        shot("FAILED-reminder-fired")
        print("reminder notification did not fire after clock move")
        sys.exit(1)
    adb("shell", "cmd", "statusbar", "expand-notifications")
    time.sleep(2)
    shot("13-reminder-fired")

print("SIMAK SMOKE OK")
