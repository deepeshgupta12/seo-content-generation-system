from __future__ import annotations

from typing import Any

from seo_content_engine.domain.enums import EntityType, ListingType, PageType
from seo_content_engine.utils.formatters import compact_dict


class EntityNormalizer:
    @staticmethod
    def detect_entity_type(main_data: dict[str, Any], rates_data: dict[str, Any]) -> EntityType:
        rates_type = (
            rates_data.get("data", {})
            .get("type", "")
            .strip()
            .lower()
        )
        if rates_type == "city":
            return EntityType.CITY
        if rates_type == "micromarket":
            return EntityType.MICROMARKET
        if rates_type == "locality":
            return EntityType.LOCALITY

        overview = main_data.get("data", {}).get("localityOverviewData", {})
        if overview.get("isMicroMarket") == 1:
            return EntityType.MICROMARKET
        return EntityType.LOCALITY

    @staticmethod
    def resolve_page_type(entity_type: EntityType, listing_type: ListingType) -> PageType:
        if listing_type != ListingType.RESALE:
            raise ValueError(f"Unsupported listing type: {listing_type}")

        mapping = {
            EntityType.CITY: PageType.RESALE_CITY,
            EntityType.MICROMARKET: PageType.RESALE_MICROMARKET,
            EntityType.LOCALITY: PageType.RESALE_LOCALITY,
        }
        return mapping[entity_type]

    @staticmethod
    def normalize(main_data: dict[str, Any], rates_data: dict[str, Any], listing_type: ListingType) -> dict[str, Any]:
        overview = main_data.get("data", {}).get("localityOverviewData", {})
        locality_data = main_data.get("data", {}).get("localityData", {})
        rates_root = rates_data.get("data", {}).get("propertyRatesData", {})
        details = rates_root.get("details", {})
        market_overview = rates_root.get("marketOverview", {})
        sale = overview.get("sale", {})
        rent = overview.get("rent", {})
        metrics = overview.get("metrics", {})
        nearby_localities = main_data.get("data", {}).get("nearByLocalities", [])
        footer = main_data.get("data", {}).get("saleListingFooter", {})

        entity_type = EntityNormalizer.detect_entity_type(main_data, rates_data)
        page_type = EntityNormalizer.resolve_page_type(entity_type, listing_type)

        entity = compact_dict({
            "entity_type": entity_type.value,
            "page_type": page_type.value,
            "listing_type": listing_type.value,
            "entity_name": details.get("name") or overview.get("name") or locality_data.get("subLocalityName"),
            "city_name": details.get("cityName") or overview.get("cityName") or locality_data.get("cityName"),
            "micromarket_name": details.get("microMarketName") or overview.get("dotcomLocationName"),
            "entity_id": details.get("id") or locality_data.get("beatsLocalityId"),
            "city_id": details.get("cityId") or locality_data.get("beatsCityId"),
            "micromarket_id": details.get("microMarketId") or locality_data.get("microMarketId"),
            "beats_locality_id": locality_data.get("beatsLocalityId"),
            "dotcom_locality_id": locality_data.get("dotcomLocalityId"),
            "latitude": overview.get("latitude") or locality_data.get("sublocalityLatitude"),
            "longitude": overview.get("longitude") or locality_data.get("sublocalityLongitude"),
            "pincode": overview.get("pincode"),
            "overview_url": locality_data.get("overviewUrl") or main_data.get("data", {}).get("url"),
            "property_rates_url": details.get("diUrl"),
        })

        listing_summary = {
            "sale_count": overview.get("saleCount"),
            "rent_count": overview.get("rentCount"),
            "total_listings": overview.get("totallistings"),
            "total_projects": overview.get("totalprojects"),
            "sale_available": sale.get("available"),
            "rent_available": rent.get("available"),
            "sale_avg_price_per_sqft": sale.get("avgPricePerSqFt"),
            "rent_avg_price_per_sqft": rent.get("avgPricePerSqFt"),
            "sale_supply_count": metrics.get("sale", {}).get("supplyCount"),
            "sale_visit_count": metrics.get("sale", {}).get("visitCount"),
            "sale_enquired_count": metrics.get("sale", {}).get("enquiredCount"),
            "rent_supply_count": metrics.get("rent", {}).get("supplyCount"),
            "rent_visit_count": metrics.get("rent", {}).get("visitCount"),
            "rent_enquired_count": metrics.get("rent", {}).get("enquiredCount"),
        }

        pricing_summary = {
            "asking_price": market_overview.get("askingPrice"),
            "registration_rate": market_overview.get("registrationRate"),
            "avg_rental_rate": market_overview.get("avgRentalRate"),
            "price_trend": rates_root.get("priceTrend", []),
            "property_types": rates_root.get("propertyTypes", []),
            "property_status": rates_root.get("propertyStatus", []),
        }

        distributions = {
            "sale_unit_type_distribution": sale.get("unitType", []),
            "sale_property_type_distribution": sale.get("propertyType", []),
            "rent_unit_type_distribution": rent.get("unitType", []),
            "rent_property_type_distribution": rent.get("propertyType", []),
        }

        links = {
            "sale_unit_type_urls": footer.get("unitTypeUrls", []),
            "sale_property_type_urls": footer.get("propTypeUrls", []),
            "sale_quick_links": footer.get("quickLinks", []),
        }

        nearby = [
            compact_dict({
                "name": item.get("subLocalityName"),
                "city_name": item.get("cityName"),
                "distance_km": round(item.get("distance", 0), 3) if item.get("distance") is not None else None,
                "sale_count": item.get("sale", {}).get("count"),
                "sale_available": item.get("sale", {}).get("available"),
                "sale_avg_price_per_sqft": item.get("sale", {}).get("avgPricePerSqFt"),
                "rent_count": item.get("rent", {}).get("count"),
                "rent_available": item.get("rent", {}).get("available"),
                "rent_avg_price_per_sqft": item.get("rent", {}).get("avgPricePerSqFt"),
                "url": item.get("url"),
            })
            for item in nearby_localities[:10]
        ]

        return {
            "entity": entity,
            "listing_summary": listing_summary,
            "pricing_summary": pricing_summary,
            "distributions": distributions,
            "links": links,
            "nearby_localities": nearby,
            "top_projects": rates_root.get("topProjects", {}),
            "raw_source_meta": {
                "main_message": main_data.get("message"),
                "rates_message": rates_data.get("message"),
            },
        }