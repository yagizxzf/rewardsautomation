# Microsoft Rewards Daily Task Automation

Automates daily Microsoft Rewards tasks by detecting system idle state and launching a browser session via Selenium.

## Requirements

- Windows 10 / 11
- Python 3.8+
- Microsoft Edge

## Setup

```bash
git clone https://github.com/yagizxzf/rewardsautomation.git
cd rewardsautomation
pip install -r requirements.txt
```

On the first run, the bot will open Edge and prompt you to log in to your Microsoft account. The session is persisted to a local browser profile — no further login is required.

## Usage

```bash
python rewards_bot.py --monitor   # Watch for idle, auto-run after 5 min
python rewards_bot.py --run       # Run immediately
python rewards_bot.py --reset     # Reset daily state
```

Batch file shortcuts are also provided: `start_bot.bat`, `idle_monitor.bat`, `run_now.bat`.

## Configuration

Constants at the top of `rewards_bot.py`:

```python
IDLE_THRESHOLD_SECONDS = 300   # Seconds of idle before running (default: 5 min)
CHECK_INTERVAL_SECONDS = 30    # Poll interval for idle check
```

## How It Works

1. The idle monitor polls `GetLastInputInfo` to measure inactivity.
2. A PowerShell helper (`check_media.ps1`) pauses the timer if media is playing.
3. Once the idle threshold is reached, the bot opens Edge with an isolated profile, navigates to `rewards.bing.com`, and clicks through the three daily task cards.
4. State is written to `bot_state.json` to prevent duplicate runs within the same day.

## Project Structure

```
rewards_bot.py        Main bot logic
check_media.ps1       Media playback detection (Windows API)
start_bot.bat         Interactive menu launcher
idle_monitor.bat      Quick-start idle monitor
run_now.bat           Quick-start immediate run
requirements.txt      Python dependencies
```

## Disclaimer

This project is for educational purposes only. Automating interactions with Microsoft Rewards may violate Microsoft's Terms of Service. Use at your own risk.

## License

[MIT](LICENSE)
