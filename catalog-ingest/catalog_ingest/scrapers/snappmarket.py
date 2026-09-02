"""SnappMarket adapter — Playwright-based API scraper.

SnappMarket uses a Next.js frontend with ArvanCloud WAF and hyperlocal delivery.
This scraper uses Playwright to:
1. Launch a real browser and visit snapp.market (bypasses WAF)
2. Simulate a location selection (required to see products)
3. Extract the UDID and session cookies
4. Directly call the internal product API (express-search/v1/pb/products)
   using the Playwright browser context to inherit cookies/bypasses.

Fixes applied (2026-07):
- Image URL parsing now correctly reads 'main'/'thumb' keys (not the absent 'url' key)
- UDID is extracted from SNAPP_COOKIE env var if present, skipping the fragile modal flow
- Browser modal flow made robust with proper selector waits and multiple confirm strategies
- Page numbering corrected to 1-based (API uses 1-indexed pages)
- Improved logging to surface failures early
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, AsyncIterator
import urllib.parse

from catalog_ingest.config import Settings, get_settings
from catalog_ingest.http_client import RateLimitedClient
from catalog_ingest.scrapers.base import BaseScraper, RawProduct

logger = logging.getLogger(__name__)

# Fixed coordinates: Tehran central area
_LAT = "35.773643"
_LONG = "51.418311"
_APP_VERSION = "1.397.12"


def _first(*values: Any) -> Any:
    for v in values:
        if v is None:
            continue
        if isinstance(v, str) and not v.strip():
            continue
        return v
    return None


def _extract_udid_from_cookie(cookie_str: str) -> str:
    """Extract UDID value from a cookie string like 'UDID=xxxx; other=val'."""
    match = re.search(r"(?:^|;\s*)UDID=([^;]+)", cookie_str)
    if match:
        return match.group(1).strip()
    return ""


def parse_product(item: dict[str, Any], *, category_hint: str | None = None) -> RawProduct | None:
    title = _first(item.get("title"), item.get("name"))
    if not title:
        return None

    product_id = _first(item.get("id"), item.get("productId"))
    brand = item.get("brand") or None
    barcode = item.get("barcode") or None
    description = item.get("description") or None

    # FIX: SnappMarket images have 'main'/'thumb' keys, not 'url'
    images = item.get("images")
    image_url = None
    if isinstance(images, list) and images:
        first_img = images[0]
        if isinstance(first_img, str):
            image_url = first_img
        elif isinstance(first_img, dict):
            image_url = _first(
                first_img.get("main"),
                first_img.get("thumb"),
                first_img.get("url"),  # fallback in case API changes
            )

    if image_url and not image_url.startswith("http"):
        image_url = "https://static.snapp.express" + image_url

    source_url = None
    if product_id:
        slug = (title or "product").replace(" ", "-")
        source_url = f"https://snapp.market/product/{urllib.parse.quote(slug)}/{product_id}"

    return RawProduct(
        title=str(title),
        source="snappmarket",
        source_product_id=str(product_id) if product_id is not None else None,
        brand=str(brand) if brand is not None else None,
        category=category_hint,
        barcode=str(barcode).strip() if barcode is not None else None,
        image_url=str(image_url) if image_url else None,
        unit=None,
        description=str(description) if description is not None else None,
        source_url=str(source_url) if source_url is not None else None,
        extras={"price": item.get("price"), "discount": item.get("discount")},
    )


class SnappMarketScraper(BaseScraper):
    source_name = "snappmarket"

    def __init__(
        self,
        client: RateLimitedClient,
        settings: Settings | None = None,
    ) -> None:
        self.client = client
        self.settings = settings or get_settings()
        self._browser = None
        self._context = None
        self._page = None
        self._pw = None
        self._udid = ""

    async def _init_browser(self) -> None:
        if self._page is not None:
            return
        from playwright.async_api import async_playwright

        # FIX: Try to extract UDID from the cookie string in settings first.
        # This avoids the fragile browser modal flow when a valid cookie exists.
        if self.settings.snapp_cookie:
            extracted = _extract_udid_from_cookie(self.settings.snapp_cookie)
            if extracted:
                self._udid = extracted
                logger.info("Using UDID from SNAPP_COOKIE env var: %s", self._udid)

        self._pw = await async_playwright().start()
        self._browser = await self._pw.chromium.launch(headless=False)
        self._context = await self._browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="fa-IR",
            geolocation={"longitude": float(_LONG), "latitude": float(_LAT)},
            permissions=["geolocation"],
        )
        self._page = await self._context.new_page()

        # Inject saved cookie string into the browser context if available
        if self.settings.snapp_cookie:
            await self._inject_cookies(self.settings.snapp_cookie)

        # Always visit the homepage first to establish WAF session cookies
        logger.info("Visiting snapp.market homepage to warm up session...")
        try:
            await self._page.goto("https://snapp.market", wait_until="domcontentloaded", timeout=30000)
            await self._page.wait_for_timeout(3000)
        except Exception as exc:
            logger.warning("Homepage navigation failed: %s", exc)

        # If UDID was already set from cookie, skip the modal flow
        if self._udid:
            logger.info("Session ready (UDID from env). Skipping address modal.")
            return

        # No UDID yet — attempt the address modal flow
        logger.info("No UDID in env. Attempting address modal flow...")
        await self._setup_location_via_modal()

        # Final UDID check
        if not self._udid:
            logger.warning(
                "UDID still empty after modal flow. "
                "Products API may return empty results. "
                "Set SNAPP_COOKIE in .env with a valid session cookie."
            )

    async def _inject_cookies(self, cookie_str: str) -> None:
        """Parse a raw cookie string and inject each cookie into the browser context."""
        assert self._context is not None
        cookies = []
        for part in cookie_str.split(";"):
            part = part.strip()
            if "=" not in part:
                continue
            name, _, value = part.partition("=")
            name = name.strip()
            value = value.strip()
            if name:
                cookies.append({
                    "name": name,
                    "value": value,
                    "domain": ".snapp.market",
                    "path": "/",
                })
        if cookies:
            try:
                await self._context.add_cookies(cookies)
                logger.debug("Injected %d cookies into browser context", len(cookies))
            except Exception as exc:
                logger.warning("Cookie injection failed: %s", exc)

    async def _setup_location_via_modal(self) -> None:
        """Navigate to the address modal and attempt to confirm a location."""
        assert self._page is not None
        assert self._context is not None

        try:
            await self._page.goto(
                "https://snapp.market/modals/address/add",
                wait_until="domcontentloaded",
                timeout=30000,
            )
            await self._page.wait_for_timeout(4000)

            # Strategy 1: Look for a confirm/submit button by common patterns
            confirmed = False
            confirm_selectors = [
                "button:has-text('تایید')",
                "button:has-text('ثبت')",
                "button:has-text('انتخاب')",
                "button:has-text('تأیید')",
                "[data-testid*='confirm']",
                "[class*='confirm']",
                "[class*='submit']",
            ]
            for sel in confirm_selectors:
                try:
                    btn = await self._page.wait_for_selector(sel, timeout=2000)
                    if btn:
                        await btn.click()
                        await self._page.wait_for_timeout(2000)
                        confirmed = True
                        logger.info("Clicked confirm button via selector: %s", sel)
                        break
                except Exception:
                    continue

            if not confirmed:
                # Strategy 2: Click bottom-center of the viewport (map confirm area)
                logger.info("No confirm button found, clicking map confirm coordinates...")
                await self._page.mouse.click(640, 800)
                await self._page.wait_for_timeout(2000)

        except Exception as exc:
            logger.warning("Address modal flow failed: %s", exc)

        # Refresh UDID from cookies after modal
        try:
            cookies = await self._context.cookies()
            self._udid = next((c["value"] for c in cookies if c["name"] == "UDID"), self._udid)
            if self._udid:
                logger.info("Session established with UDID: %s", self._udid)
        except Exception as exc:
            logger.warning("Failed to read cookies after modal: %s", exc)

    async def _close_browser(self) -> None:
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._pw:
            await self._pw.stop()
            self._pw = None

    async def _fetch_categories(self) -> list[dict[str, Any]]:
        assert self._context is not None
        url = (
            "https://svc.snapp.market/express-search/categories"
            f"?client=PWA&deviceType=PWA&appVersion={_APP_VERSION}"
            f"&UDID={self._udid}&lat={_LAT}&long={_LONG}"
        )
        logger.debug("Fetching categories: %s", url)
        try:
            resp = await self._context.request.get(url)
        except Exception as exc:
            logger.error("Categories request exception: %s", exc)
            return []

        if resp.status != 200:
            logger.warning(
                "Categories API failed: HTTP %s — check UDID/cookie validity", resp.status
            )
            return []

        try:
            data = await resp.json()
        except Exception as exc:
            logger.warning("Categories JSON decode failed: %s", exc)
            return []

        if not isinstance(data, dict):
            logger.warning("Categories response is not a dict: %r", type(data))
            return []

        result = []
        for cat in data.get("categories", []):
            if not isinstance(cat, dict):
                continue
            cat_slug = cat.get("slug")
            cat_title = cat.get("title", "")
            if not cat_slug:
                continue

            subs = cat.get("sub_categories") or cat.get("children") or []
            if subs:
                for sub in subs:
                    if isinstance(sub, dict) and sub.get("slug"):
                        result.append({
                            "category_slug": cat_slug,
                            "sub_category_slug": sub["slug"],
                            "title": f"{cat_title} > {sub.get('title', '')}",
                        })
            else:
                result.append({
                    "category_slug": cat_slug,
                    "sub_category_slug": "",
                    "title": cat_title,
                })

        logger.info("Found %d category/subcategory combinations", len(result))
        return result

    async def _fetch_products_page(
        self, cat_slug: str, sub_slug: str, page: int, size: int = 50
    ) -> list[dict[str, Any]]:
        assert self._context is not None
        url = (
            "https://svc.snapp.market/express-search/v1/pb/products"
            f"?category_slug={cat_slug}&sub_category_slug={sub_slug}"
            # FIX: API uses 1-based page numbers
            f"&page={page}&size={size}&client=PWA&deviceType=PWA"
            f"&appVersion={_APP_VERSION}&UDID={self._udid}&lat={_LAT}&long={_LONG}"
        )
        try:
            resp = await self._context.request.get(url)
        except Exception as exc:
            logger.debug("Products request exception for %s/%s p%d: %s", cat_slug, sub_slug, page, exc)
            return []

        if resp.status != 200:
            logger.debug(
                "Products API failed: HTTP %s for category_slug=%s sub=%s page=%d",
                resp.status, cat_slug, sub_slug, page,
            )
            return []

        try:
            data = await resp.json()
            if isinstance(data, dict):
                items = data.get("items", [])
                if items:
                    logger.debug(
                        "Fetched %d items from %s/%s page %d", len(items), cat_slug, sub_slug, page
                    )
                return items if isinstance(items, list) else []
        except Exception as exc:
            logger.debug("Failed to decode product JSON: %s", exc)
        return []

    async def iter_products(
        self,
        *,
        category_ids: list[str] | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[RawProduct]:
        try:
            await self._init_browser()

            categories = await self._fetch_categories()
            if not categories:
                logger.error(
                    "No categories found — the scrape produced nothing. "
                    "Verify that SNAPP_COOKIE in .env is valid and UDID is present."
                )
                return

            produced = 0
            for cat in categories:
                if limit is not None and produced >= limit:
                    break

                cat_slug = cat["category_slug"]
                sub_slug = cat["sub_category_slug"]
                title = cat["title"]

                logger.info("Scraping category: %s (slug=%s/%s)", title, cat_slug, sub_slug)

                # FIX: Start at page 1 (API is 1-indexed)
                page = 1
                page_size = 50  # must match the size passed to _fetch_products_page

                while True:
                    if limit is not None and produced >= limit:
                        break

                    items = await self._fetch_products_page(cat_slug, sub_slug, page, size=page_size)
                    if not items:
                        logger.debug("No items on page %d for %s — moving to next category", page, title)
                        break

                    for item in items:
                        if limit is not None and produced >= limit:
                            break

                        raw = parse_product(item, category_hint=title)
                        if raw:
                            produced += 1
                            yield raw

                    if len(items) < page_size:
                        break

                    page += 1
                    await asyncio.sleep(1)

                await asyncio.sleep(1)

        finally:
            await self._close_browser()
