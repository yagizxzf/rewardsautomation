import os
import sys
import time
import json
import ctypes
import subprocess
from datetime import datetime, date
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.options import Options as EdgeOptions

IDLE_THRESHOLD_SECONDS = 300
CHECK_INTERVAL_SECONDS = 30
STATE_FILE = "bot_state.json"


class LASTINPUTINFO(ctypes.Structure):
    """Windows API structure for tracking last user input time."""
    _fields_ = [
        ('cbSize', ctypes.c_uint),
        ('dwTime', ctypes.c_uint),
    ]


def get_idle_time():
    """Return the number of seconds since the last user input (keyboard/mouse)."""
    lii = LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
    millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
    return millis / 1000.0


def is_media_playing():
    """Check if any media is currently playing via the Windows media transport controls."""
    try:
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "check_media.ps1")

        result = subprocess.run(
            ['powershell', '-ExecutionPolicy', 'Bypass', '-NoProfile', '-File', script_path],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        output = result.stdout.strip()
        return output == "PLAYING"

    except Exception:
        return False


def load_state():
    """Load bot state from the JSON state file."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"last_run_date": None}


def save_state(state):
    """Save bot state to the JSON state file."""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)


def already_ran_today():
    """Check whether the bot has already completed tasks today."""
    state = load_state()
    today = date.today().isoformat()
    return state.get("last_run_date") == today


def mark_as_ran_today():
    """Mark today's date as completed in the state file."""
    state = load_state()
    state["last_run_date"] = date.today().isoformat()
    save_state(state)


def create_browser():
    """Create a Microsoft Edge browser instance with an isolated profile."""
    options = EdgeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")

    bot_profile_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "edge_profile")
    if not os.path.exists(bot_profile_dir):
        os.makedirs(bot_profile_dir)
    options.add_argument(f"--user-data-dir={bot_profile_dir}")

    driver = webdriver.Edge(options=options)
    return driver


def wait_and_click(driver, wait, selector, by=By.CSS_SELECTOR, description="element"):
    """Wait for an element to become clickable and click it."""
    try:
        print(f"  -> Waiting for {description}...")
        element = wait.until(EC.element_to_be_clickable((by, selector)))
        time.sleep(1)
        element.click()
        print(f"  [OK] Clicked {description}")
        return True
    except Exception as e:
        print(f"  [X] {description} not found: {e}")
        return False


def scroll_to_element(driver, element):
    """Smoothly scroll the page so the given element is centered in the viewport."""
    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
    time.sleep(1)


def find_daily_tasks(driver):
    """Find all daily task cards in the new React-based rewards dashboard."""
    try:
        task_links = []

        try:
            daily_section = driver.find_element(By.CSS_SELECTOR, "section#dailyset")
            task_links = daily_section.find_elements(By.CSS_SELECTOR, "a[target='_blank']")
            if task_links:
                print(f"  -> Found {len(task_links)} tasks via section#dailyset")
                return task_links
        except:
            pass

        try:
            sections = driver.find_elements(By.CSS_SELECTOR, "section")
            for section in sections:
                try:
                    text = section.text
                    if "Daily" in text or "daily" in text or "Günlük" in text:
                        task_links = section.find_elements(By.CSS_SELECTOR, "a[href*='bing.com']")
                        if task_links:
                            print(f"  -> Found {len(task_links)} tasks via section text search")
                            return task_links
                except:
                    pass
        except:
            pass

        try:
            task_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='bing.com/search'][target='_blank']")
            if task_links:
                print(f"  -> Found {len(task_links)} tasks via Bing search links")
                return task_links
        except:
            pass

        try:
            task_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='bing.com']")
            external_links = [link for link in task_links if link.get_attribute('target') == '_blank' or 'bing.com/search' in link.get_attribute('href')]
            if external_links:
                print(f"  -> Found {len(external_links)} tasks via Bing link filter")
                return external_links[:3]
        except:
            pass

        try:
            result = driver.execute_script("""
                let links = Array.from(document.querySelectorAll('a[href*="bing.com"]')).filter(a => {
                    let rect = a.getBoundingClientRect();
                    return rect.width > 0 && rect.height > 0 && a.offsetParent !== null;
                });
                return links.slice(0, 3).map(l => l.outerHTML);
            """)
            if result and len(result) > 0:
                return driver.find_elements(By.CSS_SELECTOR, "a[href*='bing.com']")[:3]
        except:
            pass

        print("  [!] No task links found via any strategy")
        return []

    except Exception as e:
        print(f"  [X] Error in find_daily_tasks: {str(e)[:80]}")
        return []


def complete_daily_tasks(driver):
    """Navigate to Microsoft Rewards and complete the 3 daily tasks."""
    wait = WebDriverWait(driver, 15)

    print("\n[*] Opening rewards.bing.com...")
    driver.get("https://rewards.bing.com/")

    try:
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    except:
        pass

    time.sleep(3)

    state = load_state()
    if not state.get("first_login_done", False):
        print("\n" + "!" * 60)
        print(" FIRST-TIME SETUP: Please log in to your Microsoft account")
        print(" in the browser window that just opened.")
        print(" Once you're logged in, come back here and press ENTER.")
        print("!" * 60)
        input(" Press ENTER when ready: ")

        state["first_login_done"] = True
        save_state(state)
        print("\n[*] Login state saved — you won't be asked again.\n")

        driver.get("https://rewards.bing.com/")
        time.sleep(5)
    else:
        time.sleep(2)

    print("\n[*] Searching for daily tasks...")
    print("[*] Page may take a few seconds to render...")

    time.sleep(4)

    print("[*] Scrolling to reveal content...")
    driver.execute_script("window.scrollBy(0, 300);")
    time.sleep(2)
    driver.execute_script("window.scrollBy(0, 300);")
    time.sleep(2)

    completed_tasks = 0

    task_cards = find_daily_tasks(driver)

    if not task_cards:
        print("[*] No tasks found on first attempt, retrying...")
        driver.execute_script("window.scrollBy(0, -500);")
        time.sleep(2)
        task_cards = find_daily_tasks(driver)

    if not task_cards:
        print("  [!] Still no task cards found")
        print("  [*] Checking page content for debugging...")
        try:
            body_text = driver.find_element(By.TAG_NAME, "body").text
            print(f"  [DEBUG] Page has content: {len(body_text)} characters")
            if "Daily" in body_text or "daily" in body_text:
                print("  [DEBUG] Page contains 'Daily' text")
        except:
            pass

    if task_cards:
        print(f"\n[*] Found {len(task_cards)} tasks, processing...")

    for task_num in range(1, min(4, len(task_cards) + 1)):
        print(f"\n[*] Task {task_num}/{len(task_cards)}...")

        try:
            card = task_cards[task_num - 1]
            scroll_to_element(driver, card)
            time.sleep(1)

            main_window = driver.current_window_handle
            initial_handles = set(driver.window_handles)

            try:
                card.click()
            except Exception:
                driver.execute_script("arguments[0].click();", card)

            print(f"  [OK] Clicked")
            time.sleep(3)

            new_handles = set(driver.window_handles) - initial_handles

            if new_handles:
                new_tab = new_handles.pop()
                driver.switch_to.window(new_tab)
                print(f"  [OK] Task page opened")

                time.sleep(5)

                driver.close()
                print("  [OK] Closed")

                driver.switch_to.window(main_window)
                time.sleep(2)
            else:
                time.sleep(3)
                driver.back()
                time.sleep(2)

            completed_tasks += 1

        except Exception as e:
            print(f"  [X] Error: {str(e)[:80]}")
            continue

    return completed_tasks


def run_automation():
    """Main automation entry point: launch browser, complete tasks, and clean up."""
    print("\n" + "=" * 50)
    print("Microsoft Rewards Bot Starting")
    print("=" * 50)

    driver = None
    try:
        driver = create_browser()
        completed = complete_daily_tasks(driver)

        print("\n" + "=" * 50)
        print(f"[OK] Completed tasks: {completed}/3")
        print("=" * 50)

        if completed > 0:
            mark_as_ran_today()
            print("[*] Marked as done for today — will run again tomorrow.")

    except Exception as e:
        print(f"\n[X] Error: {e}")
    finally:
        if driver:
            time.sleep(3)
            driver.quit()
            print("[*] Browser closed")


def idle_monitor():
    """Monitor system idle state and trigger automation when the threshold is reached."""
    print("\n" + "=" * 50)
    print("Microsoft Rewards Idle Monitor")
    print("=" * 50)
    print(f"Idle threshold: {IDLE_THRESHOLD_SECONDS}s ({IDLE_THRESHOLD_SECONDS // 60} min)")
    print(f"Check interval: {CHECK_INTERVAL_SECONDS}s")
    print("Timer pauses while media is playing")
    print("=" * 50)
    print("\n[*] Monitoring idle state... (Ctrl+C to quit)")

    while True:
        try:
            if already_ran_today():
                print(f"\r[*] Already ran today. Waiting for tomorrow... "
                      f"(Time: {datetime.now().strftime('%H:%M:%S')})", end="")
                time.sleep(60)

                if datetime.now().hour == 0 and datetime.now().minute < 2:
                    print("\n[*] New day started, resetting state...")
                continue

            if is_media_playing():
                print(f"\r[*] Media playing, timer paused | "
                      f"Time: {datetime.now().strftime('%H:%M:%S')}    ", end="")
                time.sleep(CHECK_INTERVAL_SECONDS)
                continue

            idle_time = get_idle_time()

            if idle_time >= IDLE_THRESHOLD_SECONDS:
                print(f"\n\n[*] Idle for {idle_time:.0f}s detected!")
                print("[*] Starting automation...\n")
                run_automation()
                print("\n[*] Resuming monitoring...\n")
            else:
                remaining = IDLE_THRESHOLD_SECONDS - idle_time
                print(f"\r[*] Idle: {idle_time:.0f}s / {IDLE_THRESHOLD_SECONDS}s "
                      f"(Remaining: {remaining:.0f}s) | "
                      f"Time: {datetime.now().strftime('%H:%M:%S')}", end="")

            time.sleep(CHECK_INTERVAL_SECONDS)

        except KeyboardInterrupt:
            print("\n\n[*] Shutting down...")
            break
        except Exception as e:
            print(f"\n[!] Error: {e}")
            time.sleep(10)


def main():
    """Entry point with CLI argument support and interactive menu."""
    print("""
    +=========================================================+
    |     Microsoft Rewards Daily Task Automation              |
    +---------------------------------------------------------+
    |  1. Idle Monitor (wait 5 min, auto-run)                 |
    |  2. Run Now (start immediately)                         |
    |  3. Reset State (allow re-run today)                    |
    |  4. Exit                                                |
    +=========================================================+
    """)

    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ['--monitor', '-m', '1']:
            idle_monitor()
        elif arg in ['--run', '-r', '2']:
            run_automation()
        elif arg in ['--reset', '-s', '3']:
            state = load_state()
            state["last_run_date"] = None
            save_state(state)
            print("[OK] State reset!")
        return

    while True:
        choice = input("\nYour choice (1-4): ").strip()

        if choice == '1':
            idle_monitor()
        elif choice == '2':
            run_automation()
        elif choice == '3':
            state = load_state()
            state["last_run_date"] = None
            save_state(state)
            print("[OK] State reset! Bot can run again today.")
        elif choice == '4':
            print("Goodbye!")
            break
        else:
            print("[X] Invalid choice!")


if __name__ == "__main__":
    main()
