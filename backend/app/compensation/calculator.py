"""Statutory Award & Solatium Calculator per RFCTLARR Act (2013).

Implements the mandatory computation formulas from:
- Section 26: Determination of Market Value by Collector
- Section 26(2) & First Schedule: Multiplier factor for rural areas (1.0 to 2.0)
- Section 29: Determination of value of things attached to land (structures, trees, crops)
- Section 30(1): Solatium of 100% over and above the market value
- Section 30(3): Additional 12% per annum interest from Preliminary Notification to Award
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Dict, Optional


def calculate_multiplier_factor(is_rural: bool, distance_from_urban_boundary_km: float = 0.0) -> float:
    """Computes multiplier factor per First Schedule of RFCTLARR Act 2013."""
    if not is_rural:
        return 1.0
    if distance_from_urban_boundary_km <= 10.0:
        return 1.25
    elif distance_from_urban_boundary_km <= 20.0:
        return 1.50
    elif distance_from_urban_boundary_km <= 30.0:
        return 1.75
    else:
        return 2.00


def calculate_statutory_award(
    base_market_value_per_hectare: float,
    area_hectares: float,
    is_rural: bool = True,
    distance_from_urban_boundary_km: float = 15.0,
    structure_valuation: float = 0.0,
    trees_and_crops_valuation: float = 0.0,
    notification_date_iso: Optional[str] = None,
    award_date_iso: Optional[str] = None,
) -> Dict[str, Any]:
    """Computes transparent statutory award breakdown with complete legal schedule references."""
    # Step 1: Base Land Value
    base_land_value = round(base_market_value_per_hectare * area_hectares, 2)

    # Step 2: Multiplier Factor (Section 26(2) & First Schedule)
    multiplier_factor = calculate_multiplier_factor(is_rural, distance_from_urban_boundary_km)
    market_value_after_multiplier = round(base_land_value * multiplier_factor, 2)

    # Step 3: Assets Attached to Land (Section 29)
    assets_total = round(structure_valuation + trees_and_crops_valuation, 2)
    total_land_and_assets = round(market_value_after_multiplier + assets_total, 2)

    # Step 4: Solatium 100% (Section 30(1))
    # Solatium is 100% of the total assessed market value
    solatium_amount = round(total_land_and_assets * 1.00, 2)

    # Step 5: Additional 12% p.a. Interest (Section 30(3))
    interest_days = 365  # Default ~1 year if dates not supplied
    if notification_date_iso and award_date_iso:
        try:
            d_notif = datetime.fromisoformat(notification_date_iso).date()
            d_award = datetime.fromisoformat(award_date_iso).date()
            interest_days = max(1, (d_award - d_notif).days)
        except Exception:
            interest_days = 365

    annual_rate = 0.12  # 12% statutory per annum
    interest_years = interest_days / 365.25
    additional_interest = round(market_value_after_multiplier * annual_rate * interest_years, 2)

    # Total Gross Statutory Award
    total_award_amount = round(total_land_and_assets + solatium_amount + additional_interest, 2)

    return {
        "statutory_compliance": "RFCTLARR Act (2013) First Schedule",
        "inputs": {
            "area_hectares": area_hectares,
            "base_market_value_per_hectare": base_market_value_per_hectare,
            "is_rural": is_rural,
            "distance_from_urban_km": distance_from_urban_boundary_km,
            "structure_valuation": structure_valuation,
            "trees_and_crops_valuation": trees_and_crops_valuation,
            "interest_elapsed_days": interest_days,
        },
        "breakdown": {
            "step_1_base_land_value": base_land_value,
            "step_2_multiplier_factor": multiplier_factor,
            "step_2_market_value_factored": market_value_after_multiplier,
            "step_3_attached_assets": {
                "structures_value": structure_valuation,
                "trees_and_crops_value": trees_and_crops_valuation,
                "total_assets": assets_total,
            },
            "step_3_total_assessed_value": total_land_and_assets,
            "step_4_mandatory_solatium_100pct": solatium_amount,
            "step_5_additional_interest_12pct": additional_interest,
            "total_gross_award": total_award_amount,
        },
        "legal_citations": [
            "Section 26(1): Market value determined on higher of circle rate or registered sales deed average.",
            f"Section 26(2) First Schedule: Multiplier factor {multiplier_factor}× applied based on rural distance.",
            "Section 29: Valuation of immovable property, building structures, and standing horticultural assets.",
            "Section 30(1): Mandatory 100% Solatium awarded over assessed land & asset value.",
            f"Section 30(3): 12% per annum additional interest calculated over {interest_days} days.",
        ],
    }
