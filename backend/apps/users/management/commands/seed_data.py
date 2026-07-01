import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from stores.models import UserAddress, Store
from inventory.models import MagicBag
from datetime import time
from decimal import Decimal

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds the database with mock data for testing.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Clearing existing data (except superusers)..."))
        
        # Clear existing models (keep superusers)
        MagicBag.objects.all().delete()
        Store.objects.all().delete()
        UserAddress.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

        self.stdout.write(self.style.SUCCESS("Existing data cleared."))

        # 1. Create Users
        self.stdout.write("Creating mock users...")
        
        # Customer Ali
        ali = User.objects.create_user(
            phone_number='09121111111',
            first_name='علی',
            last_name='علوی',
            role=User.Roles.CUSTOMER
        )
        ali.set_password('12345')
        ali.save()

        # Seller Maryam (Store owner)
        maryam = User.objects.create_user(
            phone_number='09122222222',
            first_name='مریم',
            last_name='محمدی',
            role=User.Roles.VENDOR
        )
        maryam.set_password('12345')
        maryam.save()

        # Individual Seller Reza
        reza = User.objects.create_user(
            phone_number='09123333333',
            first_name='رضا',
            last_name='رضایی',
            role=User.Roles.VENDOR
        )
        reza.set_password('12345')
        reza.save()

        self.stdout.write(self.style.SUCCESS("Users created (Password for all: '12345')"))

        # 2. Create Addresses (around Vanak, Tehran: 35.7575, 51.4100)
        self.stdout.write("Creating mock addresses...")
        
        # Ali's active address at Vanak
        addr_ali = UserAddress.objects.create(
            user=ali,
            name='میدان ونک (خانه)',
            latitude=Decimal('35.757500'),
            longitude=Decimal('51.410000'),
            is_active=True
        )

        # Maryam's address near Ghandi
        addr_maryam = UserAddress.objects.create(
            user=maryam,
            name='خیابان گاندی (فروشگاه)',
            latitude=Decimal('35.760000'),
            longitude=Decimal('51.415000'),
            is_active=True
        )

        # Reza's address near Mirdamad
        addr_reza = UserAddress.objects.create(
            user=reza,
            name='بلوار میرداماد (خانه)',
            latitude=Decimal('35.765000'),
            longitude=Decimal('51.405000'),
            is_active=True
        )

        self.stdout.write(self.style.SUCCESS("Addresses created."))

        # 3. Create Stores
        self.stdout.write("Creating mock stores...")

        store_bakery = Store.objects.create(
            owner=maryam,
            name='نانوایی سنگک سنتی برکت',
            description='عرضه انواع نان سنگک داغ و کنجدی با آرد سبوس‌دار با کیفیت بالا',
            address='تهران، خیابان گاندی جنوبی، پلاک ۴۲',
            latitude=Decimal('35.760000'),
            longitude=Decimal('51.415000'),
            status=Store.StoreStatus.APPROVED
        )

        # Let's create an additional store for variety (we can create it for a new user or a placeholder)
        # Create a user for another store
        bahar_user = User.objects.create_user(
            phone_number='09124444444',
            first_name='زهرا',
            last_name='بهاری',
            role=User.Roles.VENDOR
        )
        bahar_user.set_password('12345')
        bahar_user.save()

        store_veggies = Store.objects.create(
            owner=bahar_user,
            name='میوه‌فروشی بهار ونک',
            description='انواع میوه و سبزیجات تازه روز با تخفیف‌های ویژه برای کاهش پسماند غرفه‌ها',
            address='تهران، ضلع شمال غربی میدان ونک، پاساژ ونک',
            latitude=Decimal('35.758000'),
            longitude=Decimal('51.405000'),
            status=Store.StoreStatus.APPROVED
        )

        # Sweet Shop User
        sweet_user = User.objects.create_user(
            phone_number='09125555555',
            first_name='امیر',
            last_name='قنادی',
            role=User.Roles.VENDOR
        )
        sweet_user.set_password('12345')
        sweet_user.save()

        store_sweets = Store.objects.create(
            owner=sweet_user,
            name='شیرینی‌سرای لادن ونک',
            description='انواع شیرینی‌های تر، دسرها و کیک‌های روز با کیفیت فوق‌العاده',
            address='تهران، خیابان ولیعصر، نرسیده به ونک',
            latitude=Decimal('35.753000'),
            longitude=Decimal('51.412000'),
            status=Store.StoreStatus.APPROVED
        )

        self.stdout.write(self.style.SUCCESS("Stores created and approved."))

        # 4. Create Magic Bags (Products)
        self.stdout.write("Creating mock products/magic bags...")

        # Bakery Bags
        MagicBag.objects.create(
            store=store_bakery,
            name='کیسه نان سنگک کنجدی داغ',
            description='شامل ۳ عدد نان سنگک کنجدی تازه پخت روز مابقی شیفت',
            category=MagicBag.CategoryChoices.BAKERY,
            original_price=Decimal('150000'),
            platform_price=Decimal('50000'),
            quantity=5,
            pickup_start_time=time(18, 0),
            pickup_end_time=time(21, 0),
            is_active=True
        )

        # Veggies Bags
        MagicBag.objects.create(
            store=store_veggies,
            name='کیسه میوه مخلوط ممتاز',
            description='شامل سیب، پرتقال و موز درجه یک بدون خرابی، مناسب مصرف روزانه',
            category=MagicBag.CategoryChoices.VEGETABLES,
            original_price=Decimal('300000'),
            platform_price=Decimal('90000'),
            quantity=3,
            pickup_start_time=time(17, 0),
            pickup_end_time=time(20, 0),
            is_active=True
        )

        # Sweets Bags
        MagicBag.objects.create(
            store=store_sweets,
            name='جعبه شیرینی تر خامه ای مخلوط',
            description='جعبه ۱ کیلوگرمی شیرینی تر خامه‌ای مخلوط تازه پخت امروز',
            category=MagicBag.CategoryChoices.SWEETS,
            original_price=Decimal('400000'),
            platform_price=Decimal('120000'),
            quantity=4,
            pickup_start_time=time(19, 0),
            pickup_end_time=time(22, 0),
            is_active=True
        )

        # Supermarket Bags (Individual Seller or Store - let's create a store for it)
        super_user = User.objects.create_user(
            phone_number='09126666666',
            first_name='کریم',
            last_name='سوپرمارکتی',
            role=User.Roles.VENDOR
        )
        super_user.set_password('12345')
        super_user.save()

        store_super = Store.objects.create(
            owner=super_user,
            name='هایپرمارکت رضا',
            description='سوپرمارکت محلی ونک با انواع لبنیات، خواربار و ملزومات روزانه',
            address='تهران، ملاصدرا، پلاک ۱۲',
            latitude=Decimal('35.756000'),
            longitude=Decimal('51.398000'),
            status=Store.StoreStatus.APPROVED
        )

        MagicBag.objects.create(
            store=store_super,
            name='بسته لبنیات و پروتئین روز',
            description='شامل شیر، ماست سنتی و پنیر خامه ای با تاریخ انقضای محدود (۲ روز)',
            category=MagicBag.CategoryChoices.SUPERMARKET,
            original_price=Decimal('250000'),
            platform_price=Decimal('80000'),
            quantity=6,
            pickup_start_time=time(16, 0),
            pickup_end_time=time(20, 0),
            is_active=True
        )

        # Individual Seller Reza's product (no store)
        MagicBag.objects.create(
            seller=reza,
            name='کیسه سبزی خورشتی سرخ‌شده خانگی',
            description='سبزی خورشتی قورمه‌سبزی تمیز، سرخ شده کاملاً خانگی و بهداشتی',
            category=MagicBag.CategoryChoices.INGREDIENTS,
            latitude=Decimal('35.765000'),
            longitude=Decimal('51.405000'),
            original_price=Decimal('180000'),
            platform_price=Decimal('60000'),
            quantity=5,
            pickup_start_time=time(15, 0),
            pickup_end_time=time(19, 0),
            is_active=True
        )

        # Individual Seller 2 - Sweet Bag
        cookie_seller = User.objects.create_user(
            phone_number='09127777777',
            first_name='سارا',
            last_name='کلوچه‌پز',
            role=User.Roles.VENDOR
        )
        cookie_seller.set_password('12345')
        cookie_seller.save()

        MagicBag.objects.create(
            seller=cookie_seller,
            name='بسته کوکی شکلاتی خانگی تازه',
            description='۱۰ عدد کوکی شکلاتی داغ خانگی پخته شده در عصر امروز',
            category=MagicBag.CategoryChoices.SWEETS,
            latitude=Decimal('35.759000'),
            longitude=Decimal('51.412000'),
            original_price=Decimal('150000'),
            platform_price=Decimal('50000'),
            quantity=4,
            pickup_start_time=time(18, 0),
            pickup_end_time=time(21, 0),
            is_active=True
        )

        self.stdout.write(self.style.SUCCESS("Products/Magic bags seeded successfully."))
        self.stdout.write(self.style.SUCCESS("Database Seeding Completed successfully!"))
