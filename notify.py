"""Send alert.txt to Telegram. No-op when there are no role changes."""

import json
import os
import urllib.request

LIMIT = 3500


def chunks(text: str) -> list[str]:
    blocks = text.split("\n\n")
    out: list[str] = []
    current = ""
    for block in blocks:
        piece = block.strip()
        if not piece:
            continue
        if len(piece) > LIMIT:
            piece = piece[: LIMIT - 1] + "…"
        if current and len(current) + 2 + len(piece) > LIMIT:
            out.append(current)
            current = piece
        elif current:
            current = current + "\n\n" + piece
        else:
            current = piece
    if current:
        out.append(current)
    return out


def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat:
        print("Telegram secrets missing. Nothing sent.")
        return
    if not os.path.exists("alert.txt"):
        print("No alert file.")
        return
    text = open("alert.txt", encoding="utf-8").read().strip()
    if not text or text == "NONE":
        print("No role changes to send.")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    for part in chunks(text):
        body = json.dumps(
            {
                "chat_id": chat,
                "text": part,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }
        ).encode()
        request = urllib.request.Request(
            url, data=body, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode())
        if not payload.get("ok"):
            raise SystemExit("Telegram rejected a role alert.")
        print("Telegram accepted a role alert.")


if __name__ == "__main__":
    main()
