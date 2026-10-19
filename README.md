# Watch Time v1.10 — News Feed

This package adds an English-language News page for anime, movie, and TV news, plus an automatic RSS-to-JSON updater for GitHub Pages.

## Install in an existing repository

This ZIP is arranged for a common GitHub Pages setup where `index.html` is in the repository root. Copy these files/folders into the root of your existing repository and allow the new `index.html` to replace the old one:

- `index.html` — replace your current app HTML.
- `news.json` — add this file.
- `scripts/update_news.py` — add this script.
- `.github/workflows/update-news.yml` — add this workflow (GitHub only detects workflows in the repository-root `.github/workflows/` folder).

Keep your existing `manifest.json`, `sw.js`, `icons/`, and other PWA files. The app's existing localStorage keys are unchanged. Back up your library from Settings before updating as usual.

> If your GitHub Pages app is published from a subfolder instead of the repository root, keep `index.html` and `news.json` together in that published folder and adjust the workflow script/output paths to match it. If you share your repository structure or URL, I can tailor the paths exactly.

## Enable automatic updates

1. Commit/push the files above to the same GitHub repository that publishes Watch Time.
2. Open **Settings → Actions → General**. Ensure workflows are allowed and repository workflow permissions permit writing contents. This workflow requests `contents: write`; organization policy may override it.
3. Open **Actions → Update News Feed → Run workflow** and run it once manually.
4. When it finishes, it writes `news.json` and commits the refreshed headlines automatically.
5. Open Watch Time and select **News**. Tap Refresh if needed.

GitHub Actions then refreshes the feed every six hours (scheduled runs may be delayed). No TMDB token or paid News API key is needed for the News page.

## RSS sources

- Anime News Network: `https://www.animenewsnetwork.com/news/rss.xml?ann-edition=us`
- Variety Film: `https://variety.com/v/film/feed/`
- Variety TV: `https://variety.com/v/tv/feed/`
- The Hollywood Reporter: `https://www.hollywoodreporter.com/feed/`

The app displays headlines, short excerpts, publisher attribution, dates, and links to original articles; it does not copy full articles. Images are only used when a feed includes an image URL and are loaded from the publisher's URL, not hosted in this repository.

## Notes

- The browser reads the local `news.json` file rather than fetching RSS feeds directly, avoiding browser CORS limitations.
- Categories are inferred from source and headline/excerpt keywords, so occasional category mismatches are possible.
- If one publisher's feed fails, the updater logs the issue and continues if other feeds succeed.
- The included `news.json` starts empty; run the workflow once to populate live stories.
