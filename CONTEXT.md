# JustApply

Job-page watcher. Copied into JERVIS on 2026-11-07 from `C:\Users\jerie\Documents\GitHub\JustApply`.

Not a node. Not a JERVIS route. Do not port Selenium, Telegram, or this workflow into the Fastify/React shell.

Read this file before editing the scraper, the workflow, or the Telegram setup.

## What it does

`daily_scraper.py` opens each URL in headless Chrome, strips scripts and styles, and compares the text to `text_storage/<md5 of url>.txt`. It rewrites `changes.md` with only the latest run. A new URL's first run stores a baseline and reports no previous version.

Python deps: `requirements.txt` (`selenium`, `webdriver-manager`, `beautifulsoup4`). Needs Python 3.11+ and Google Chrome.

## Where the live job runs

This folder is a file copy. It has no `.git`. The GitHub Action does not run from here.

| Copy | Role |
|---|---|
| `junnengsoo/JustApply` | Upstream. Last commit 2026-01-04. GitHub login **Nimastic** has pull only. Cannot push or set Actions secrets. Scheduled runs stopped after the repo went quiet. |
| `Nimastic/JustApply` | Operating fork. https://github.com/Nimastic/JustApply |
| `JustApply/` in JERVIS | Read-only handoff of the upstream tree, including January `changes.md` and `text_storage/`. |

Workflow file: `.github/workflows/daily_scrape.yml`, name **Daily Scraper**.

- Cron: `0 3 * * *` (03:00 UTC). `workflow_dispatch` is also on.
- On a new fork the workflow starts as `disabled_fork`. It was enabled on 2026-11-07. State was `active` after `PUT /repos/Nimastic/JustApply/actions/workflows/410295235/enable`.
- The job checks out the fork, runs `python daily_scraper.py`, and commits `changes.md` plus `text_storage/` only when the diff is non-empty. Committer is `github-actions[bot]`.
- Telegram runs only when that commit happens (`steps.commit.outputs.no_changes == 'false'`). A clean run sends nothing.
- Last successful fork run: https://github.com/Nimastic/JustApply/actions/runs/42370030217 (2026-11-07, workflow_dispatch, about 4m18s). Telegram returned `ok: true` for the scrape message.

The fork's `changes.md` and `text_storage/` are newer than this folder. This folder still shows `## 2026-01-04 04:12:35`. Do not treat this copy as the live baseline.

## Telegram

- Bot: `@jervisjobbot` (display name Jobs). `getMe` succeeded on 2026-11-07.
- Chat: Jeriel's private Telegram (`username` jerielchan). A test message was delivered the same day (`message_id` 2), then the scrape alert (`message_id` 3).
- Secret names on **Nimastic/JustApply** only: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.
- Do not write the token or chat id into git, `AGENTS.md`, or this file. Rotate the token in `@BotFather` with `/revoke` if it leaks, then `gh secret set TELEGRAM_BOT_TOKEN --repo Nimastic/JustApply`.
- `junnengsoo/JustApply` does not have these secrets. Setting them there from the Nimastic login returns 403.

The notify step interpolates `changes.md` into a JSON string and sets `parse_mode` to HTML. Quotes or `<` in the diff can break the payload. `curl` is not run with `-f`, so the step can look green when Telegram rejects the body. Read the step log for `"ok":true` before calling a run delivered.

## Watched URLs

`boards.py` is the list. One full-time career board per company, copied from `resume/recruiting/apply-later.md`, `apply-robotics.md`, and the companies with a saved application. Intern filters are gone (Stripe university, Google intern, Meta internship, Qube students, Point72 internships, HRT students, Jane Street students-and-new-grads, Balyasny internships, NVIDIA internships). A single job id was replaced with that company's board. LinkedIn, gov forms, Anduril, and Shield AI are not watched. The July practice list (DBS, Deloitte, EY, KPMG, Accenture) is not watched.

Caladan was on the old scraper and is not in the tracker, so it is gone.

NYC pages are extra watches, not replacements: Jane Street open roles filtered to New York, Stripe New York, IMC US, and Google, Meta, Apple, and Amazon New York software searches. Company-wide boards that already list every office stay as they are. A new NYC page stores a baseline on its first run and stays quiet that day.

## What Telegram sends

`daily_scraper.py` still stores the page text in `text_storage/`. The message is not that diff. A line is a role when it looks like a job title. Cookie banners, certificate errors, and intern titles are dropped. The alert names the company, lists titles that appeared (`+`) and titles that disappeared (`closed:`), and links the board. `alert.txt` is `NONE` when nothing qualifies, and `notify.py` sends nothing.

The first run of a new board stores a baseline and stays quiet. The next run is the one that can name a new title.

A URL added only in this JERVIS folder does not change the daily job. The Action runs the fork's `boards.py`. Push to `Nimastic/JustApply` only if Jeriel asks.

## Run it locally

```powershell
cd C:\Users\jerie\Desktop\JERVIS\JustApply
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python daily_scraper.py
```

`venv/` is gitignored by this project's own `.gitignore` (`/venv`). Inside the JERVIS repo that pattern does not apply. Do not commit a venv.

Headless is on in `setup_selenium()`. Comment out `--headless` only to watch Chrome. Page wait is 15 seconds inside `fetch_page()`. There is a 2 second pause between URLs.

## Agent rules

- Commit or push only if Jeriel asks. Never commit the bot token.
- Do not scrape or paste proprietary problem bodies. These URLs are public career pages.
- Prefer editing the fork when the goal is "tomorrow's Telegram." Editing only this folder changes nothing on the schedule.
- Upstream `junnengsoo/JustApply` stays read-only from the Nimastic login.
