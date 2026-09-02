"""Debug script to select an address in snapp.market."""
import asyncio
from playwright.async_api import async_playwright
import sys

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

        print("Visiting snapp.market...")
        await page.goto("https://snapp.market")
        await page.wait_for_timeout(5000)

        # Look for the address modal and select a location
        print("Trying to set location via UI...")
        try:
            # Click the location button in header or modal
            location_btns = await page.query_selector_all("button:has-text('انتخاب آدرس'), button:has-text('ثبت آدرس')")
            if location_btns:
                print("Clicking location button...")
                await location_btns[0].click()
                await page.wait_for_timeout(2000)
            
            # Click "Use my current location" if available
            my_loc_btn = await page.query_selector("button:has-text('مکان یاب'), button:has-text('موقعیت من')")
            if my_loc_btn:
                print("Clicking 'My Location'...")
                await my_loc_btn.click()
                await page.wait_for_timeout(3000)
                
                # Confirm location
                confirm_btn = await page.query_selector("button:has-text('تایید'), button:has-text('ثبت')")
                if confirm_btn:
                    print("Confirming location...")
                    await confirm_btn.click()
                    await page.wait_for_timeout(3000)
        except Exception as e:
            print(f"Error setting location: {e}")

        # Check local storage for location data
        print("\nLocal Storage:")
        ls = await page.evaluate("() => JSON.stringify(window.localStorage, null, 2)")
        print(ls[:500] + "..." if len(ls) > 500 else ls)

        # Check cookies
        print("\nCookies:")
        cookies = await context.cookies()
        for c in cookies:
            print(f"{c['name']}: {c['value'][:50]}")

        print("\nNavigating to dairy/milk category...")
        await page.goto("https://snapp.market/shopping-list/dairy/milk?hasBanner=")
        await page.wait_for_timeout(5000)

        # See if we have products now
        products = await page.evaluate('''() => {
            return document.querySelectorAll('a[href*="/product/"]').length;
        }''')
        print(f"Product links found: {products}")

        await browser.close()

asyncio.run(main())
