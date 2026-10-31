import asyncio
from playwright.async_api import async_playwright
OUT = "/tmp/claude-0/vid/frames"
B = "http://localhost:8000"

async def run_call(ctx, name, url, warn_off=True):
    pg = await ctx.new_page()
    await pg.clock.install()
    await pg.goto(url)
    await pg.wait_for_timeout(1200)
    await pg.clock.run_for(500)
    await pg.evaluate("document.getElementById('voiceWarn').checked=false")
    await pg.screenshot(path=f"{OUT}/{name}_0.jpg", type="jpeg", quality=92)
    await pg.click("#startBtn")
    seen = 0
    for _ in range(400):
        await pg.clock.run_for(300)
        await pg.wait_for_timeout(120)
        n = await pg.locator("#transcript .line").count()
        if n > seen:
            seen = n
            await pg.wait_for_timeout(1100)
            await pg.screenshot(path=f"{OUT}/{name}_{n}.jpg", type="jpeg", quality=92)
            print(name, n, await pg.get_attribute("body", "data-level"), flush=True)
        if await pg.is_visible("#actionsDone"):
            await pg.wait_for_timeout(900)
            await pg.screenshot(path=f"{OUT}/{name}_end.jpg", type="jpeg", quality=92)
            break
    return pg

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={"width": 1280, "height": 720}, device_scale_factor=1.5)
        pg = await run_call(ctx, "police", f"{B}/?demo=police-bukit-aman&lang=ms&voice=0")
        # numbers block view in end state
        await pg.evaluate("document.getElementById('numBlock').scrollIntoView({block:'center'})")
        await pg.wait_for_timeout(500)
        await pg.screenshot(path=f"{OUT}/police_numbers.jpg", type="jpeg", quality=92)
        wa = await pg.get_attribute("#waBtn", "href")
        print("WA", wa)
        await run_call(ctx, "bank", f"{B}/?demo=real-bank&lang=en&voice=0")
        d = await ctx.new_page()
        await d.goto(f"{B}/dashboard"); await d.wait_for_timeout(1200)
        await d.screenshot(path=f"{OUT}/dash.jpg", type="jpeg", quality=92)
        await b.close()
asyncio.run(main())
