from pathlib import Path
from playwright.sync_api import sync_playwright

# Root folder: the "Stategies" directory where this script lives
OUTPUT_ROOT = Path(__file__).resolve().parent

# Slug → URL map (slug also matches the folder name)
STRATEGIES = {
    "pw-trend-trading-strategy": "https://fx-list.com/blog/strategies/pw-trend-trading-strategy",
    "master-trend-trading-strategy": "https://fx-list.com/blog/strategies/master-trend-trading-strategy",
    "rsi-failure-swing-trading-strategy": "https://fx-list.com/blog/strategies/rsi-failure-swing-trading-strategy",
    "ifibonacci-short-term-trading-strategy": "https://fx-list.com/blog/strategies/ifibonacci-short-term-trading-strategy",
    "short-term-moving-average-trading-strategy": "https://fx-list.com/blog/strategies/short-term-moving-average-trading-strategy",
    "trendline-break-macd-cross-trading-strategy": "https://fx-list.com/blog/strategies/trendline-break-macd-cross-trading-strategy",
    "macd-moving-average-trading-strategy": "https://fx-list.com/blog/strategies/macd-moving-average-trading-strategy",
    "economic-news-trading-strategy": "https://fx-list.com/blog/strategies/economic-news-trading-strategy",
    "macd-histogram-trading-strategy": "https://fx-list.com/blog/strategies/macd-histogram-trading-strategy",
    "bollinger-bands-swing-trading-strategy": "https://fx-list.com/blog/strategies/bollinger-bands-swing-trading-strategy",
    "day-trading-pivot-point-strategy": "https://fx-list.com/blog/strategies/day-trading-pivot-point-strategy",
    "forex-power-trading-strategy": "https://fx-list.com/blog/strategies/forex-power-trading-strategy",
    "rounding-pattern-reversal-trading-strategy": "https://fx-list.com/blog/strategies/rounding-pattern-reversal-trading-strategy",
    "short-covering-rally-trading-strategy": "https://fx-list.com/blog/strategies/short-covering-rally-trading-strategy",
    "three-phase-trading-strategy": "https://fx-list.com/blog/strategies/three-phase-trading-strategy",
    "channel-divergence-trading-strategy": "https://fx-list.com/blog/strategies/channel-divergence-trading-strategy",
    "1-2-3-reversal-pattern-trading-strategy": "https://fx-list.com/blog/strategies/1-2-3-reversal-pattern-trading-strategy",
    "tenkan-kijun-trading-cross-strategy": "https://fx-list.com/blog/strategies/tenkan-kijun-trading-cross-strategy",
    "kumo-break-trading-strategy": "https://fx-list.com/blog/strategies/kumo-break-trading-strategy",
    "wolfe-wave-trading-strategy": "https://fx-list.com/blog/strategies/wolfe-wave-trading-strategy",
    "macd-ema-trading-strategy": "https://fx-list.com/blog/strategies/macd-ema-trading-strategy",
    "parabolic-sar-indicator-trading-strategy": "https://fx-list.com/blog/strategies/parabolic-sar-indicator-trading-strategy",
    "pivot-points-trading-strategy": "https://fx-list.com/blog/strategies/pivot-points-trading-strategy",
    "fibonacci-intraday-trading-strategy": "https://fx-list.com/blog/strategies/fibonacci-intraday-trading-strategy",
    "pivot-oscillator-divergence-strategy": "https://fx-list.com/blog/strategies/pivot-oscillator-divergence-strategy",
    "high-low-channel-trading-strategy": "https://fx-list.com/blog/strategies/high-low-channel-trading-strategy",
    "price-channel-breakouts-strategy": "https://fx-list.com/blog/strategies/price-channel-breakouts-strategy",
}


def slug_to_title(slug: str) -> str:
    """Turn 'pw-trend-trading-strategy' → 'Pw Trend Trading Strategy'."""
    return slug.replace("-", " ").title()


def main() -> None:
    root = OUTPUT_ROOT

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for slug, url in STRATEGIES.items():
            folder = root / slug
            folder.mkdir(parents=True, exist_ok=True)

            # 1) Clean any old PDFs in that folder so we don't keep garbage names
            for pdf in folder.glob("*.pdf"):
                pdf.unlink()

            # 2) New consistent names
            pdf_path = folder / f"{slug}.pdf"
            md_path = folder / f"{slug}.md"

            print(f"Fetching {url}")
            print(f"  → PDF: {pdf_path}")
            print(f"  → MD : {md_path}")

            # Load the page
            page.goto(url, wait_until="networkidle")
            page.wait_for_timeout(2000)

            # Save PDF
            page.pdf(path=str(pdf_path), format="A4")

            # Grab main article text if possible, else fall back to body text
            text = ""
            article = page.query_selector("article")
            if article:
                text = article.inner_text()
            else:
                text = page.inner_text("body")

            title = slug_to_title(slug)
            md_content = f"# {title}\n\nSource: {url}\n\n{text}\n"

            md_path.write_text(md_content, encoding="utf-8")

        browser.close()


if __name__ == "__main__":
    main()