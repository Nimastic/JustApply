from datetime import datetime
import os
import hashlib
import tempfile
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

from boards import BOARDS

ROLE_WORDS = (
    "engineer",
    "developer",
    "researcher",
    "scientist",
    "trader",
    "quantitative",
    "quant ",
    "software",
    "infrastructure",
    "inference",
    "designer",
    "platform",
    "backend",
    "frontend",
    "full stack",
    "fullstack",
    "machine learning",
    "data scientist",
    "swe",
)
SKIP_PHRASES = (
    "intern",
    "internship",
    "new grad",
    "new-grad",
    "university graduate",
    "students and new",
    "cookie",
    "privacy",
    "copyright",
    "sign in",
    "log in",
    "certificate",
    "err_cert",
    "accept all",
    "equal opportunity",
    "all rights",
)
MAX_ADDED = 12
MAX_CLOSED = 5


def get_url_hash(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()


def setup_selenium():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument(f"--user-data-dir={tempfile.mkdtemp(prefix='chrome-user-data-')}")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-images")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-features=TranslateUI")
    chrome_options.add_argument("--disable-ipc-flooding-protection")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)


def fetch_html(driver, url: str) -> str | None:
    print(f"Fetching {url}")
    try:
        driver.set_page_load_timeout(30)
        driver.get(url)
        time.sleep(8)
        return driver.page_source
    except Exception as e:
        print(f"Fetch failed for {url}: {e}")
        return None


def extract_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    lines = [line.strip() for line in soup.get_text(separator="\n").splitlines() if line.strip()]
    return "\n".join(lines)


def storage_path(url: str) -> str:
    return f"text_storage/{get_url_hash(url)}.txt"


def save_text(url: str, text_content: str) -> None:
    os.makedirs("text_storage", exist_ok=True)
    with open(storage_path(url), "w", encoding="utf-8") as f:
        f.write(text_content)


def load_text(url: str) -> str | None:
    path = storage_path(url)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return f.read()


def is_role(line: str) -> bool:
    if len(line) < 8 or len(line) > 120:
        return False
    if len(line.split()) < 2:
        return False
    letters = sum(c.isalpha() for c in line)
    if letters < len(line) * 0.5:
        return False
    low = line.lower()
    if any(phrase in low for phrase in SKIP_PHRASES):
        return False
    return any(word in low for word in ROLE_WORDS)


def role_lines(text: str) -> list[str]:
    seen = []
    for line in text.splitlines():
        cleaned = line.strip()
        if cleaned and is_role(cleaned) and cleaned not in seen:
            seen.append(cleaned)
    return seen


def html_escape(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def format_side(label: str, lines: list[str], limit: int) -> list[str]:
    shown = lines[:limit]
    extra = len(lines) - len(shown)
    body = [f"{label} {html_escape(line)}" for line in shown]
    if extra > 0:
        body.append(f"{label} {extra} more")
    return body


def role_alert(name: str, url: str, old_roles: list[str], new_roles: list[str]) -> str | None:
    added = [line for line in new_roles if line not in old_roles]
    closed = [line for line in old_roles if line not in new_roles]
    if not added and not closed:
        return None
    lines = [f"<b>{html_escape(name)}</b>"]
    lines.extend(format_side("+", added, MAX_ADDED))
    lines.extend(format_side("closed:", closed, MAX_CLOSED))
    lines.append(f'<a href="{html_escape(url)}">open the board</a>')
    return "\n".join(lines)


def write_reports(alerts: list[str], baselines: list[str], failures: list[str]) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    parts = [f"# Latest role check\n\n## {timestamp}\n"]
    if alerts:
        parts.append("\n\n".join(alerts))
        open("alert.txt", "w", encoding="utf-8").write("\n\n".join(alerts) + "\n")
    else:
        parts.append("No role changes.")
        open("alert.txt", "w", encoding="utf-8").write("NONE\n")
    if baselines:
        parts.append("\n\nBaselines stored, no alert: " + ", ".join(baselines))
    if failures:
        parts.append("\n\nFetch failed: " + ", ".join(failures))
    parts.append("\n")
    with open("changes.md", "w", encoding="utf-8") as f:
        f.write("\n".join(parts))


def process_boards() -> None:
    driver = setup_selenium()
    alerts = []
    baselines = []
    failures = []
    try:
        for index, (name, url) in enumerate(BOARDS):
            print(f"\n{index + 1}/{len(BOARDS)} {name}")
            html = fetch_html(driver, url)
            if html is None:
                try:
                    driver.quit()
                except Exception:
                    pass
                driver = setup_selenium()
                failures.append(name)
            else:
                text = extract_text(html)
                previous = load_text(url)
                new_roles = role_lines(text)
                if previous is None:
                    baselines.append(name)
                    save_text(url, text)
                else:
                    alert = role_alert(name, url, role_lines(previous), new_roles)
                    if alert:
                        alerts.append(alert)
                    if text != previous:
                        save_text(url, text)
            if index < len(BOARDS) - 1:
                time.sleep(2)
    finally:
        try:
            driver.quit()
        except Exception:
            pass
    write_reports(alerts, baselines, failures)


def main():
    process_boards()
    print(f"\nChecked {len(BOARDS)} boards. See changes.md.")


if __name__ == "__main__":
    main()
