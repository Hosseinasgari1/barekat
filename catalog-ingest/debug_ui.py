"""Debug script to properly set address via UI interaction."""
import asyncio
import json
import sys
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="fa-IR",
            geolocation={"longitude": 51.418311, "latitude": 35.773643},
            permissions=["geolocation"]
        )
        page = await context.new_page()

        print("Visiting address modal...")
        await page.goto("https://snapp.market/modals/address/add", wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)
        
        # Check if we see a map and the confirm button
        buttons = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('button')).map(b => ({
                text: b.textContent?.trim(),
                className: b.className
            }));
        }''')
        print(f"Buttons found on address modal: {json.dumps(buttons, ensure_ascii=False)}")
        
        # Click the confirm button
        print("Clicking 'تایید' button...")
        try:
            btn = await page.wait_for_selector("button:has-text('تایید')", timeout=3000)
            if btn:
                await btn.click()
            else:
                await page.mouse.click(500, 800)
        except Exception as e:
            print(f"Failed to click button: {e}")
            await page.mouse.click(500, 800)
            
        await page.wait_for_timeout(3000)
        
        # Go to home and wait for load
        print("Going to home...")
        await page.goto("https://snapp.market", wait_until="networkidle")
        await page.wait_for_timeout(5000)
        
        # Check URL after home
        print(f"Current URL: {page.url}")
        
        # See if there's any vendor/supermarket selected
        vendor = await page.evaluate('''() => {
            const h = document.querySelector('header');
            return h ? h.textContent : null;
        }''')
        print(f"Header text: {vendor}")

        await browser.close()

asyncio.run(main())
