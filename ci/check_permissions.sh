#!/usr/bin/env bash
# Permission gate for simak.
#
# simak requests exactly five Android permissions, each tied to a feature the
# user asked for (see AndroidManifest.xml comments):
#   POST_NOTIFICATIONS   - reminder alerts (runtime-asked on Android 13+)
#   SCHEDULE_EXACT_ALARM - fire reminders at their minute
#   USE_EXACT_ALARM      - same, where the system grants it at install
#   RECEIVE_BOOT_COMPLETED - re-arm reminders after a restart
#   READ_CONTACTS        - on-device "speakers you may know" check
# Anything else fails the release loudly so the drift is re-reviewed.
set -euo pipefail

AAPT="$1"; APK="$2"

allowed="android.permission.POST_NOTIFICATIONS
android.permission.SCHEDULE_EXACT_ALARM
android.permission.USE_EXACT_ALARM
android.permission.RECEIVE_BOOT_COMPLETED
android.permission.READ_CONTACTS"

dump="$("$AAPT" dump permissions "$APK")"
while IFS= read -r line; do
    [ -z "$line" ] && continue
    name="$(printf '%s' "$line" | sed "s/.*name='\([^']*\)'.*/\1/")"
    if ! printf '%s\n' "$allowed" | grep -qxF "$name"; then
        echo "unexpected permission requested: $name"
        exit 1
    fi
done <<EOF
$(printf '%s\n' "$dump" | grep 'uses-permission' || true)
EOF

for need in $allowed; do
    if ! printf '%s\n' "$dump" | grep -qF "name='${need}'"; then
        echo "expected permission missing from APK: $need"
        exit 1
    fi
done

echo "permission gate: exactly the five declared permissions are requested"
