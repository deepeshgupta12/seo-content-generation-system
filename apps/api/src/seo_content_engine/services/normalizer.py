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
    def _extract_specific_property_type_from_url(url: str | None) -> str | None:
        if not url or not isinstance(url, str):
            return None

        lowered = url.strip().lower()
        if not lowered:
            return None

        property_type_aliases = {
            "Apartment": ["apartment", "apartments", "flat", "flats"],
            "Builder Floor": ["builder-floor", "builder floor", "builder-floors", "builder floors"],
            "Villa": ["villa", "villas"],
            "Plot": ["plot", "plots"],
            "House": ["house", "houses", "independent-house", "independent house"],
            "Penthouse": ["penthouse", "penthouses"],
            "Studio": ["studio", "studios"],
            "Office Space": ["office-space", "office space", "office-spaces", "office spaces"],
            "Shop": ["shop", "shops"],
            "Warehouse": ["warehouse", "warehouses"],
            "Showroom": ["showroom", "showrooms"],
        }

        for canonical, aliases in property_type_aliases.items():
            if any(alias in lowered for alias in aliases):
                return canonical

        return None

    @staticmethod
    def _infer_page_property_type_context(
        overview_url: str | None,
        property_rates_url: str | None,
    ) -> dict[str, Any]:
        for candidate_url in [overview_url, property_rates_url]:
            detected = EntityNormalizer._extract_specific_property_type_from_url(candidate_url)
            if detected:
                return {
                    "scope": "specific",
                    "property_type": detected,
                    "source_url": candidate_url,
                }

        return {
            "scope": "all",
            "property_type": None,
            "source_url": overview_url or property_rates_url,
        }

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
    def _extract_property_rates_ai_data(property_rates_ai_data: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(property_rates_ai_data, dict):
            return {}

        list_fields = [
            "investmentOpportunities",
            "marketChallenges",
            "marketStrengths",
        ]

        normalized_lists: dict[str, list[str]] = {}
        for field_name in list_fields:
            values = property_rates_ai_data.get(field_name, [])
            cleaned_values: list[str] = []
            if isinstance(values, list):
                for item in values[:10]:
                    if isinstance(item, str) and item.strip():
                        cleaned_values.append(item.strip())
            normalized_lists[field_name] = cleaned_values

        return compact_dict(
            {
                "market_snapshot": property_rates_ai_data.get("marketSnapshotOverview"),
                "insights_long": property_rates_ai_data.get("insightsLong"),
                "insights_short": property_rates_ai_data.get("insightsShort"),
                "asking_price_trends_description": property_rates_ai_data.get("askingPriceTrendsDescription"),
                "by_area_description": property_rates_ai_data.get("byAreaDescription"),
                "rates_by_property_types_description": property_rates_ai_data.get("ratesByPropertyTypesDescription"),
                "rates_by_project_status_description": property_rates_ai_data.get("ratesByProjectStatusDescription"),
                "top_projects_asking_description": property_rates_ai_data.get("topProjectsAskingDescription"),
                "registration_overview_description": property_rates_ai_data.get("registrationOverviewDescription"),
                "top_projects_by_transactions_description": property_rates_ai_data.get("topProjectsByTransactionsDescription"),
                "top_projects_by_value_description": property_rates_ai_data.get("topProjectsByValueDescription"),
                "top_developers_by_transactions_description": property_rates_ai_data.get("topDevelopersByTransactionsDescription"),
                "top_developers_by_value_description": property_rates_ai_data.get("topDevelopersByValueDescription"),
                "recent_transactions_description": property_rates_ai_data.get("recentTransactionsDescription"),
                "investment_opportunities": normalized_lists["investmentOpportunities"],
                "market_challenges": normalized_lists["marketChallenges"],
                "market_strengths": normalized_lists["marketStrengths"],
            }
        )

    @staticmethod
    def _extract_insight_rates(locality_overview: dict[str, Any], root_insight_rates: dict[str, Any]) -> dict[str, Any]:
        overview_rates = locality_overview.get("insightRates", {}) if isinstance(locality_overview, dict) else {}
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
    def _city_sale_summary_from_megamenu(mega_menu_buy: dict[str, Any]) -> dict[str, Any]:
        popular_searches = mega_menu_buy.get("Popular Searches", []) if isinstance(mega_menu_buy, dict) else []
        property_type_links = mega_menu_buy.get("Property Type", []) if isinstance(mega_menu_buy, dict) else []
        by_bhk_links = mega_menu_buy.get("By BHK", []) if isinstance(mega_menu_buy, dict) else []

        sale_count = None
        total_listings = None

        for item in popular_searches:
            if not isinstance(item, dict):
                continue
            title = (item.get("title") or item.get("name") or "").lower()
            if "property in" in title or "property for sale" in title:
                sale_count = item.get("doc_count")
                total_listings = item.get("doc_count")
                break

        total_projects = None
        for item in mega_menu_buy.get("New Projects in Mumbai", []):
            if isinstance(item, dict) and item.get("doc_count") is not None:
                total_projects = item.get("doc_count")
                break

        return compact_dict(
            {
                "sale_count": sale_count,
                "total_listings": total_listings,
                "total_projects": total_projects,
                "sale_available": sale_count,
                "sale_property_type_count": len(property_type_links) if property_type_links else None,
                "sale_bhk_link_count": len(by_bhk_links) if by_bhk_links else None,
            }
        )

    @staticmethod
    def _city_distributions_from_megamenu(mega_menu_buy: dict[str, Any]) -> dict[str, Any]:
        by_bhk = mega_menu_buy.get("By BHK", []) if isinstance(mega_menu_buy, dict) else []
        property_types = mega_menu_buy.get("Property Type", []) if isinstance(mega_menu_buy, dict) else []

        bhk_distribution = []
        for item in by_bhk:
            if not isinstance(item, dict):
                continue
            bhk_distribution.append(
                compact_dict(
                    {
                        "key": item.get("name"),
                        "doc_count": item.get("doc_count"),
                        "url": item.get("url"),
                    }
                )
            )

        property_type_distribution = []
        for item in property_types:
            if not isinstance(item, dict):
                continue
            property_type_distribution.append(
                compact_dict(
                    {
                        "key": item.get("name"),
                        "doc_count": item.get("doc_count"),
                        "url": item.get("url"),
                    }
                )
            )

        return {
            "sale_unit_type_distribution": bhk_distribution,
            "sale_property_type_distribution": property_type_distribution,
            "rent_unit_type_distribution": [],
            "rent_property_type_distribution": [],
        }

    @staticmethod
    def _city_links_from_megamenu(mega_menu_buy: dict[str, Any]) -> dict[str, Any]:
        by_bhk = mega_menu_buy.get("By BHK", []) if isinstance(mega_menu_buy, dict) else []
        property_types = mega_menu_buy.get("Property Type", []) if isinstance(mega_menu_buy, dict) else []
        new_projects = mega_menu_buy.get("New Projects in Mumbai", []) if isinstance(mega_menu_buy, dict) else []

        sale_unit_type_urls = [
            [
                compact_dict(
                    {
                        "unitType": item.get("name"),
                        "url": item.get("url"),
                    }
                )
            ]
            for item in by_bhk
            if isinstance(item, dict) and item.get("name") and item.get("url")
        ]

        sale_property_type_urls = [
            [
                compact_dict(
                    {
                        "propertyType": item.get("name"),
                        "url": item.get("url"),
                    }
                )
            ]
            for item in property_types
            if isinstance(item, dict) and item.get("name") and item.get("url")
        ]

        sale_quick_links = [
            compact_dict(
                {
                    "label": item.get("name"),
                    "url": item.get("url"),
                }
            )
            for item in new_projects
            if isinstance(item, dict) and item.get("name") and item.get("url")
        ]

        return {
            "sale_unit_type_urls": sale_unit_type_urls,
            "sale_property_type_urls": sale_property_type_urls,
            "sale_quick_links": sale_quick_links,
        }

    @staticmethod
    def _city_nearby_from_rates(rates_root: dict[str, Any], city_name: str | None) -> list[dict[str, Any]]:
        nearby = []
        for item in rates_root.get("micromarketRates", [])[:10]:
            if not isinstance(item, dict):
                continue
            nearby.append(
                compact_dict(
                    {
                        "name": item.get("name"),
                        "city_name": city_name,
                        "sale_avg_price_per_sqft": item.get("avgRate"),
                    }
                )
            )
        return nearby

    @staticmethod
    def normalize(main_data: dict[str, Any], rates_data: dict[str, Any], listing_type: ListingType) -> dict[str, Any]:
        root = main_data.get("data", {})
        overview = root.get("localityOverviewData", {})
        locality_data = root.get("localityData", {})
        city_data = root.get("cityData", {})
        mega_menu = root.get("megaMenu", {})
        mega_menu_buy = mega_menu.get("Buy", {}) if isinstance(mega_menu, dict) else {}

        rates_data_root = rates_data.get("data", {})
        rates_root = rates_data_root.get("propertyRatesData", {})
        property_rates_ai_data = rates_data_root.get("propertyRatesAiData", {})
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

        if entity_type == EntityType.CITY:
            city_name = (
                root.get("cityName")
                or city_data.get("cityName")
                or details.get("cityName")
                or details.get("name")
            )
            entity_name = details.get("name") or city_name
            page_property_type_context = EntityNormalizer._infer_page_property_type_context(
                root.get("url"),
                details.get("diUrl"),
            )
            entity_name = details.get("name") or city_name

            entity = compact_dict(
                {
                    "entity_type": entity_type.value,
                    "page_type": page_type.value,
                    "listing_type": listing_type.value,
                    "entity_name": entity_name,
                    "city_name": city_name,
                    "entity_id": details.get("id") or root.get("beatsCityId") or city_data.get("beatsCityId"),
                    "city_id": details.get("cityId") or root.get("beatsCityId") or city_data.get("beatsCityId"),
                    "beats_city_id": root.get("beatsCityId") or city_data.get("beatsCityId"),
                    "dotcom_city_id": root.get("dotcomCityId") or city_data.get("dotcomCityId"),
                    "page_property_type_scope": page_property_type_context.get("scope"),
                    "page_property_type": page_property_type_context.get("property_type"),
                    "latitude": city_data.get("latitude"),
                    "longitude": city_data.get("longitude"),
                    "overview_url": root.get("url"),
                    "property_rates_url": details.get("diUrl"),
                    "last_modified_date": root.get("lastModifiedDate"),
                }
            )

            listing_summary = EntityNormalizer._city_sale_summary_from_megamenu(mega_menu_buy)

            pricing_summary = {
                "asking_price": market_overview.get("askingPrice"),
                "registration_rate": market_overview.get("registrationRate"),
                "avg_rental_rate": market_overview.get("avgRentalRate"),
                "price_trend": rates_root.get("priceTrend", []),
                "location_rates": rates_root.get("micromarketRates", []),
                "micromarket_rates": rates_root.get("micromarketRates", []),
                "property_types": rates_root.get("propertyTypes", []),
                "property_status": rates_root.get("propertyStatus", []),
            }

            distributions = EntityNormalizer._city_distributions_from_megamenu(mega_menu_buy)
            links = EntityNormalizer._city_links_from_megamenu(mega_menu_buy)
            nearby = EntityNormalizer._city_nearby_from_rates(rates_root, city_name)

        else:
            page_property_type_context = EntityNormalizer._infer_page_property_type_context(
                locality_data.get("overviewUrl") or root.get("url"),
                details.get("diUrl"),
            )
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
                    "page_property_type_scope": page_property_type_context.get("scope"),
                    "page_property_type": page_property_type_context.get("property_type"),
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
                "micromarket_rates": rates_root.get("micromarketRates", []),
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
            "property_rates_ai_summary": EntityNormalizer._extract_property_rates_ai_data(property_rates_ai_data),
            "insight_rates": EntityNormalizer._extract_insight_rates(overview, insight_rates_root),
            "demand_supply": demand_supply,
            "listing_ranges": EntityNormalizer._extract_listing_count_data(listing_count_data),
            "cms_faq": normalized_cms_faq,
            "featured_projects": normalized_featured_projects,
            "projects_by_status": projects_by_status,
            "page_property_type_context": page_property_type_context,
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