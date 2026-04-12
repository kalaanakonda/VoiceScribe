# 🎤 VoiceScribe

**Free, local, private voice-to-text for macOS.**

No cloud. No API keys. No subscriptions. Everything runs on your Mac using [Whisper](https://github.com/openai/whisper).

## Install

**One command:**
```bash
curl -fsSL https://raw.githubusercontent.com/kalaanakonda/VoiceScribe/main/install.sh | bash
```

**Or with Homebrew:**
```bash
brew install kalaanakonda/tap/voicescribe
```

## How it works

1. Double-tap **Fn** to start recording
2. Speak naturally
3. Double-tap **Fn** again to stop
4. Text is transcribed locally and auto-pasted wherever your cursor is

That's it.

## Features

- **Local transcription** — Whisper runs on-device, nothing leaves your Mac
- **Auto-paste** — transcribed text goes straight into whatever app you're using
- **Custom dictionary** — teach it names, jargon, and technical terms
- **Snippets** — say a trigger phrase, get a full text expansion
- **Dashboard** — track words, sessions, time saved
- **Filler word removal** — automatically cleans "um", "uh", "like"
- **Multiple models** — tiny, base, small, medium (pick your speed/accuracy trade-off)

## Permissions

macOS will ask for two things on first launch:

- **Microphone** — to record your voice
- **Accessibility** — to auto-paste text (Cmd+V simulation)

Grant both in **System Settings → Privacy & Security**.

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
- Python 3.9+
- ~200 MB disk (base model)
