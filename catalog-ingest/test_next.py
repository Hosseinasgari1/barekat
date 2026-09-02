"""Discover _next/data calls."""
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1280, "height": 900})
        page = await context.new_page()

        async def log_response(response):
            if "_next/data" in response.url or "api" in response.url or "svc" in response.url:
                print(f"[{response.status}] {response.url[:150]}")

        page.on("response", log_response)

        print("Visiting snapp.market...")
        await page.goto("https://snapp.market")
        await page.wait_for_timeout(5000)

        print("Trying to set address...")
        # Since the map modal opens automatically, let's try to find and click the confirm button
        try:
            # Wait for map to load
            await page.wait_for_selector(".leaflet-container, canvas", timeout=10000)
            print("Map found. Clicking center bottom to confirm...")
            await page.mouse.click(640, 800)
            await page.wait_for_timeout(3000)
        except Exception as e:
            print(f"Map not found: {e}")

        # Navigate to a category
        print("Navigating to dairy...")
        await page.goto("https://snapp.market/shopping-list/dairy/milk")
        await page.wait_for_timeout(5000)

        # Check __NEXT_DATA__
        next_data = await page.evaluate('''() => {
            const el = document.getElementById('__NEXT_DATA__');
            return el ? el.textContent : null;
        }''')
        
        if next_data:
            print(f"Found __NEXT_DATA__, length: {len(next_data)}")
            with open("next_data.json", "w", encoding="utf-8") as f:
                f.write(next_data)
        else:
            print("No __NEXT_DATA__ found!")

        await browser.close()

asyncio.run(main())
