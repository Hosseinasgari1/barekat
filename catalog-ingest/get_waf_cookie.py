import asyncio
import os
from playwright.async_api import async_playwright
from catalog_ingest.config import ROOT_DIR

async def get_cookie():
    print("Launching visible browser to bypass WAF...")
    async with async_playwright() as p:
        # Launch visible browser
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        print("Navigating to snapp.market...")
        await page.goto('https://snapp.market')
        
        # Wait 10 seconds for the WAF challenge to pass
        print("Waiting 10 seconds for Cloudflare/ArvanCloud to verify browser...")
        await page.wait_for_timeout(10000)
        
        # Now try to hit the API or just grab cookies
        cookies = await context.cookies()
        cookie_string = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
        
        if cookie_string:
            print("Successfully grabbed session cookies!")
            
            # Read existing .env
            env_path = ROOT_DIR / ".env"
            if env_path.exists():
                lines = env_path.read_text().splitlines()
            else:
                lines = []
            
            # Update or append SNAPP_COOKIE
            updated = False
            for i, line in enumerate(lines):
                if line.startswith("SNAPP_COOKIE="):
                    lines[i] = f"SNAPP_COOKIE={cookie_string}"
                    updated = True
                    break
            
            if not updated:
                lines.append(f"SNAPP_COOKIE={cookie_string}")
                
            env_path.write_text("\n".join(lines))
            print(".env updated with new cookie. You can now run the scraper.")
        else:
            print("Failed to get cookies.")
            
        await browser.close()

asyncio.run(get_cookie())
