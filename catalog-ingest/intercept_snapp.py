import asyncio
from playwright.async_api import async_playwright
import json

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        print("Navigating to a category page on snapp.market...")
        
        products = []
        
        # Intercept responses
        async def handle_response(response):
            if "products" in response.url or "category" in response.url or "graphql" in response.url:
                if response.status == 200:
                    try:
                        content = await response.json()
                        print(f"Got JSON from {response.url[:100]}")
                        # naive check
                        str_content = str(content)
                        if "title" in str_content and "price" in str_content:
                            products.append(content)
                    except:
                        pass
        
        page.on("response", handle_response)
        
        await page.goto('https://snapp.market/c/1')
        print("Waiting to load and for WAF...")
        await page.wait_for_timeout(10000)
        
        # scroll to trigger more
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(5000)
        
        print(f"Captured {len(products)} potential product JSON payloads")
        if products:
            with open("snapp_intercepted.json", "w", encoding="utf-8") as f:
                json.dump(products[0], f, ensure_ascii=False)
            print("Saved first payload to snapp_intercepted.json")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
