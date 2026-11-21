#!/usr/bin/env bash
set -euo pipefail
mkdir -p ci/shots
test -n "${RELEASE_TAG:-}" || { echo "RELEASE_TAG is required: smoke tests run against a published release"; exit 1; }
mkdir -p /tmp/rel
gh release download "$RELEASE_TAG" --repo "$GITHUB_REPOSITORY" --dir /tmp/rel --pattern '*.apk' --pattern '*.sha256' --clobber
(cd /tmp/rel && sha256sum -c ./*.sha256)
APK=$(ls /tmp/rel/simak-v*.apk)
# package/version evidence next to the pixel evidence
AAPT=$(find "$ANDROID_HOME/build-tools" -mindepth 2 -maxdepth 2 -type f -name aapt | sort -V | tail -1)
{
  "$AAPT" dump badging "$APK" | grep -E "^package:|uses-permission:" || true
} > ci/shots/00-badging.txt
adb install -r "$APK"
adb shell pm dump com.vanipy.simak | grep -E 'versionName|versionCode' | head -2 >> ci/shots/00-badging.txt || true
python3 ci/smoke.py
