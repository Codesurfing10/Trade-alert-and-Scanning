# Trade-alert-and-Scanning

A lightweight, static **trade alert scanner** that runs fully in the browser and can be deployed to **GitHub Pages**.

## Scanner

Open `index.html` and paste rows in this format:

`SYMBOL,PRICE,CHANGE_PERCENT,VOLUME`

Set thresholds for:
- Minimum % change
- Minimum volume

Then click **Run Scan** to see alert results.

## GitHub Pages deployment

This repo includes a workflow at:

`/.github/workflows/deploy-pages.yml`

It deploys the scanner site on pushes to `main` (and supports manual runs with `workflow_dispatch`).

To enable Pages in GitHub:
1. Go to **Settings → Pages**
2. Set **Source** to **GitHub Actions**
3. Push to `main` (or run the workflow manually)
