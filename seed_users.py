"""
Seed script to create realistic Django users and addresses.
Use this before seeding orders so recommendation and admin analytics
have multiple customers to work with.
"""

import os
import sys
from pathlib import Path

import django

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ZaikaX.settings")
django.setup()

from django.contrib.auth.models import User

from accounts.models import Address


USER_SEED_DATA = [
    {
        "username": "rahul_foodie",
        "email": "rahul.foodie@example.com",
        "first_name": "Rahul",
        "last_name": "Sharma",
        "password": "testpass123",
        "addresses": [
            {
                "full_name": "Rahul Sharma",
                "email": "rahul.foodie@example.com",
                "phone": "9876501001",
                "address_line1": "22 Green Park Road",
                "address_line2": "Near City Mall",
                "city": "Delhi",
                "state": "Delhi",
                "pincode": "110016",
                "country": "India",
                "is_default": True,
            }
        ],
    },
    {
        "username": "neha_cravings",
        "email": "neha.cravings@example.com",
        "first_name": "Neha",
        "last_name": "Verma",
        "password": "testpass123",
        "addresses": [
            {
                "full_name": "Neha Verma",
                "email": "neha.cravings@example.com",
                "phone": "9876501002",
                "address_line1": "18 Lake View Apartments",
                "address_line2": "Flat 402",
                "city": "Mumbai",
                "state": "Maharashtra",
                "pincode": "400050",
                "country": "India",
                "is_default": True,
            }
        ],
    },
    {
        "username": "arjun_spice",
        "email": "arjun.spice@example.com",
        "first_name": "Arjun",
        "last_name": "Patel",
        "password": "testpass123",
        "addresses": [
            {
                "full_name": "Arjun Patel",
                "email": "arjun.spice@example.com",
                "phone": "9876501003",
                "address_line1": "9 Riverfront Residency",
                "address_line2": "",
                "city": "Ahmedabad",
                "state": "Gujarat",
                "pincode": "380009",
                "country": "India",
                "is_default": True,
            }
        ],
    },
    {
        "username": "simran_bites",
        "email": "simran.bites@example.com",
        "first_name": "Simran",
        "last_name": "Kaur",
        "password": "testpass123",
        "addresses": [
            {
                "full_name": "Simran Kaur",
                "email": "simran.bites@example.com",
                "phone": "9876501004",
                "address_line1": "44 Rose Enclave",
                "address_line2": "Block B",
                "city": "Chandigarh",
                "state": "Chandigarh",
                "pincode": "160022",
                "country": "India",
                "is_default": True,
            }
        ],
    },
    {
        "username": "kiran_combo",
        "email": "kiran.combo@example.com",
        "first_name": "Kiran",
        "last_name": "Nair",
        "password": "testpass123",
        "addresses": [
            {
                "full_name": "Kiran Nair",
                "email": "kiran.combo@example.com",
                "phone": "9876501005",
                "address_line1": "77 Palm Residency",
                "address_line2": "Near Metro Station",
                "city": "Bengaluru",
                "state": "Karnataka",
                "pincode": "560038",
                "country": "India",
                "is_default": True,
            }
        ],
    },
    {
        "username": "aisha_flavors",
        "email": "aisha.flavors@example.com",
        "first_name": "Aisha",
        "last_name": "Khan",
        "password": "testpass123",
        "addresses": [
            {
                "full_name": "Aisha Khan",
                "email": "aisha.flavors@example.com",
                "phone": "9876501006",
                "address_line1": "12 Heritage Colony",
                "address_line2": "",
                "city": "Lucknow",
                "state": "Uttar Pradesh",
                "pincode": "226010",
                "country": "India",
                "is_default": True,
            }
        ],
    },
]


def seed_users():
    created_users = 0
    updated_users = 0
    created_addresses = 0

    for user_data in USER_SEED_DATA:
        defaults = {
            "email": user_data["email"],
            "first_name": user_data["first_name"],
            "last_name": user_data["last_name"],
        }
        user, created = User.objects.get_or_create(username=user_data["username"], defaults=defaults)

        if created:
            user.set_password(user_data["password"])
            user.save()
            created_users += 1
        else:
            changed = False
            for field in ["email", "first_name", "last_name"]:
                if getattr(user, field) != user_data[field]:
                    setattr(user, field, user_data[field])
                    changed = True
            if changed:
                user.save(update_fields=["email", "first_name", "last_name"])
                updated_users += 1

        for address_data in user_data["addresses"]:
            address_defaults = address_data.copy()
            is_default = address_defaults.pop("is_default", False)

            address, addr_created = Address.objects.get_or_create(
                user=user,
                address_line1=address_data["address_line1"],
                city=address_data["city"],
                pincode=address_data["pincode"],
                defaults={**address_defaults, "is_default": is_default},
            )

            if addr_created:
                created_addresses += 1
            else:
                for key, value in address_defaults.items():
                    setattr(address, key, value)
                address.is_default = is_default
                address.save()

        default_address = user.addresses.filter(is_default=True).first()
        if not default_address:
            first_address = user.addresses.first()
            if first_address:
                first_address.is_default = True
                first_address.save(update_fields=["is_default"])

    print("User seeding complete.")
    print(f"Created users: {created_users}")
    print(f"Updated users: {updated_users}")
    print(f"Created addresses: {created_addresses}")
    print(f"Total users available: {User.objects.count()}")
    print("Login password for seeded users: testpass123")


if __name__ == "__main__":
    seed_users()
