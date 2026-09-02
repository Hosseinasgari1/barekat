"""Debug script: navigate to a category page and dump the DOM structure."""
import asyncio
import json
import sys
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1280, "height": 900}, locale="fa-IR")
        page = await context.new_page()

        print("Visiting snapp.market...")
        await page.goto("https://snapp.market", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        await page.mouse.click(50, 50)  # dismiss modal
        await page.wait_for_timeout(1000)

        print("Navigating to dairy/milk category...")
        await page.goto("https://snapp.market/shopping-list/dairy/milk?hasBanner=", wait_until="domcontentloaded")
        await page.wait_for_timeout(4000)

        # Scroll to load content
        for i in range(3):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1500)

        # Get full page info
        result = await page.evaluate('''() => {
            const info = {};
            
            // Count elements by type
            info.totalLinks = document.querySelectorAll('a').length;
            info.productLinks = document.querySelectorAll('a[href*="/product/"]').length;
            info.allImages = document.querySelectorAll('img').length;
            info.articles = document.querySelectorAll('article').length;
            
            // Get all product links with details
            info.products = [];
            const links = document.querySelectorAll('a[href*="/product/"]');
            for (const link of links) {
                const href = link.getAttribute('href') || '';
                info.products.push({
                    href: href.substring(0, 200),
                    text: (link.textContent || '').trim().substring(0, 150),
                    innerHTML_len: link.innerHTML.length,
                    childCount: link.children.length,
                    classes: link.className?.substring(0, 100),
                    parentClasses: link.parentElement?.className?.substring(0, 100),
                });
            }
            
            // Get all img elements details 
            info.images = [];
            const imgs = document.querySelectorAll('img[src*="product"], img[alt]');
            for (const img of imgs) {
                const src = img.getAttribute('src') || '';
                const alt = img.getAttribute('alt') || '';
                if (alt.length > 3 || src.includes('product')) {
                    info.images.push({
                        src: src.substring(0, 200),
                        alt: alt.substring(0, 100),
                        parentTag: img.parentElement?.tagName,
                        parentClasses: img.parentElement?.className?.substring(0, 80),
                    });
                }
            }
            
            // Get page HTML size and body structure 
            info.bodyHTML_len = document.body.innerHTML.length;
            info.rootDiv = document.querySelector('#root')?.children.length;
            info.title = document.title;
            info.url = window.location.href;
            
            // Get all unique class names that contain "product" (case insensitive)
            const productClasses = new Set();
            document.querySelectorAll('*').forEach(el => {
                if (el.className && typeof el.className === 'string') {
                    el.className.split(' ').forEach(cls => {
                        if (cls.toLowerCase().includes('product') || cls.toLowerCase().includes('card') || cls.toLowerCase().includes('item')) {
                            productClasses.add(cls);
                        }
                    });
                }
            });
            info.productClasses = Array.from(productClasses).slice(0, 50);
            
            return info;
        }''')

        print(f"URL: {result.get('url')}")
        print(f"Title: {result.get('title')}")
        print(f"Body HTML length: {result.get('bodyHTML_len')}")
        print(f"Root children: {result.get('rootDiv')}")
        print(f"Total links: {result.get('totalLinks')}")
        print(f"Product links: {result.get('productLinks')}")
        print(f"All images: {result.get('allImages')}")
        print(f"Articles: {result.get('articles')}")
        
        print(f"\nProduct-related CSS classes: {result.get('productClasses')}")
        
        print(f"\n=== Product Links ({len(result.get('products', []))}) ===")
        for p in result.get('products', [])[:20]:
            print(f"  href={p['href'][:80]}")
            print(f"    text={p['text'][:80]}")
            print(f"    classes={p['classes'][:80] if p.get('classes') else 'NONE'}")
            print(f"    parentClasses={p['parentClasses'][:80] if p.get('parentClasses') else 'NONE'}")
            print()
        
        print(f"\n=== Images ({len(result.get('images', []))}) ===")
        for img in result.get('images', [])[:10]:
            print(f"  alt={img['alt'][:60]} src={img['src'][:80]}")

        await browser.close()

asyncio.run(main())
