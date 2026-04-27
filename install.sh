#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# VoiceScribe installer — run with:
#   curl -fsSL https://raw.githubusercontent.com/kalaanakonda/VoiceScribe/main/install.sh | bash
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

REPO="https://github.com/kalaanakonda/VoiceScribe.git"
INSTALL_DIR="$HOME/.voicescribe"
APP_NAME="VoiceScribe.app"
APP_PATH="/Applications/$APP_NAME"
BUNDLE_ID="com.voicescribe.app"

# Version is read from the repo's VERSION file (fallback: 1.0.0)
VS_VERSION="1.0.0"

# ── Colours ──────────────────────────────────────────────────────────────────
bold="\033[1m"
dim="\033[2m"
reset="\033[0m"
green="\033[32m"
red="\033[31m"

info()  { printf "${bold}▸${reset} %s\n" "$*"; }
ok()    { printf "${green}✓${reset} %s\n" "$*"; }
fail()  { printf "${red}✗ %s${reset}\n" "$*"; exit 1; }

# ── Pre-checks ───────────────────────────────────────────────────────────────
[[ "$(uname)" == "Darwin" ]] || fail "VoiceScribe only runs on macOS."

command -v git  >/dev/null 2>&1 || fail "git is required.  Install Xcode CLT:  xcode-select --install"
command -v clang >/dev/null 2>&1 || fail "clang is required.  Install Xcode CLT:  xcode-select --install"
command -v python3 >/dev/null 2>&1 || fail "python3 is required.  Install from python.org or via Homebrew."

# Python version check — faster-whisper needs >= 3.8
PY_VER="$(python3 -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")')"
PY_MAJOR="${PY_VER%.*}"; PY_MINOR="${PY_VER#*.}"
if (( PY_MAJOR < 3 || (PY_MAJOR == 3 && PY_MINOR < 9) )); then
  fail "Python 3.9+ required (you have $PY_VER).  Install via Homebrew: brew install python@3.11"
fi

# Check architecture
ARCH="$(uname -m)"
info "Detected architecture: $ARCH"

# ── Kill any running instance ────────────────────────────────────────────────
if pgrep -f "voicescribe" >/dev/null 2>&1; then
  info "Stopping running VoiceScribe…"
  pkill -f "voicescribe" 2>/dev/null || true
  sleep 1
fi
# Clean up any stale lock file from forced termination
rm -f /tmp/voicescribe.lock 2>/dev/null || true

# ── Clone / update repo ─────────────────────────────────────────────────────
if [[ -d "$INSTALL_DIR/.git" ]]; then
  info "Updating existing installation…"
  cd "$INSTALL_DIR"
  git pull --ff-only origin main 2>/dev/null || {
    info "Pull failed — doing a clean re-clone…"
    cd /
    rm -rf "$INSTALL_DIR"
    git clone --depth 1 "$REPO" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
  }
else
  info "Cloning VoiceScribe…"
  rm -rf "$INSTALL_DIR"
  git clone --depth 1 "$REPO" "$INSTALL_DIR"
  cd "$INSTALL_DIR"
fi
ok "Source ready at $INSTALL_DIR"

# Read version from repo
if [[ -f "$INSTALL_DIR/VERSION" ]]; then
  VS_VERSION="$(cat "$INSTALL_DIR/VERSION" | tr -d '[:space:]')"
  info "Version: $VS_VERSION"
fi

# ── Virtual environment ──────────────────────────────────────────────────────
cd "$INSTALL_DIR"
info "Setting up Python virtual environment…"
if [[ ! -d "$INSTALL_DIR/venv" ]]; then
  python3 -m venv "$INSTALL_DIR/venv"
fi
source "$INSTALL_DIR/venv/bin/activate"

info "Installing dependencies (this may take a minute)…"
pip install --upgrade pip -q
pip install -r "$INSTALL_DIR/requirements.txt" -q
ok "Dependencies installed"

# ── Build native launcher ────────────────────────────────────────────────────
info "Building native launcher…"

LAUNCHER_SRC="$(mktemp /tmp/vs_launcher_XXXX.c)"
cat > "$LAUNCHER_SRC" << 'CEOF'
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <spawn.h>
#include <sys/wait.h>

extern char **environ;

int main(int argc, char *argv[]) {
    /* cd to the install directory so Python can find the package */
    const char *install_dir = getenv("VOICESCRIBE_DIR");
    if (!install_dir) {
        /* Fallback: derive from executable path */
        char buf[4096];
        ssize_t n = readlink("/proc/self/exe", buf, sizeof(buf) - 1);
        if (n < 0) {
            /* macOS doesn't have /proc — use _NSGetExecutablePath instead */
            install_dir = NULL;
        }
    }

    /* Use the bundled path written at build time */
    const char *base = "VOICESCRIBE_INSTALL_DIR_PLACEHOLDER";
    if (chdir(base) != 0) {
        perror("chdir");
        return 1;
    }

    char py_path[4096];
    char script_path[4096];
    snprintf(py_path, sizeof(py_path), "%s/venv/bin/python", base);
    snprintf(script_path, sizeof(script_path), "%s/run.py", base);

    char *const child_argv[] = { py_path, script_path, NULL };
    pid_t pid;
    int ret = posix_spawn(&pid, py_path, NULL, NULL, child_argv, environ);
    if (ret != 0) {
        perror("posix_spawn");
        return 1;
    }

    int status;
    waitpid(pid, &status, 0);
    return WIFEXITED(status) ? WEXITSTATUS(status) : 1;
}
CEOF

# Patch in the actual install directory
sed -i '' "s|VOICESCRIBE_INSTALL_DIR_PLACEHOLDER|${INSTALL_DIR}|g" "$LAUNCHER_SRC"

LAUNCHER_BIN="$(mktemp /tmp/vs_launcher_XXXX)"
if [[ "$ARCH" == "arm64" ]]; then
  clang -arch arm64 -O2 -o "$LAUNCHER_BIN" "$LAUNCHER_SRC"
else
  clang -O2 -o "$LAUNCHER_BIN" "$LAUNCHER_SRC"
fi
rm -f "$LAUNCHER_SRC"
ok "Native launcher built"

# ── Assemble .app bundle ────────────────────────────────────────────────────
info "Building $APP_NAME…"

rm -rf "$APP_PATH"
mkdir -p "$APP_PATH/Contents/MacOS"
mkdir -p "$APP_PATH/Contents/Resources"

cp "$LAUNCHER_BIN" "$APP_PATH/Contents/MacOS/VoiceScribe"
chmod +x "$APP_PATH/Contents/MacOS/VoiceScribe"
rm -f "$LAUNCHER_BIN"

# Build paste_helper — native binary that sends Cmd+V.
# Living inside the .app bundle, it inherits VoiceScribe's TCC identity
# instead of being attributed to Python.
if [[ -f "$INSTALL_DIR/paste_helper.c" ]]; then
  info "Building paste_helper…"
  if [[ "$ARCH" == "arm64" ]]; then
    clang -arch arm64 -O2 -framework ApplicationServices \
      -o "$APP_PATH/Contents/MacOS/paste_helper" "$INSTALL_DIR/paste_helper.c"
  else
    clang -O2 -framework ApplicationServices \
      -o "$APP_PATH/Contents/MacOS/paste_helper" "$INSTALL_DIR/paste_helper.c"
  fi
  chmod +x "$APP_PATH/Contents/MacOS/paste_helper"
  ok "paste_helper built"
fi

# Copy app icon if present
if [[ -f "$INSTALL_DIR/VoiceScribe.icns" ]]; then
  cp "$INSTALL_DIR/VoiceScribe.icns" "$APP_PATH/Contents/Resources/VoiceScribe.icns"
fi

cat > "$APP_PATH/Contents/Info.plist" << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleExecutable</key>
  <string>VoiceScribe</string>
  <key>CFBundleIdentifier</key>
  <string>com.voicescribe.app</string>
  <key>CFBundleName</key>
  <string>VoiceScribe</string>
  <key>CFBundleIconFile</key>
  <string>VoiceScribe</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleVersion</key>
  <string>VOICESCRIBE_VERSION_PLACEHOLDER</string>
  <key>CFBundleShortVersionString</key>
  <string>VOICESCRIBE_VERSION_PLACEHOLDER</string>
  <key>LSUIElement</key>
  <true/>
  <key>NSPrincipalClass</key>
  <string>NSApplication</string>
  <key>LSArchitecturePriority</key>
  <array>
    <string>arm64</string>
    <string>x86_64</string>
  </array>
  <key>NSHighResolutionCapable</key>
  <true/>
  <key>NSMicrophoneUsageDescription</key>
  <string>VoiceScribe needs microphone access for voice transcription.</string>
</dict>
</plist>
PLIST

# Patch version into plist
sed -i '' "s|VOICESCRIBE_VERSION_PLACEHOLDER|${VS_VERSION}|g" "$APP_PATH/Contents/Info.plist"

# ── Code sign ────────────────────────────────────────────────────────────────
info "Signing app bundle…"
# Deep-sign the bundle first, then re-sign paste_helper with the app's bundle
# identifier so TCC attributes its keystrokes to com.voicescribe.app rather
# than to a synthetic "paste_helper-<hash>" identity (which would force the
# user to grant Accessibility permission separately).
codesign --force --deep --sign - "$APP_PATH" 2>/dev/null || true
if [[ -f "$APP_PATH/Contents/MacOS/paste_helper" ]]; then
  codesign --force --sign - --identifier "$BUNDLE_ID" \
    "$APP_PATH/Contents/MacOS/paste_helper" 2>/dev/null || true
fi

# Strip quarantine attribute (if any) so Gatekeeper doesn't pop a warning
xattr -dr com.apple.quarantine "$APP_PATH" 2>/dev/null || true
ok "App bundle ready at $APP_PATH"

# ── Done ─────────────────────────────────────────────────────────────────────
echo ""
printf "${bold}${green}VoiceScribe installed!${reset}\n"
echo ""
echo "  Open it from /Applications, or run:"
echo "    open /Applications/VoiceScribe.app"
echo ""
echo "  ${bold}First launch:${reset}"
echo "    • The Whisper model (~150 MB) downloads silently in the background."
echo "      The menu-bar icon stays as ⌛ until ready (~30s on fast wifi)."
echo "    • macOS will ask for Microphone + Accessibility permissions."
echo "      Grant BOTH or auto-paste won't work."
echo ""
echo "  ${bold}Hotkey:${reset} double-tap Fn to start, double-tap again to stop."
echo "    If macOS Dictation is enabled (System Settings → Keyboard → Dictation),"
echo "    set its shortcut to something else to avoid Fn-key conflicts."
echo ""
echo "  To update later:  curl -fsSL https://raw.githubusercontent.com/kalaanakonda/VoiceScribe/main/install.sh | bash"
echo "  To uninstall:     rm -rf ~/.voicescribe /Applications/VoiceScribe.app"
echo ""

# Offer to launch
read -rp "Launch VoiceScribe now? [Y/n] " ans </dev/tty 2>/dev/null || ans="y"
case "${ans:-y}" in
  [Nn]*) ;;
  *) open "$APP_PATH" ;;
esac
