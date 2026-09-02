"""Navigate to snapp.market category pages and extract product data from the rendered HTML."""
import asyncio
import json
import sys
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Visit the site
        print("Visiting snapp.market...")
        await page.goto("https://snapp.market")
        await page.wait_for_timeout(5000)

        # Navigate to a supermarket category page
        print("\nNavigating to dairy category...")
        await page.goto("https://snapp.market/supermarket/dairy")
        await page.wait_for_timeout(5000)

        # Check for Redux store / global state
        print("\nChecking for global state...")
        state_info = await page.evaluate('''() => {
            const results = {};
            
            // Check all window properties for state
            for (const key of Object.keys(window)) {
                if (key.startsWith('__') || key.includes('STATE') || key.includes('DATA') || key.includes('STORE')) {
                    results[key] = typeof window[key];
                }
            }
            
            // Check for React fiber / internal state
            const mainEl = document.querySelector('#__next') || document.querySelector('#root') || document.querySelector('#app');
            if (mainEl) {
                results['_mainElement'] = mainEl.id || mainEl.tagName;
                const reactKey = Object.keys(mainEl).find(k => k.startsWith('__reactFiber') || k.startsWith('__reactInternalInstance'));
                results['_hasReact'] = !!reactKey;
            }
            
            return results;
        }''')
        print(f"State: {json.dumps(state_info, indent=2)}")

        # Extract product data from HTML
        print("\nExtracting products from page HTML...")
        products = await page.evaluate('''() => {
            const products = [];
            
            // Try common product card selectors
            const selectors = [
                '[data-testid*="product"]',
                '[class*="product"]',
                '[class*="Product"]',
                'article',
                '.product-card',
                '.item-card',
                '[class*="card"]',
                '[class*="Card"]',
            ];
            
            let found = null;
            for (const sel of selectors) {
                const els = document.querySelectorAll(sel);
                if (els.length > 0) {
                    found = {selector: sel, count: els.length};
                    break;
                }
            }
            
            // Also get all links to products
            const links = [];
            document.querySelectorAll('a[href*="/p/"]').forEach(a => {
                links.push({
                    href: a.href,
                    text: a.textContent?.trim()?.substring(0, 100)
                });
            });
            
            // Get all product-like elements
            const allCards = document.querySelectorAll('a');
            const productLinks = [];
            allCards.forEach(a => {
                const href = a.href || '';
                const text = a.textContent?.trim() || '';
                if (href.includes('/p/') || href.includes('/product/')) {
                    productLinks.push({href: href.substring(0, 200), text: text.substring(0, 100)});
                }
            });
            
            return {
                found,
                productLinks: productLinks.slice(0, 20),
                title: document.title,
                bodyLen: document.body.innerHTML.length,
                url: window.location.href,
            };
        }''')
        print(f"Page title: {products.get('title')}")
        print(f"URL: {products.get('url')}")
        print(f"Body length: {products.get('bodyLen')}")
        print(f"Found selector: {products.get('found')}")
        print(f"Product links ({len(products.get('productLinks', []))}):")
        for pl in products.get('productLinks', [])[:10]:
            print(f"  {pl['href'][:100]} - {pl['text'][:60]}")

        # Now let's try navigating to a specific vendor/store page
        print("\n\n=== Trying vendor/store pages ===")
        
        # Scroll to load more products
        for i in range(3):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)
        
        # Re-extract after scrolling
        products2 = await page.evaluate('''() => {
            const productLinks = [];
            document.querySelectorAll('a').forEach(a => {
                const href = a.href || '';
                const text = a.textContent?.trim() || '';
                if (href.includes('/p/') || href.includes('/product/')) {
                    productLinks.push({href: href.substring(0, 200), text: text.substring(0, 100)});
                }
            });
            return {productLinks: productLinks.slice(0, 50)};
        }''')
        print(f"\nAfter scrolling, product links: {len(products2.get('productLinks', []))}")
        for pl in products2.get('productLinks', [])[:10]:
            print(f"  {pl['href'][:100]} - {pl['text'][:60]}")

        await browser.close()

asyncio.run(main())
