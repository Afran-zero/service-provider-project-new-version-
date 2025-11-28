"""Seed script to create sample businesses and services using the app models.

Usage (from `backend` folder with venv active):
    python scripts/seed_data.py

This script uses the app's `SingletonDB` to connect via `Config`, then
calls controller helpers to create Business and Service documents so
`business_id` and `service_id` fields are populated consistently.
"""
import sys
import os
from datetime import datetime

# Ensure backend package imports resolve when run from backend/
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from database.singleton_db import SingletonDB
from models.business import Business, Service


SAMPLE_BUSINESSES = [
    {
        "owner_id": None,
        "owner_name": "Owner One",
        "name": "Sparkle Home Cleaning",
        "email": "contact@sparkleclean.com",
        "phone": "+1-555-0101",
        "street_house": "12 Maple Ave",
        "city": "Springfield",
        "district": "Northside",
        "description": "Reliable home and office cleaning, regular & deep clean options.",
        "category": "cleaning",
    },
    {
        "owner_id": None,
        "owner_name": "Owner Two",
        "name": "FlowRight Plumbing Co.",
        "email": "hello@flowrightplumbing.com",
        "phone": "+1-555-0202",
        "street_house": "88 River Road",
        "city": "Springfield",
        "district": "Riverside",
        "description": "Emergency and scheduled plumbing repairs, leak detection, and installs.",
        "category": "plumbing",
    },
    {
        "owner_id": None,
        "owner_name": "Owner Three",
        "name": "BrightWatt Electricals",
        "email": "service@brightwatt.com",
        "phone": "+1-555-0303",
        "street_house": "200 Industrial Park",
        "city": "Springfield",
        "district": "West End",
        "description": "Licensed electricians for wiring, lighting, and safety inspections.",
        "category": "electric",
    },
    {
        "owner_id": None,
        "owner_name": "Owner Four",
        "name": "Canvas & Co. Painters",
        "email": "info@canvasco-paint.com",
        "phone": "+1-555-0404",
        "street_house": "45 Oak Street",
        "city": "Springfield",
        "district": "Downtown",
        "description": "Interior and exterior painting services, color consultation available.",
        "category": "painting",
    },
    {
        "owner_id": None,
        "owner_name": "Owner Five",
        "name": "GreenThumb Gardeners",
        "email": "grow@greenthumb.com",
        "phone": "+1-555-0505",
        "street_house": "31 Garden Lane",
        "city": "Springfield",
        "district": "Southside",
        "description": "Lawn care, landscaping and seasonal garden maintenance.",
        "category": "gardening",
    },
]

SAMPLE_SERVICES = {
    "cleaning": [
        {"name": "Standard Home Clean", "price": 49.99, "duration_minutes": 60},
    ],
    "plumbing": [
        {"name": "Leak Repair", "price": 79.0, "duration_minutes": 90},
    ],
    "electric": [
        {"name": "Wiring Inspection", "price": 120.0, "duration_minutes": 120},
    ],
    "painting": [
        {"name": "Interior Room Paint", "price": 199.0, "duration_minutes": 240},
    ],
    "gardening": [
        {"name": "Lawn Mowing", "price": 39.0, "duration_minutes": 45},
    ],
}


def main():
    print("Connecting to database...")
    # Ensure DB connection established via singleton
    SingletonDB()

    created = []

    for b in SAMPLE_BUSINESSES:
        print(f"Creating business: {b['name']}")
        biz = Business(
            owner_id=b.get('owner_id'),
            owner_name=b.get('owner_name'),
            name=b['name'],
            email=b['email'],
            phone=b['phone'],
            street_house=b['street_house'],
            city=b['city'],
            district=b['district'],
            description=b.get('description', ''),
            profile_pic_url=None,
            gallery_urls=[],
            category=b['category'],
            is_active=True,
        )
        biz.save()

        biz_info = {
            'business_id': getattr(biz, 'business_id', None),
            'name': biz.name,
            'category': biz.category,
        }
        created.append(biz_info)

        # create sample service(s) for this business using Service model directly
        services = SAMPLE_SERVICES.get(biz.category, [])
        for s in services:
            svc = Service(
                business_id=biz.business_id,
                name=s['name'],
                description=s.get('description', ''),
                price=s['price'],
                duration_minutes=s.get('duration_minutes', 60),
                is_active=True,
            )
            svc.save()
            print(f"  - Created service: {svc.name} (id={svc.service_id})")

    print('\nCreated businesses:')
    for c in created:
        print(f" - {c['name']} (business_id={c['business_id']}) category={c['category']}")

    print('\nSeed complete.')


if __name__ == '__main__':
    main()
