from __future__ import annotations

from typing import Any

from seo_content_engine.domain.enums import EntityType, ListingType, PageType
from seo_content_engine.utils.formatters import compact_dict


class EntityNormalizer:
    @staticmethod
    def detect_entity_type(main_data: dict[str, Any], rates_data: dict[str, Any]) -> EntityType:
        rates_type = rates_data.get("data", {}).get("type", "").strip().lower()
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
    def _extract_review_summary(rating_review: dict[str, Any]) -> dict[str, Any]:
        overview = {}
        rating_overview = rating_review.get("ratingOverview", [])
        if rating_overview and isinstance(rating_overview[0], dict):
            item = rating_overview[0]
            overview = compact_dict(
                {
                    "avg_rating": item.get("AvgRating"),
                    "rating_count": item.get("RatingCount"),
                    "review_count": item.get("ReviewCount"),
                    "min_rating": item.get("MinimumRating"),
                    "max_rating": item.get("MaximimRating"),
                }
            )

        star_distribution = []
        for item in rating_review.get("ratingStarCount", []):
            if not isinstance(item, dict):
                continue
            star_distribution.append(
                compact_dict(
                    {
                        "rating": item.get("Rating"),
                        "count": item.get("Count"),
                    }
                )
            )

        positive_tags = []
        for item in rating_review.get("good", []):
            if isinstance(item, dict) and item.get("tag"):
                positive_tags.append(item.get("tag"))
            elif isinstance(item, str):
                positive_tags.append(item)

        negative_tags = []
        for item in rating_review.get("bad", []):
            if isinstance(item, dict) and item.get("tag"):
                negative_tags.append(item.get("tag"))
            elif isinstance(item, str):
                negative_tags.append(item)

        return {
            "overview": overview,
            "star_distribution": star_distribution,
            "positive_tags": positive_tags[:10],
            "negative_tags": negative_tags[:10],
        }

    @staticmethod
    def _extract_ai_summary(locality_ai_data: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(locality_ai_data, dict):
            return {}

        tagged_reviews = locality_ai_data.get("tagged_reviews", [])
        normalized_tagged_reviews = []
        for item in tagged_reviews[:10]:
            if not isinstance(item, dict):
                continue
            normalized_tagged_reviews.append(
                compact_dict(
                    {
                        "topic": item.get("topic"),
                        "sentiment": item.get("sentiment"),
                        "summary": item.get("summary"),
                    }
                )
            )

        return compact_dict(
            {
                "locality_summary": locality_ai_data.get("locality_summary"),
                "tagged_reviews": normalized_tagged_reviews,
            }
        )

    @staticmethod
    def _extract_insight_rates(locality_overview: dict[str, Any], root_insight_rates: dict[str, Any]) -> dict[str, Any]:
        overview_rates = locality_overview.get("insightRates", {})
        root_rates = root_insight_rates or {}

        return compact_dict(
            {
                "name": root_rates.get("name") or overview_rates.get("name"),
                "avg_rate": root_rates.get("avgRate") or overview_rates.get("avgRate"),
                "rental_rate": root_rates.get("rentalRate") or overview_rates.get("rentalRate"),
                "rental_distribution": root_rates.get("rentalDistribution") or overview_rates.get("rentalDistribution"),
            }
        )

    @staticmethod
    def _extract_listing_count_data(listing_count_data: list[dict[str, Any]]) -> dict[str, Any]:
        sale_listing_range = {}
        rent_listing_range = {}

        for item in listing_count_data:
            if not isinstance(item, dict):
                continue

            bucket = {
                "doc_count": item.get("doc_count"),
                "min_price": (item.get("minPrice") or {}).get("value"),
                "max_price": (item.get("maxPrice") or {}).get("value"),
                "url": item.get("url"),
                "building_types": [
                    compact_dict(
                        {
                            "key": b.get("key"),
                            "doc_count": b.get("doc_count"),
                            "url": b.get("url"),
                        }
                    )
                    for b in item.get("buildingType", [])
                    if isinstance(b, dict)
                ],
            }

            key = (item.get("key") or "").strip().lower()
            if key == "sale":
                sale_listing_range = compact_dict(bucket)
            elif key == "rent":
                rent_listing_range = compact_dict(bucket)

        return {
            "sale_listing_range": sale_listing_range,
            "rent_listing_range": rent_listing_range,
        }

    @staticmethod
    def normalize(main_data: dict[str, Any], rates_data: dict[str, Any], listing_type: ListingType) -> dict[str, Any]:
        root = main_data.get("data", {})
        overview = root.get("localityOverviewData", {})
        locality_data = root.get("localityData", {})
        rates_root = rates_data.get("data", {}).get("propertyRatesData", {})
        details = rates_root.get("details", {})
        market_overview = rates_root.get("marketOverview", {})
        sale = overview.get("sale", {})
        rent = overview.get("rent", {})
        metrics = overview.get("metrics", {})
        nearby_localities = root.get("nearByLocalities", [])
        footer = root.get("saleListingFooter", {})
        rating_review = root.get("ratingReview", {})
        locality_ai_data = root.get("localityAiData", {})
        demand_supply = root.get("demandSupply", {})
        listing_count_data = root.get("listingCountData", [])
        insight_rates_root = root.get("insightRates", {})
        cms_faq = root.get("cmsFAQ", [])
        featured_projects = root.get("featuredProjects", [])
        projects_by_status = root.get("projectsByStatus", {})

        entity_type = EntityNormalizer.detect_entity_type(main_data, rates_data)
        page_type = EntityNormalizer.resolve_page_type(entity_type, listing_type)

        entity = compact_dict(
            {
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
                "overview_url": locality_data.get("overviewUrl") or root.get("url"),
                "property_rates_url": details.get("diUrl"),
                "last_modified_date": root.get("lastModifiedDate"),
            }
        )

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
            "location_rates": rates_root.get("locationRates", []),
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
            compact_dict(
                {
                    "name": item.get("subLocalityName"),
                    "city_name": item.get("cityName"),
                    "distance_km": round(item.get("distance", 0), 3) if item.get("distance") is not None else None,
                    "sale_count": item.get("sale", {}).get("count"),
                    "sale_available": item.get("sale", {}).get("available"),
                    "sale_avg_price_per_sqft": item.get("sale", {}).get("avgPricePerSqFt"),
                    "rent_count": item.get("rent", {}).get("count"),
                    "rent_available": item.get("rent", {}).get("available"),
                    "rent_avg_price_per_sqft": item.get("rent", {}).get("avgPricePerSqFt"),
                    "sale_supply_count": item.get("metrics", {}).get("sale", {}).get("supplyCount"),
                    "sale_visit_count": item.get("metrics", {}).get("sale", {}).get("visitCount"),
                    "sale_enquired_count": item.get("metrics", {}).get("sale", {}).get("enquiredCount"),
                    "url": item.get("url"),
                }
            )
            for item in nearby_localities[:10]
        ]

        normalized_cms_faq = [
            compact_dict({"question": item.get("question"), "answer": item.get("answer")})
            for item in cms_faq[:10]
            if isinstance(item, dict)
        ]

        normalized_featured_projects = [
            compact_dict(
                {
                    "name": item.get("projectName") or item.get("name"),
                    "url": item.get("projectUrl") or item.get("url"),
                }
            )
            for item in featured_projects[:10]
            if isinstance(item, dict)
        ]

        return {
            "entity": entity,
            "listing_summary": listing_summary,
            "pricing_summary": pricing_summary,
            "distributions": distributions,
            "links": links,
            "nearby_localities": nearby,
            "top_projects": rates_root.get("topProjects", {}),
            "review_summary": EntityNormalizer._extract_review_summary(rating_review),
            "ai_summary": EntityNormalizer._extract_ai_summary(locality_ai_data),
            "insight_rates": EntityNormalizer._extract_insight_rates(overview, insight_rates_root),
            "demand_supply": demand_supply,
            "listing_ranges": EntityNormalizer._extract_listing_count_data(listing_count_data),
            "cms_faq": normalized_cms_faq,
            "featured_projects": normalized_featured_projects,
            "projects_by_status": projects_by_status,
            "raw_source_meta": {
                "main_message": main_data.get("message"),
                "rates_message": rates_data.get("message"),
                "last_modified_date": root.get("lastModifiedDate"),
            },
        }

    @staticmethod
    def normalize_from_paths(
        main_datacenter_json_path: str,
        property_rates_json_path: str,
        listing_type: ListingType,
        source_loader,
    ) -> dict[str, Any]:
        main_data = source_loader.load_json(main_datacenter_json_path)
        rates_data = source_loader.load_json(property_rates_json_path)
        return EntityNormalizer.normalize(
            main_data=main_data,
            rates_data=rates_data,
            listing_type=listing_type,
        )