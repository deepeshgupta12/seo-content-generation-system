"""H1 — Schema Markup Generator

Generates JSON-LD structured data blocks for SEO content pages:
  - FAQPage: enables Google FAQ rich results in SERPs
  - WebPage (real-estate context): provides location entity context + breadcrumbs

Usage::

    schemas = SchemaMarkupGenerator.generate_all(draft)
    script_tags = SchemaMarkupGenerator.to_script_tags(schemas)
    # inject script_tags into HTML <head> before </head>
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class SchemaMarkupGenerator:
    """Generates JSON-LD schema markup for Square Yards SEO content pages."""

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    @staticmethod
    def generate_all(draft: dict) -> list[dict]:
        """Generate all applicable JSON-LD schema objects for a draft.

        Returns a list of JSON-LD dicts (one per @type block).  The WebPage
        schema is always first; FAQPage follows when FAQs are present.
        """
        entity: dict = draft.get("entity") or {}
        metadata: dict = draft.get("metadata") or {}
        faqs: list[dict] = draft.get("faqs") or []

        schemas: list[dict] = []

        webpage_schema = SchemaMarkupGenerator.generate_real_estate_page_schema(entity, metadata)
        if webpage_schema:
            schemas.append(webpage_schema)

        faq_schema = SchemaMarkupGenerator.generate_faq_schema(faqs)
        if faq_schema:
            schemas.append(faq_schema)

        return schemas

    @staticmethod
    def to_script_tags(schemas: list[dict]) -> list[str]:
        """Convert a list of JSON-LD schema dicts to HTML <script> tag strings.

        Each tag is indented for clean embedding inside a <head> block.
        """
        tags: list[str] = []
        for schema in schemas:
            try:
                json_str = json.dumps(schema, ensure_ascii=False, indent=2)
                tags.append(
                    f'  <script type="application/ld+json">\n{json_str}\n  </script>'
                )
            except (TypeError, ValueError) as exc:
                logger.warning("Failed to serialize JSON-LD schema block: %s", exc)
        return tags

    # ------------------------------------------------------------------ #
    # FAQPage schema                                                       #
    # ------------------------------------------------------------------ #

    @staticmethod
    def generate_faq_schema(faqs: list[dict]) -> dict | None:
        """Build a schema.org FAQPage JSON-LD object from the draft FAQ list.

        Only FAQs that have both a non-empty question and answer are included.
        Returns None when there are no valid FAQs.
        """
        if not faqs:
            return None

        main_entity: list[dict] = []
        for faq in faqs:
            question = str(faq.get("question") or "").strip()
            answer = str(faq.get("answer") or "").strip()
            if not question or not answer:
                continue
            # Prefer snippet-optimised answer when available (H2)
            snippet_answer = str(faq.get("snippet_answer") or "").strip()
            display_answer = snippet_answer if snippet_answer else answer
            main_entity.append(
                {
                    "@type": "Question",
                    "name": question,
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": display_answer,
                    },
                }
            )

        if not main_entity:
            return None

        return {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": main_entity,
        }

    # ------------------------------------------------------------------ #
    # WebPage / Real-Estate context schema                                 #
    # ------------------------------------------------------------------ #

    @staticmethod
    def generate_real_estate_page_schema(entity: dict, metadata: dict) -> dict | None:
        """Build a schema.org WebPage JSON-LD for a real estate listing category page.

        The schema embeds a ``Place`` node with geolocation and postal address,
        a ``BreadcrumbList`` for navigation, and a price hint via
        ``additionalProperty`` when ``canonical_asking_price`` is available.
        """
        entity_name: str = (entity.get("entity_name") or entity.get("name") or "").strip()
        city_name: str = (entity.get("city_name") or entity.get("city") or "").strip()
        micromarket_name: str = (entity.get("micromarket_name") or "").strip()
        page_title: str = (metadata.get("title") or metadata.get("h1") or "").strip()
        meta_description: str = (metadata.get("meta_description") or "").strip()
        overview_url: str = (entity.get("overview_url") or "").strip()
        latitude = entity.get("latitude")
        longitude = entity.get("longitude")
        pincode: str = str(entity.get("pincode") or "").strip()
        canonical_price = entity.get("canonical_asking_price")
        page_type: str = str(entity.get("page_type") or "").lower()

        if not entity_name and not page_title:
            return None

        # ---- Address node ------------------------------------------- #
        address_node: dict[str, Any] = {
            "@type": "PostalAddress",
            "addressLocality": entity_name or city_name,
            "addressCountry": "IN",
        }
        if city_name and entity_name:
            address_node["addressRegion"] = city_name
        if pincode:
            address_node["postalCode"] = pincode

        # ---- Place node --------------------------------------------- #
        place_node: dict[str, Any] = {
            "@type": "Place",
            "name": entity_name or city_name,
            "address": address_node,
        }
        if latitude is not None and longitude is not None:
            try:
                place_node["geo"] = {
                    "@type": "GeoCoordinates",
                    "latitude": float(latitude),
                    "longitude": float(longitude),
                }
            except (TypeError, ValueError):
                pass

        # Embed canonical price hint as AdditionalProperty
        if canonical_price:
            try:
                price_val = float(canonical_price)
                place_node["additionalProperty"] = {
                    "@type": "PropertyValue",
                    "name": "Canonical Asking Price per sq ft (INR)",
                    "value": price_val,
                    "unitCode": "INR",
                }
            except (TypeError, ValueError):
                pass

        # ---- BreadcrumbList ----------------------------------------- #
        breadcrumb_items: list[dict] = []
        pos = 1

        breadcrumb_items.append(
            {
                "@type": "ListItem",
                "position": pos,
                "name": "Square Yards",
                "item": "https://www.squareyards.com/",
            }
        )
        pos += 1

        if city_name:
            city_slug = city_name.lower().replace(" ", "-")
            breadcrumb_items.append(
                {
                    "@type": "ListItem",
                    "position": pos,
                    "name": f"Properties in {city_name}",
                    "item": f"https://www.squareyards.com/{city_slug}/",
                }
            )
            pos += 1

        if micromarket_name and page_type in ("resale_micromarket", "resale_locality"):
            breadcrumb_items.append(
                {
                    "@type": "ListItem",
                    "position": pos,
                    "name": f"Properties in {micromarket_name}",
                }
            )
            pos += 1

        if entity_name and page_type == "resale_locality":
            breadcrumb_items.append(
                {
                    "@type": "ListItem",
                    "position": pos,
                    "name": f"Flats for Sale in {entity_name}",
                }
            )

        # ---- Assemble WebPage schema --------------------------------- #
        schema: dict[str, Any] = {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": page_title or entity_name,
            "about": place_node,
        }
        if meta_description:
            schema["description"] = meta_description
        if overview_url:
            schema["url"] = overview_url
        if breadcrumb_items:
            schema["breadcrumb"] = {
                "@type": "BreadcrumbList",
                "itemListElement": breadcrumb_items,
            }

        return schema
