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
    for i in range(6):
        if present(text, exact):
            return
        if i >= 2:
            adb("shell", "input", "swipe", "540", "700", "540", "1800", "300")
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
    r = adb("shell", "content", "insert", "--uri", "content://com.android.contacts/raw_contacts")
    m = re.search(r"raw_contacts/(\d+)", r.stdout.decode())
    if not m:
        print("raw contact insert failed:", r.stdout, r.stderr)
        sys.exit(1)
    rid = m.group(1)
    r2 = adb("shell", "content", "insert", "--uri", "content://com.android.contacts/data",
             "--bind", "raw_contact_id:i:" + rid,
             "--bind", "mimetype:s:vnd.android.cursor.item/name",
             "--bind", "data1:s:" + name)
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
adb("shell", "input", "swipe", "540", "1800", "540", "600", "400")  # open app drawer
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

# --- 3. Day 2 tab with the Kresna session
tap("Day 2", exact=True)
need("Building a Browser Engine with AI Is Harder Than You Think")
need("Kresna Satya")
shot("03-day2-kresna")

# --- 4. star the first Day 2 card
tap("\u2606", exact=True)  # outlined star
if not wait_present("\u2605", exact=True, tries=4):
    shot("FAILED-star-toggle")
    print("star did not toggle to filled")
    sys.exit(1)
shot("04-starred")

# --- 5. note on the first Day 2 card (tap title to expand, then type)
tap("Registration")
if not wait_present("Your note for this session", tries=4):
    shot("FAILED-note-expand")
    print("note field did not expand")
    sys.exit(1)
tap("Your note for this session")
adb("shell", "input", "text", "meet%sfriends%safter")
time.sleep(1)
need("meet friends after")
shot("05-note")

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

print("SIMAK SMOKE OK")
