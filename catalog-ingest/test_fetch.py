"""Test page.evaluate fetch for products."""
import asyncio
import json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="fa-IR",
        )
        page = await context.new_page()

        print("Visiting snapp.market...")
        await page.goto("https://snapp.market", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)

        print("Fetching products via page.evaluate...")
        
        # Test category products (milk = 731224)
        cat_data = await page.evaluate('''async () => {
            try {
                // Must pass lat/long or vendorCode to get products
                const r = await fetch("https://svc.snapp.market/express-search/products/by-category?category_id=731224&page=0&page_size=50&client=PWA&deviceType=PWA&appVersion=1.397.12&lat=35.773643&long=51.418311");
                return {status: r.status, body: await r.json()};
            } catch (e) {
                return {status: 500, error: e.toString()};
            }
        }''')
        
        with open("cat_products.json", "w", encoding="utf-8") as f:
            json.dump(cat_data, f, ensure_ascii=False, indent=2)
            
        print(f"Category fetch status: {cat_data.get('status')}")

        # Test search products
        search_data = await page.evaluate('''async () => {
            try {
                const term = encodeURIComponent("شیر");
                const r = await fetch("https://svc.snapp.market/express-search/products/by-search?page=0&page_size=50&q=" + term + "&client=PWA&deviceType=PWA&appVersion=1.397.12&lat=35.773643&long=51.418311");
                return {status: r.status, body: await r.json()};
            } catch (e) {
                return {status: 500, error: e.toString()};
            }
        }''')

        with open("search_products.json", "w", encoding="utf-8") as f:
            json.dump(search_data, f, ensure_ascii=False, indent=2)
            
        print(f"Search fetch status: {search_data.get('status')}")

        await browser.close()

asyncio.run(main())
