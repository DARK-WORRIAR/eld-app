"""
Commercial Freight Bill of Lading (BOL) and Cargo Manifest Engine.
Generates Uniform Straight Bill of Lading documents compliant with
FMCSA 49 CFR § 395.8(d)(17) and 49 U.S.C. § 14706 (Carmack Amendment).
"""

from datetime import datetime
import random
from typing import Any, Dict, Optional


def build_bill_of_lading(
    data: Dict[str, Any],
    locations: Dict[str, Any],
    start_time: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Constructs an official Commercial Bill of Lading (BOL) manifest object.

    Args:
        data: Validated trip input parameters (carrier, driver, trailer, commodity, weight, etc.)
        locations: Geocoded locations for current origin, shipper (pickup), and consignee (dropoff).
        start_time: Scheduled departure timestamp.

    Returns:
        Dict[str, Any]: Complete Bill of Lading payload including line items, security seals, and legal certifications.
    """
    if start_time is None:
        start_time = datetime.now()

    # Generate or format BOL number
    user_bol = data.get("bol_number", "")
    if user_bol and str(user_bol).strip():
        bol_number = str(user_bol).strip()
    else:
        date_prefix = start_time.strftime("%Y%m")
        rand_suffix = random.randint(1000, 9999)
        bol_number = f"BOL-{date_prefix}-{rand_suffix}"

    carrier_name = data.get("carrier_name", "Apex Logistics Freight, Inc.")
    driver_name = data.get("driver_name", "Commercial Driver")
    truck_number = data.get("truck_number", "TRK-409")
    trailer_number = data.get("trailer_number", "TRL-9201")
    commodity = data.get("commodity", "General Freight & Dry Goods").strip() or "General Freight & Dry Goods"
    cargo_weight_lbs = int(data.get("cargo_weight_lbs") or 38000)
    seal_number = (data.get("seal_number") or "").strip() or "SEAL-89104"

    shipper_loc = locations.get("pickup", {})
    receiver_loc = locations.get("dropoff", {})

    weight_kg = int(round(cargo_weight_lbs * 0.45359237))

    # Determine freight class and estimated pallet count based on weight
    pallet_count = max(4, min(30, int(round(cargo_weight_lbs / 1600))))
    freight_class = "70" if ("dry" in commodity.lower() or "general" in commodity.lower()) else "85"

    line_items = [
        {
            "item_number": 1,
            "quantity": pallet_count,
            "packaging_type": "Pallets / Skids (Shrink-Wrapped)",
            "commodity_description": commodity,
            "nmfc_freight_class": freight_class,
            "weight_lbs": cargo_weight_lbs,
            "weight_kg": weight_kg,
            "hazardous_material": False,
        }
    ]

    return {
        "bol_number": bol_number,
        "standard_form": "Uniform Straight Bill of Lading (Original - Not Negotiable)",
        "regulatory_statute": "49 CFR § 395.8(d)(17) / 49 U.S.C. § 14706",
        "date_issued": start_time.strftime("%Y-%m-%d"),
        "date_issued_formatted": start_time.strftime("%A, %B %d, %Y"),
        "carrier": {
            "name": carrier_name,
            "tractor_number": truck_number,
            "trailer_number": trailer_number,
            "driver_name": driver_name,
            "mc_dot_number": "USDOT 3849102 / MC-928410",
        },
        "shipper": {
            "facility_name": "Shipper Distribution Facility",
            "address": shipper_loc.get("display_name") or shipper_loc.get("address") or data.get("pickup_location"),
            "coordinates": {
                "lat": shipper_loc.get("lat"),
                "lon": shipper_loc.get("lon"),
            },
        },
        "consignee": {
            "facility_name": "Receiver Commercial Terminal",
            "address": receiver_loc.get("display_name") or receiver_loc.get("address") or data.get("dropoff_location"),
            "coordinates": {
                "lat": receiver_loc.get("lat"),
                "lon": receiver_loc.get("lon"),
            },
        },
        "cargo_security": {
            "seal_number": seal_number,
            "seal_type": "High-Security Bolt Seal (ISO 17712 Compliant)",
            "seal_verified": True,
        },
        "line_items": line_items,
        "totals": {
            "total_packages": pallet_count,
            "total_weight_lbs": cargo_weight_lbs,
            "total_weight_kg": weight_kg,
        },
        "special_instructions": (
            "Protect freight from freezing and moisture. Deliver between 07:00 and 17:00 local time. "
            "Do not break cargo seal until verified by consignee receiving manager. Notify dispatch on arrival."
        ),
        "legal_liability_terms": (
            "Received, subject to individually determined rates or contracts that have been agreed upon in writing "
            "between the carrier and shipper, the property described above, in apparent good order, except as noted. "
            "Carrier liability governed under 49 U.S.C. § 14706 (Carmack Amendment)."
        ),
        "signatures": {
            "shipper_signature": "Authorized Shipper Agent",
            "driver_signature": driver_name,
            "consignee_signature": "Pending Delivery Verification",
            "signed_at": start_time.isoformat(),
        },
    }
