#!/usr/bin/env bash
#
# Build, ad-hoc sign, and package muask（沐问） for macOS.
#
# Produces:
#   dist/muask.app
#   dist/muask-macos-<arch>.dmg
#
# The app is ad-hoc signed ("-"), which is enough to run locally but does NOT
# satisfy Gatekeeper. Users downloading the DMG must approve it once via
# System Settings -> Privacy & Security -> "Open Anyway". See README.
#
# To ship without that prompt you need a paid Developer ID; the two places to
# change are marked TODO(notarize) below.

set -euo pipefail

cd "$(dirname "$0")/.."

APP="dist/muask.app"
ARCH="$(uname -m)"
DMG="dist/muask-macos-${ARCH}.dmg"
VOLNAME="沐问 MuAsk"

echo "==> Building with PyInstaller"
pyinstaller --clean --noconfirm muask.spec

if [[ ! -d "$APP" ]]; then
  echo "error: $APP was not produced — is this spec running on macOS?" >&2
  exit 1
fi

# Must happen before signing: extended attributes picked up during the build
# (com.apple.provenance, quarantine on any input file, Finder metadata) get
# sealed into the signature and then fail `codesign --verify --strict`.
echo "==> Clearing extended attributes"
xattr -cr "$APP"

echo "==> Ad-hoc signing"
# TODO(notarize): replace `-` with "Developer ID Application: NAME (TEAMID)"
# and add --options runtime --entitlements scripts/entitlements.plist
codesign --force --deep --sign - --timestamp=none "$APP"

echo "==> Verifying signature"
codesign --verify --strict --verbose=2 "$APP"

echo "==> Building DMG"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
cp -R "$APP" "$STAGE/"
# Drag-to-install target inside the mounted volume.
ln -s /Applications "$STAGE/Applications"

rm -f "$DMG"
hdiutil create \
  -volname "$VOLNAME" \
  -srcfolder "$STAGE" \
  -ov -format UDZO \
  "$DMG"

# TODO(notarize): once signed with a Developer ID, add
#   xcrun notarytool submit "$DMG" --keychain-profile <profile> --wait
#   xcrun stapler staple "$DMG"
# after which users get no prompt at all.

echo
echo "==> Done"
echo "    app: $APP"
echo "    dmg: $DMG"
