import os
from pathlib import Path


def main() -> None:
    # Base = the folder where this script lives
    base_dir = Path(__file__).resolve().parent

    # This is your existing strategies root:
    strategies_root = base_dir

    # Hubs to collect aliases
    pdf_hub = base_dir / "Strategy_PDFs"
    md_hub = base_dir / "Strategy_MDs"

    pdf_hub.mkdir(exist_ok=True)
    md_hub.mkdir(exist_ok=True)

    # Folders we do NOT treat as strategy folders
    ignore_dirs = {
        pdf_hub.name,
        md_hub.name,
        "__pycache__",
    }

    for item in strategies_root.iterdir():
        if not item.is_dir():
            continue
        if item.name in ignore_dirs:
            continue

        # Expect structure like:
        # Stategies/
        #   pw-trend-trading-strategy/
        #       pw-trend-trading-strategy.pdf
        #       pw-trend-trading-strategy.md

        # Link PDFs
        for pdf in item.glob("*.pdf"):
            target_link = pdf_hub / pdf.name
            if target_link.exists() or target_link.is_symlink():
                continue  # don't overwrite existing
            os.symlink(pdf, target_link)
            print(f"PDF alias: {target_link} -> {pdf}")

        # Link MDs
        for md in item.glob("*.md"):
            target_link = md_hub / md.name
            if target_link.exists() or target_link.is_symlink():
                continue
            os.symlink(md, target_link)
            print(f"MD alias: {target_link} -> {md}")


if __name__ == "__main__":
    main()