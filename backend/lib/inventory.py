from datetime import datetime, timezone

from lib.catalog import CATALOG
from lib.db import db


async def ensure_inventory() -> None:
    for slug, product in CATALOG.items():
        await db.inventory.update_one(
            {"product_slug": slug},
            {"$setOnInsert": {
                "product_slug": slug,
                "name": product["name"],
                "variety": product["variety"],
                "tracking_enabled": False,
                "stock_50g": 0,
                "stock_100g": 0,
                "updated_at": datetime.now(timezone.utc),
            }},
            upsert=True,
        )


async def inventory_list() -> list[dict]:
    await ensure_inventory()
    documents = await db.inventory.find({}, {"_id": 0}).to_list(100)
    by_slug = {document["product_slug"]: document for document in documents}
    return [by_slug[slug] for slug in CATALOG if slug in by_slug]