import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        await stealth_async(page)
        
        # Go to main site first to get WAF cookies
        print("Navigating to snapp.market...")
        await page.goto('https://snapp.market')
        await page.wait_for_timeout(3000)
        
        print("Navigating to API...")
        page_resp = await page.goto('https://api.snapp.market/v1/products?category_id=1&categoryId=1&page=1&page_size=24&limit=24&offset=0')
        print("Page Goto Status:", page_resp.status if page_resp else None)
        
        await browser.close()

asyncio.run(main())
