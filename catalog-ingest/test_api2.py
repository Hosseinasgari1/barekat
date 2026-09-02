"""Test http_client.py fetching from API."""
import asyncio
import json
from catalog_ingest.config import get_settings
from catalog_ingest.http_client import RateLimitedClient

async def main():
    settings = get_settings()
    async with RateLimitedClient(settings) as client:
        url = (
            "https://svc.snapp.market/express-search/products/by-category"
            "?category_id=731224&page=0&page_size=50&client=PWA"
            "&deviceType=PWA&appVersion=1.397.12&lat=35.773643&long=51.418311"
        )
        print(f"Fetching {url}...")
        try:
            data = await client.get_json(url)
            print("Success!")
            print(f"Keys: {list(data.keys())}")
            if "products" in data:
                print(f"Found {len(data['products'])} products")
                if data["products"]:
                    p = data["products"][0]
                    print(f"Sample: id={p.get('id')}, title={p.get('title')}, price={p.get('price')}")
            with open("api_test_results.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed: {e}")

asyncio.run(main())
