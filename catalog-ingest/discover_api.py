"""Discover snapp.market product API by navigating category pages and intercepting all traffic."""
import asyncio
import json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        captured = []
        product_payloads = []

        async def handle_response(response):
            url = response.url
            status = response.status
            ct = response.headers.get("content-type", "")
            if "static.snapp" in url or "kafka" in url or "matomo" in url:
                return
            if "tile.snappmaps" in url or ".js" in url or ".css" in url or ".woff" in url:
                return
            if ".png" in url or ".jpg" in url or ".webp" in url or ".svg" in url:
                return
            if "sentry" in url:
                return
            
            body = None
            try:
                body = await response.json()
            except:
                pass
            
            entry = {"url": url[:400], "status": status, "ct": ct[:80]}
            if body:
                if isinstance(body, dict):
                    entry["keys"] = list(body.keys())[:20]
                elif isinstance(body, list):
                    entry["type"] = f"list[{len(body)}]"
                    
                # Check for product data
                body_str = json.dumps(body, ensure_ascii=False)[:500]
                if any(kw in body_str for kw in ["product", "title", "price", "قیمت"]):
                    entry["has_products"] = True
                    product_payloads.append({"url": url[:400], "body": body})
            
            captured.append(entry)
            print(f"[{status}] {url[:150]}")

        page.on("response", handle_response)

        # 1. Get the token first
        print("=== Step 1: Landing page ===")
        await page.goto("https://snapp.market")
        await page.wait_for_timeout(5000)

        # 2. Get categories  
        print("\n=== Step 2: Get categories ===")
        cats_data = await page.evaluate('''async () => {
            const r = await fetch("https://svc.snapp.market/express-search/categories?client=PWA&deviceType=PWA&appVersion=1.397.12&lat=35.773643&long=51.418311");
            return await r.json();
        }''')
        
        categories = []
        if isinstance(cats_data, dict) and "categories" in cats_data:
            for cat in cats_data["categories"]:
                if isinstance(cat, dict):
                    categories.append({"id": cat.get("id"), "title": cat.get("title"), "slug": cat.get("slug")})
                    # Also get subcategories
                    for sub in (cat.get("sub_categories") or cat.get("children") or []):
                        if isinstance(sub, dict):
                            categories.append({"id": sub.get("id"), "title": sub.get("title"), "slug": sub.get("slug"), "parent": cat.get("title")})
        
        print(f"Found {len(categories)} categories")
        with open("snapp_categories.json", "w", encoding="utf-8") as f:
            json.dump(categories, f, ensure_ascii=False, indent=2)

        # 3. Try to search for products (the search API likely returns products)
        print("\n=== Step 3: Try search API ===")
        search_terms = ["شیر", "نان", "برنج", "ماکارونی", "روغن"]
        for term in search_terms:
            try:
                search_result = await page.evaluate('''async (term) => {
                    const r = await fetch("https://svc.snapp.market/express-search/products/by-search?page=1&page_size=50&q=" + encodeURIComponent(term) + "&client=PWA&deviceType=PWA&appVersion=1.397.12&lat=35.773643&long=51.418311");
                    return {status: r.status, body: await r.json()};
                }''', term)
                print(f"Search '{term}': status={search_result.get('status')}, keys={list(search_result.get('body', {}).keys())[:10] if isinstance(search_result.get('body'), dict) else 'not dict'}")
                if search_result.get("status") == 200:
                    product_payloads.append({"url": f"search?q={term}", "body": search_result["body"]})
            except Exception as e:
                print(f"Search '{term}' failed: {e}")
            
            # Also try category products endpoint
            try:
                cat_result = await page.evaluate('''async (term) => {
                    const r = await fetch("https://svc.snapp.market/express-search/products/by-category?page=1&page_size=50&category_id=1&client=PWA&deviceType=PWA&appVersion=1.397.12&lat=35.773643&long=51.418311");
                    return {status: r.status, body: await r.json()};
                }''', term)
                print(f"Category products: status={cat_result.get('status')}, keys={list(cat_result.get('body', {}).keys())[:10] if isinstance(cat_result.get('body'), dict) else 'not dict'}")
                if cat_result.get("status") == 200:
                    product_payloads.append({"url": "category_products", "body": cat_result["body"]})
                break  # Only need one category test
            except Exception as e:
                print(f"Category products failed: {e}")

        # 4. Try different product endpoints  
        print("\n=== Step 4: Try various product endpoints ===")
        endpoints = [
            "/express-search/products/by-category?category_id=1&page=1&page_size=50",
            "/express-search/products/by-search?q=milk&page=1&page_size=50",
            "/product-hub/categories",
            "/product-hub/products?category_id=1&page=1&page_size=50",
            "/express-home/mobile/v3/products?category_id=1",
            "/mobile/v4/product/categories",
            "/mobile/v4/categories",
        ]
        for ep in endpoints:
            try:
                result = await page.evaluate('''async (ep) => {
                    const r = await fetch("https://svc.snapp.market" + ep + "&client=PWA&deviceType=PWA&appVersion=1.397.12&lat=35.773643&long=51.418311");
                    return {status: r.status, body: await r.json()};
                }''', ep)
                print(f"  {ep[:80]}: status={result.get('status')}, type={type(result.get('body')).__name__}")
                if result.get("status") == 200:
                    body = result["body"]
                    if isinstance(body, dict):
                        print(f"    keys: {list(body.keys())[:15]}")
                    product_payloads.append({"url": ep, "body": result["body"]})
            except Exception as e:
                print(f"  {ep[:80]}: ERROR {str(e)[:80]}")

        # 5. Navigate to a category page and check __NEXT_DATA__
        print("\n=== Step 5: Check for SSR data ===")
        await page.goto("https://snapp.market/supermarket/dairy-eggs-bread")
        await page.wait_for_timeout(5000)
        
        try:
            ssr_data = await page.evaluate('''() => {
                const el = document.querySelector("script#__NEXT_DATA__");
                if (el) return JSON.parse(el.textContent);
                // Check for other SSR patterns
                if (window.__INITIAL_STATE__) return window.__INITIAL_STATE__;
                if (window.__PRELOADED_STATE__) return window.__PRELOADED_STATE__;
                return null;
            }''')
            if ssr_data:
                print("Found SSR data!")
                product_payloads.append({"url": "SSR_DATA", "body": ssr_data})
            else:
                print("No __NEXT_DATA__ or SSR data found")
        except Exception as e:
            print(f"SSR check failed: {e}")

        # Save everything
        with open("snapp_product_payloads.json", "w", encoding="utf-8") as f:
            json.dump(product_payloads, f, ensure_ascii=False, indent=2, default=str)
        print(f"\nSaved {len(product_payloads)} product-related payloads to snapp_product_payloads.json")
        
        with open("snapp_all_api.json", "w", encoding="utf-8") as f:
            json.dump(captured, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(captured)} total API calls to snapp_all_api.json")

        await browser.close()

asyncio.run(main())
