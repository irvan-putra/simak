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


# --- 0. synthetic fixture: one made-up contact sharing a long name token
# with a Day 2 speaker ("kresna"), to prove fuzzy matching without any real
# contact data.
insert_synthetic_contact("Kresna Wijaya")

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

# --- 10. reminder through the notification permission dialog (Day 2 card,
# session is tomorrow so it schedules in the future)
tap("Day 2", exact=True)
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
adb("shell", "reboot")
subprocess.run(["adb", "wait-for-device"], check=True)
for _ in range(60):
    b = adb("shell", "getprop", "sys.boot_completed").stdout.decode().strip()
    if b == "1":
        break
    time.sleep(3)
time.sleep(10)  # let BootReceiver run
alarm2 = adb("shell", "dumpsys", "alarm").stdout.decode("utf-8", "replace")
hits2 = [l for l in alarm2.splitlines() if PKG in l]
open(f"{OUT}/12-boot-rearm-dumpsys.txt", "w").write("\n".join(hits2[:40]))
if not hits2:
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
    fired = False
    for _ in range(40):  # up to ~100 s; alarm due at 08:50:00
        dn = adb("shell", "dumpsys", "notification").stdout.decode("utf-8", "replace")
        if PKG in dn and "Starting at 09:00" in dn:
            fired = True
            open(f"{OUT}/13-notification-dumpsys.txt", "w").write(
                "\n".join(l for l in dn.splitlines() if PKG in l or "Starting at" in l or "Registration" in l)[:4000])
            break
        time.sleep(2.5)
    if not fired:
        shot("FAILED-reminder-fired")
        print("reminder notification did not fire after clock move")
        sys.exit(1)
    adb("shell", "cmd", "statusbar", "expand-notifications")
    time.sleep(2)
    shot("13-reminder-fired")

print("SIMAK SMOKE OK")
