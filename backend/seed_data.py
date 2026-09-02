import os
import django
import uuid
from datetime import datetime
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from inventory.models import MasterProduct

def seed():
    print("Seeding local database...")
    from django.db import connections
    with connections['catalog'].cursor() as cursor:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id char(32) PRIMARY KEY,
                title text,
                brand text,
                category text,
                barcode text,
                image_url text,
                unit text,
                description text,
                source varchar(64),
                source_product_id text,
                source_url text,
                created_at datetime,
                updated_at datetime
            )
        ''')

    if MasterProduct.objects.exists():
        print("Database already seeded. Skipping.")
        return

    products = [
        {"title": "شیر کم چرب میهن 1 لیتر", "category": "لبنیات", "source": "snappmarket", "image_url": "https://picsum.photos/200/200?random=1"},
        {"title": "شیر پرچرب کاله 1 لیتر", "category": "لبنیات", "source": "snappmarket", "image_url": "https://picsum.photos/200/200?random=2"},
        {"title": "ماست سون کاله 900 گرمی", "category": "لبنیات", "source": "snappmarket", "image_url": "https://picsum.photos/200/200?random=3"},
        {"title": "پنیر فتا هراز 400 گرمی", "category": "لبنیات", "source": "snappmarket", "image_url": "https://picsum.photos/200/200?random=4"},
        {"title": "پفک نمکی مینو", "category": "تنقلات", "source": "snappmarket", "image_url": "https://picsum.photos/200/200?random=5"},
        {"title": "چیپس مزمز سرکه نمکی", "category": "تنقلات", "source": "snappmarket", "image_url": "https://picsum.photos/200/200?random=6"},
        {"title": "بیسکویت ساقه طلایی مینو", "category": "تنقلات", "source": "snappmarket", "image_url": "https://picsum.photos/200/200?random=7"},
        {"title": "نوشابه کوکاکولا 1.5 لیتری", "category": "نوشیدنی", "source": "snappmarket", "image_url": "https://picsum.photos/200/200?random=8"},
        {"title": "دوغ آبعلی", "category": "نوشیدنی", "source": "snappmarket", "image_url": "https://picsum.photos/200/200?random=9"},
        {"title": "آب معدنی دماوند", "category": "نوشیدنی", "source": "snappmarket", "image_url": "https://picsum.photos/200/200?random=10"},
        {"title": "نان تست اورنج", "category": "نان", "source": "snappmarket", "image_url": "https://picsum.photos/200/200?random=11"},
        {"title": "نان همبرگر نان آوران", "category": "نان", "source": "snappmarket", "image_url": "https://picsum.photos/200/200?random=12"},
        {"title": "برنج هاشمی گلستان 5 کیلوگرمی", "category": "خواربار", "source": "snappmarket", "image_url": "https://picsum.photos/200/200?random=13"},
        {"title": "روغن آفتابگردان لادن 1.5 لیتری", "category": "خواربار", "source": "snappmarket", "image_url": "https://picsum.photos/200/200?random=14"},
        {"title": "ماکارونی مانا 700 گرمی", "category": "خواربار", "source": "snappmarket", "image_url": "https://picsum.photos/200/200?random=15"},
    ]

    for p in products:
        MasterProduct.objects.create(
            id=uuid.uuid4(),
            title=p['title'],
            category=p['category'],
            source=p['source'],
            image_url=p['image_url'],
            created_at=timezone.now(),
            updated_at=timezone.now()
        )
    print(f"Inserted {len(products)} mock products.")

if __name__ == '__main__':
    seed()
