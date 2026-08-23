# Auto-updating Nifty 500 screener

The screener page loads its data from `data/data.json`. A scheduled job re-runs
`scripts/fetch_data.py`, which rewrites that file — so the page is always as
fresh as the last successful run, with no manual rebuilding.

```
index.html                     the screener (loads data/data.json at runtime)
data/data.json                 prices + betas, rewritten by the job
data/universe.json             cached NSE constituent list (fallback)
scripts/fetch_data.py          the fetcher
.github/workflows/update.yml   the schedule
```

---

## Option A — GitHub Pages + Actions (free, unattended)

1. **Create a repo** and push these files.
2. **Settings → Pages** → Source: *Deploy from a branch* → Branch: `main`, folder `/ (root)` → Save.
3. **Settings → Actions → General** → Workflow permissions → select **Read and write permissions** → Save.
   (Without this the job can't commit the refreshed data.)
4. **Actions tab** → *Update screener data* → **Run workflow** to trigger the first run.
5. Open `https://<your-username>.github.io/<repo>/`.

From then on the job runs on the schedule in `update.yml`:
* **every 15 minutes during market hours** (09:15–15:30 IST, Mon–Fri)
* **once after the close** (15:45 IST) for the settled end-of-day snapshot

The page also re-checks `data.json` every 5 minutes while open, and has a
**refresh now** link in the header.

### Honest notes about the schedule
* GitHub's cron is **best-effort** — runs can be delayed by several minutes at
  busy times. It is not a low-latency feed.
* Scheduled workflows are **paused after 60 days of repo inactivity**; push any
  commit (or hit Run workflow) to resume.
* Free-tier Actions minutes are generous for this job (~1–2 min per run), but
  every-15-minutes adds up; widen the cron if you want to use fewer.

## Option B — your own machine or VPS (guaranteed timing)

```bash
pip install yfinance pandas numpy
python scripts/fetch_data.py          # writes data/data.json
python -m http.server 8000            # then open http://localhost:8000
```

Add to `crontab -e` (times in IST on an IST-configured machine):

```cron
*/15 9-15 * * 1-5  cd /path/to/repo && /usr/bin/python3 scripts/fetch_data.py
45   15  * * 1-5   cd /path/to/repo && /usr/bin/python3 scripts/fetch_data.py
```

**Opening `index.html` directly from disk will not work** — browsers block
`fetch` on `file://` URLs. Serve the folder (as above) or use the Pages URL.

---

## What the data is (and isn't)

* Source is Yahoo Finance daily bars (free, **delayed**, no bid/ask). During
  market hours a "15-minute refresh" therefore picks up the latest *delayed
  daily bar*, not true intraday ticks. For real intraday with bid/ask you need
  a broker feed (Zerodha Kite, Upstox — keyed, paid); swap the fetch call in
  `fetch_data.py` and the rest of the pipeline is unchanged.
* Cap labels come from NSE's own index files (Nifty 100 / Midcap 150 /
  Smallcap 250), so Large/Mid/Small are the official classification.
* Betas are computed on **date-aligned** returns vs ^NSEI in pandas. Aligning by
  position instead of date silently destroys the correlation — that is why this
  is done in Python, not in the browser.
* If a run fails to fetch anything, the script exits without overwriting
  `data.json`, so the page keeps showing the last good snapshot.

Everything here is a statistical description of recent price behaviour.
**It is not investment advice.**
