# 🎤 VoiceScribe

**Free, local, private voice-to-text for macOS.**

No cloud. No API keys. No subscriptions. Everything runs on your Mac using [Whisper](https://github.com/openai/whisper).

A free, open-source alternative to Wispr Flow / Superwhisper.

---

## Install

**One command:**
```bash
curl -fsSL https://raw.githubusercontent.com/kalaanakonda/VoiceScribe/main/install.sh | bash
```

**Or with Homebrew:**
```bash
brew install kalaanakonda/tap/voicescribe
```

The installer pulls the source, sets up a Python venv, builds a native launcher, and drops `VoiceScribe.app` into `/Applications`.

## How it works

1. Double-tap **Fn** to start recording
2. Speak naturally
3. Double-tap **Fn** again to stop
4. Text is transcribed locally and auto-pasted wherever your cursor is

That's it. A floating pill appears at the bottom of your screen while recording — click the red stop button or double-tap Fn again to end.

## Features

- **Local transcription** — Whisper runs on-device, nothing leaves your Mac
- **Auto-paste** — transcribed text goes straight into whatever app you're using
- **Custom dictionary** — teach it names, jargon, and technical terms
- **Snippets** — say a trigger phrase, get a full text expansion (e.g. "intro email" → full template)
- **Dashboard** — track words, sessions, time saved
- **Filler word removal** — automatically cleans "um", "uh", "like"
- **Multiple models** — tiny, base, small, medium (pick your speed/accuracy trade-off)
- **Auto-update checker** — notifies you when a new version is available
- **Error log** — accessible from the menu bar for easy bug reporting

## Permissions

macOS will ask for two things on first launch:

- **Microphone** — to record your voice
- **Accessibility** — to auto-paste text (Cmd+V simulation)

Grant both in **System Settings → Privacy & Security**. The app will prompt you and open the right pane automatically if either is missing.

## Updates

VoiceScribe checks GitHub for new releases on launch. When one is available, you'll see a notification and an **"⬆ Update Available"** item in the menu bar. Click it to open the release page.

To update manually, just re-run the install command.

## Troubleshooting

**Auto-paste not working?**
Make sure both VoiceScribe AND Python are listed in System Settings → Privacy & Security → Accessibility, and that both toggles are ON.

**App didn't start?**
Check the error log via the menu bar → "View Error Log", or look at:
```
~/Library/Application Support/VoiceScribe/crash.log
/tmp/voicescribe_debug.log
```

**Want to report a bug?**
Open an issue with the contents of `crash.log` attached.

## Uninstall

```bash
curl -fsSL https://raw.githubusercontent.com/kalaanakonda/VoiceScribe/main/uninstall.sh | bash
```

Or manually:
```bash
rm -rf ~/.voicescribe /Applications/VoiceScribe.app
```

Your data lives at `~/Library/Application Support/VoiceScribe/` — delete that too for a clean slate.

## Requirements

- macOS 13+ (Ventura or later)
- Apple Silicon or Intel Mac
- Python 3.9+
- ~200 MB disk (base model)

## License

MIT
