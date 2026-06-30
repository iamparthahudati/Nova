# Rai

Rai is a small offline voice-command app launcher for macOS. Say the wake word, speak a command like "open chrome" or "open youtube", and Rai opens the matching app or website. Everything runs locally on your Mac — no cloud APIs, no LLM, no data sent to any server.

## Requirements

- macOS
- Python 3.9+
- [Homebrew](https://brew.sh/) (for PortAudio)
- A free [Picovoice AccessKey](https://console.picovoice.ai/) (wake-word detection only)

## Setup

### 1. Install PortAudio

`sounddevice` needs PortAudio on macOS:

```bash
brew install portaudio
```

### 2. Create a virtual environment

```bash
cd rai
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

On first run, faster-whisper downloads the `base.en` model (~75 MB with int8 on CPU).

### 4. Get a Picovoice AccessKey

1. Sign up at [console.picovoice.ai](https://console.picovoice.ai/)
2. Copy your AccessKey from the home page
3. Set it in your shell (add to `~/.zshrc` to persist):

```bash
export PICOVOICE_ACCESS_KEY="your-key-here"
```

Rai reads `PICOVOICE_ACCESS_KEY` from the environment and exits with a clear message if it is missing.

### 5. Grant microphone permission

macOS will prompt for microphone access the first time Rai listens. If it does not:

1. Open **System Settings → Privacy & Security → Microphone**
2. Enable access for **Terminal** (or whichever app you run Rai from, e.g. iTerm, VS Code)

## Run

```bash
python rai.py
```

You should see:

```
Rai is ready.
Say the wake word to speak a command (Ctrl+C to quit).

Loading Whisper model (first run may download weights)…
Whisper loaded.

Listening for wake word…
```

When the wake word is detected, Rai records your command, transcribes it locally, and opens the match.

Press **Ctrl+C** to exit.

## Wake word

Rai uses [Picovoice Porcupine](https://picovoice.ai/platform/porcupine/) for always-on wake-word detection in the terminal.

### Test with the built-in "jarvis" word first

Leave `WAKEWORD_PATH` empty in `rai.py` (the default). Rai falls back to Porcupine's built-in **"jarvis"** keyword so you can verify the full pipeline before training a custom word:

1. Run `python rai.py`
2. Say **"jarvis"**
3. When you see `Wake word detected!`, say a command like **"open chrome"** within 4 seconds

### Train a custom "Rai" wake word

1. Go to [Picovoice Console](https://console.picovoice.ai/)
2. Open **Porcupine** → create a custom keyword named **Rai**
3. Train and test the keyword in the browser
4. Download the **macOS** `.ppn` file
5. Save it in the project, e.g. `rai_mac.ppn`
6. Set the path in `rai.py`:

```python
WAKEWORD_PATH = "rai_mac.ppn"
```

Wake-word files are platform-specific — use the macOS build on your Mac.

### Tune sensitivity

Adjust `SENSITIVITY` at the top of `rai.py` (0.0–1.0, default `0.5`). Higher values detect the wake word more easily but may cause more false triggers.

## How it works

1. Porcupine listens continuously for the wake word via `pvrecorder`.
2. On detection, Rai releases the wake-word mic and records 4 seconds of mono audio at 16 kHz with `sounddevice`.
3. faster-whisper transcribes the audio locally (model `base.en`, CPU, int8).
4. The transcript is matched against a `COMMANDS` dictionary using substring matching — so both "open chrome" and "chrome please" match the `chrome` entry.
5. On match, Rai runs the command with `subprocess`. On no match, it prints a friendly note.
6. Rai resumes listening for the wake word.

## Add your own commands

Edit the `COMMANDS` dictionary at the top of `rai.py`.

**Apps** — check the exact name in `/Applications`:

```bash
ls /Applications
```

Then add an entry:

```python
"slack": ["open", "-a", "Slack"],
```

**Websites**:

```python
"reddit": ["open", "https://www.reddit.com"],
```

Longer phrases are matched first, so `"vs code"` is preferred over `"code"`.

## Running as a background daemon (LaunchAgent)

Rai can auto-start at login and run invisibly — no terminal window needed.

A LaunchAgent plist lives at `~/Library/LaunchAgents/com.partha.rai.plist`. It
runs `rai.py` with the project's `.venv` Python, restarts it if it crashes
(`KeepAlive`), and starts it automatically at login (`RunAtLoad`). All stdout
and stderr (including Whisper logs, RMS levels, and errors) are written to
`~/rai.log` so you can debug without a visible terminal:

```bash
tail -f ~/rai.log
```

**Load it (start now + enable at login):**

```bash
launchctl load ~/Library/LaunchAgents/com.partha.rai.plist
```

**Unload it (stop and disable at login):**

```bash
launchctl unload ~/Library/LaunchAgents/com.partha.rai.plist
```

**Check whether it's running:**

```bash
launchctl list | grep com.partha.rai
```

**Reload after editing the plist or `rai.py`:**

```bash
launchctl unload ~/Library/LaunchAgents/com.partha.rai.plist
launchctl load ~/Library/LaunchAgents/com.partha.rai.plist
```

The plist hardcodes the absolute paths to the venv interpreter and `rai.py`
(`/Users/parthahudati/rai/...`) — if you move the project, update the plist's
`ProgramArguments` and `WorkingDirectory` to match.

## Configuration

At the top of `rai.py`:

| Variable | Default | Purpose |
|----------|---------|---------|
| `RECORD_SECONDS` | `4` | Recording length after wake word |
| `WHISPER_MODEL` | `"base.en"` | Whisper model name |
| `WAKEWORD_PATH` | `""` | Path to custom macOS `.ppn`; empty uses built-in `"jarvis"` |
| `SENSITIVITY` | `0.5` | Wake-word sensitivity (higher = more sensitive) |

Other defaults: 16 kHz mono audio, CPU device, int8 compute type.
