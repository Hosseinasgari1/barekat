"""Fetch products directly using the newly discovered API endpoint via context.request."""
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

        print("Visiting snapp.market address modal...")
        await page.goto("https://snapp.market/modals/address/add", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        
        print("Clicking confirm location...")
        await page.mouse.click(640, 800)
        await page.wait_for_timeout(3000)

        # Get UDID from cookies
        cookies = await context.cookies()
        udid = next((c['value'] for c in cookies if c['name'] == 'UDID'), 'dummy-udid')
        print(f"UDID: {udid}")

        url = f"https://svc.snapp.market/express-search/v1/pb/products?category_slug=dairy&sub_category_slug=milk&page=0&size=10&client=PWA&deviceType=PWA&appVersion=1.397.12&UDID={udid}&lat=35.773643&long=51.418311"
        print(f"Fetching {url}")

        resp = await context.request.get(url)
        print(f"Status: {resp.status}")
        
        if resp.status == 200:
            try:
                data = await resp.json()
                print(f"Keys: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                with open("pb_products.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                # Check for product arrays
                for k, v in (data.items() if isinstance(data, dict) else []):
                    if isinstance(v, list) and v:
                        print(f"Array '{k}' with {len(v)} items. First item keys: {list(v[0].keys())}")
            except Exception as e:
                print(f"JSON decode failed: {e}")
                
                # It might be protobuf if the pb stands for protobuf!
                text = await resp.text()
                print(f"Text sample: {text[:200]}")
                with open("pb_products.raw", "wb") as f:
                    f.write(await resp.body())
        else:
            print(await resp.text())

        await browser.close()

asyncio.run(main())
