"""Debug DOM for snappmarket with location set."""
import asyncio
import json
import sys
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 925, "height": 952},
            locale="fa-IR",
            geolocation={"longitude": 51.418311, "latitude": 35.773643},
            permissions=["geolocation"]
        )
        page = await context.new_page()

        print("Visiting snapp.market address modal...")
        await page.goto("https://snapp.market/modals/address/add", wait_until="domcontentloaded")
        await page.wait_for_timeout(4000)
        
        print("Clicking confirm location...")
        await page.mouse.click(500, 890)
        await page.wait_for_timeout(3000)
        
        print("Navigating to dairy/milk category...")
        await page.goto("https://snapp.market/shopping-list/dairy/milk?hasBanner=", wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)

        # Scroll to load content
        for i in range(3):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1500)

        # Get all links
        result = await page.evaluate('''() => {
            const links = [];
            document.querySelectorAll('a').forEach(a => {
                const href = a.getAttribute('href') || '';
                const text = a.textContent?.trim() || '';
                // Look for links that might be products
                if (href.includes('/p/') || href.includes('/product') || href.includes('/item')) {
                    links.push({href, text: text.substring(0, 100)});
                }
            });
            return { links: links.slice(0, 50) };
        }''')
        
        print(f"\nPotential product links ({len(result.get('links', []))}):")
        for link in result.get('links', []):
            print(f"  {link['href']} - {link['text']}")

        # If no product links, let's look at the structure of articles/cards
        print("\nLet's check articles/divs...")
        structure = await page.evaluate('''() => {
            const items = [];
            document.querySelectorAll('article, [class*="product"], [class*="card"]').forEach(el => {
                items.push({
                    tag: el.tagName,
                    classes: el.className,
                    text: el.textContent?.trim().substring(0, 50),
                    html_snippet: el.innerHTML.substring(0, 100).replace(/\\n/g, '')
                });
            });
            return items.slice(0, 10);
        }''')
        for item in structure:
            print(f"  {item['tag']} ({item['classes']}): {item['text']}")
            print(f"    {item['html_snippet']}")

        await browser.close()

asyncio.run(main())
