"""
Capture clean screenshots of every PF9 app demo for use in marketing
videos, ads, and the storefront screenshot library that the Cowork
Creative agent draws from.

Setup (one time):
    pip install playwright
    playwright install chromium

Run:
    python tools/capture_screenshots.py
    python tools/capture_screenshots.py --variant video_1080p
    python tools/capture_screenshots.py --target flowtrack
    python tools/capture_screenshots.py --variant social_square --target shiftlog

Outputs land in ./screenshots/ as PNGs named:
    {target}_{variant}_{YYYYMMDD}.png

The Creative agent (see AGENTS.md Agent 6) consumes the latest dated
file per target+variant.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

CONFIG_PATH = Path(__file__).parent / "screenshot_targets.json"


def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def capture_one(page, target, viewport, wait_ms, output_dir, variant_name):
    name = target["name"]
    url = target["url"]
    full_page = target.get("full_page", False)
    target_wait = target.get("wait_ms", wait_ms)

    page.set_viewport_size(viewport)

    try:
        page.goto(url, wait_until="networkidle", timeout=30000)
    except PWTimeout:
        page.goto(url, wait_until="load", timeout=30000)

    page.wait_for_timeout(target_wait)

    today = datetime.utcnow().strftime("%Y%m%d")
    filename = f"{name}_{variant_name}_{today}.png"
    out_path = output_dir / filename

    page.screenshot(path=str(out_path), full_page=full_page)
    print(f"  captured  {out_path.name}")
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Capture PF9 app demo screenshots")
    parser.add_argument("--variant", default="default",
                        help="Viewport variant from config (default, social_square, social_story, linkedin_feed, video_1080p)")
    parser.add_argument("--target", default=None,
                        help="Single target name to capture (default: all)")
    parser.add_argument("--headed", action="store_true",
                        help="Run with visible browser (debugging)")
    args = parser.parse_args()

    config = load_config()

    if args.variant == "default":
        viewport = config["default_viewport"]
    elif args.variant in config["viewport_variants"]:
        viewport = config["viewport_variants"][args.variant]
    else:
        sys.exit(f"unknown variant: {args.variant}")

    targets = config["targets"]
    if args.target:
        targets = [t for t in targets if t["name"] == args.target]
        if not targets:
            sys.exit(f"unknown target: {args.target}")

    output_dir = (Path(__file__).parent / config["output_dir"]).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"variant: {args.variant}  viewport: {viewport['width']}x{viewport['height']}")
    print(f"output:  {output_dir}")
    print(f"targets: {len(targets)}")

    failures = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=not args.headed)
        context = browser.new_context(device_scale_factor=2)
        page = context.new_page()

        for target in targets:
            print(f"\n{target['name']}  {target['url']}")
            try:
                capture_one(page, target, viewport, config["default_wait_ms"], output_dir, args.variant)
            except Exception as e:
                print(f"  FAILED    {e}")
                failures.append((target["name"], str(e)))

        browser.close()

    print(f"\ndone. {len(targets) - len(failures)}/{len(targets)} captured.")
    if failures:
        print("failures:")
        for name, err in failures:
            print(f"  {name}: {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
