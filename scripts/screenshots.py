"""Capture README / Devpost screenshots from a running server.

    uvicorn app.main:app --port 8000 &
    python -m scripts.seed_demo_reports
    python scripts/screenshots.py          # writes docs/screenshots/*.png
"""

import asyncio
from pathlib import Path

from playwright.async_api import async_playwright

BASE = "http://localhost:8000"
OUT = Path(__file__).resolve().parent.parent / "docs" / "screenshots"


async def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        desk = await browser.new_page(viewport={"width": 1280, "height": 860}, device_scale_factor=2)
        await desk.goto(f"{BASE}/?lang=en")
        await desk.wait_for_timeout(800)
        await desk.screenshot(path=OUT / "1-ready.png")

        await desk.goto(f"{BASE}/?lang=en&demo=police-bukit-aman&voice=0&autostart=1")
        await desk.wait_for_selector("body[data-level=caution], body[data-level=high]", timeout=60000)
        await desk.wait_for_timeout(600)
        await desk.screenshot(path=OUT / "2-caution.png")
        await desk.wait_for_selector("#numBlock:not([hidden])", timeout=60000)
        await desk.wait_for_timeout(1500)
        await desk.screenshot(path=OUT / "3-scam-warning.png")

        phone = await browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=3, is_mobile=True)
        await phone.goto(f"{BASE}/?lang=ms&demo=lhdn-tax&voice=0&autostart=1")
        await phone.wait_for_selector("body[data-level=high]", timeout=60000)
        await phone.wait_for_timeout(1200)
        await phone.screenshot(path=OUT / "4-mobile-amaran.png")

        legit = await browser.new_page(viewport={"width": 1280, "height": 860}, device_scale_factor=2)
        await legit.goto(f"{BASE}/?lang=en&demo=real-bank&voice=0&autostart=1")
        await legit.wait_for_selector("#actionsDone:not([hidden])", timeout=60000)
        await legit.wait_for_timeout(500)
        await legit.screenshot(path=OUT / "5-legit-bank-call.png")

        dash = await browser.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=2)
        await dash.goto(f"{BASE}/dashboard")
        await dash.wait_for_timeout(1000)
        await dash.screenshot(path=OUT / "6-community-dashboard.png", full_page=True)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
