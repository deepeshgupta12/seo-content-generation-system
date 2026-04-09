"""Square Yards URL parser — extracts all page filters from a canonical SY URL.

Supported URL families (all under ``squareyards.com/sale/``):

    Property Type only
        apartments-for-sale-in-{loc}
        villas-for-sale-in-{loc}
        builder-floors-for-sale-in-{loc}
        ...

    BHK only
        {N}-bhk-for-sale-in-{loc}
        {N}-rk-for-sale-in-{loc}
        studio-for-sale-in-{loc}

    Property Type + BHK
        {N}-bhk-{property-type}-in-{loc}-for-sale

    Budget (standalone)
        properties-for-sale-in-{loc}-under-{X}-lakhs
        properties-for-sale-in-{loc}-under-{X}-crore

    Property Type + Budget
        {property-type}-in-{loc}-under-{X}-lakhs-for-sale
        {property-type}-in-{loc}-between-{X}-lakhs-to-{Y}-lakhs-for-sale

    Property Type + BHK + Budget
        {N}-bhk-{property-type}-in-{loc}-under-{X}-lakhs-for-sale

    Furnishing Type
        furnished-properties-for-sale-in-{loc}
        semi-furnished-properties-for-sale-in-{loc}
        gated-community-for-sale-in-{loc}

    Owner / No-Brokerage
        owner-properties-for-sale-in-{loc}
        property-in-{loc}-without-brokerage-for-sale

    Amenities
        properties-for-sale-in-{loc}-with-{amenity}
"""

from __future__ import annotations

import re
from typing import Any


class UrlParser:
    """Parse a Square Yards sale URL and return a structured ``PageFilters`` dict."""

    # ── Property type aliases → canonical label ─────────────────────────────
    _PROPERTY_TYPE_MAP: dict[str, str] = {
        "apartment": "Apartment",
        "apartments": "Apartment",
        "flat": "Apartment",
        "flats": "Apartment",
        "apartments-flats": "Apartment",
        "builder-floor": "Builder Floor",
        "builder-floors": "Builder Floor",
        "villa": "Villa",
        "villas": "Villa",
        "plot": "Plot",
        "plots": "Plot",
        "land": "Plot",
        "lands": "Plot",
        "industrial-plot": "Plot",
        "industrial-plots": "Plot",
        "independent-house": "House",
        "independent-houses": "House",
        "house": "House",
        "houses": "House",
        "penthouse": "Penthouse",
        "penthouses": "Penthouse",
        "studio": "Studio",
        "shop": "Shop",
        "shops": "Shop",
        "office-space": "Office Space",
        "office-spaces": "Office Space",
        "showroom": "Showroom",
        "showrooms": "Showroom",
        "warehouse": "Warehouse",
        "warehouses": "Warehouse",
        "co-working-space": "Co-Working Space",
        "co-working-spaces": "Co-Working Space",
        "commercial-properties": "Commercial",
        "commercial-property": "Commercial",
    }

    # Buyer-friendly plural labels used in H1 / title
    _PROPERTY_TYPE_H1_LABEL: dict[str, str] = {
        "Apartment": "Flats",
        "Villa": "Villas",
        "Builder Floor": "Builder Floors",
        "Plot": "Plots",
        "House": "Independent Houses",
        "Penthouse": "Penthouses",
        "Studio": "Studio Apartments",
        "Office Space": "Office Spaces",
        "Shop": "Shops",
        "Showroom": "Showrooms",
        "Warehouse": "Warehouses",
        "Co-Working Space": "Co-Working Spaces",
        "Commercial": "Commercial Properties",
    }

    # BHK aliases → canonical label
    _BHK_MAP: dict[str, str] = {
        "1-rk": "1 RK",
        "1-bhk": "1 BHK",
        "2-bhk": "2 BHK",
        "3-bhk": "3 BHK",
        "4-bhk": "4 BHK",
        "5-bhk": "5 BHK",
        "6-bhk": "6 BHK",
        "studio": "Studio",
    }

    # Furnishing type aliases → canonical label
    _FURNISHING_MAP: dict[str, str] = {
        "furnished": "Furnished",
        "semi-furnished": "Semi-Furnished",
        "gated-community": "Gated Community",
    }

    # Amenity aliases → display name
    _AMENITY_MAP: dict[str, str] = {
        "power-backup": "Power Backup",
        "gym": "Gym",
        "clubhouse": "Clubhouse",
        "swimming-pool": "Swimming Pool",
        "lift": "Lift",
        "park": "Park",
        "security": "Security",
        "parking": "Parking",
    }

    # ── Budget regex helpers ─────────────────────────────────────────────────
    # Matches "under-50-lakhs", "under-1-crore"
    _BUDGET_UNDER_RE = re.compile(
        r"under-(\d+(?:\.\d+)?)-?(lakh|lakhs|crore|crores|cr)",
        re.IGNORECASE,
    )
    # Matches "between-20-lakhs-to-50-lakhs" or "between-1-crore-to-2-crore"
    _BUDGET_BETWEEN_RE = re.compile(
        r"between-(\d+(?:\.\d+)?)-?(lakh|lakhs|crore|crores|cr)-to-(\d+(?:\.\d+)?)-?(lakh|lakhs|crore|crores|cr)",
        re.IGNORECASE,
    )

    @staticmethod
    def _amount_in_rupees(value: float, unit: str) -> int:
        unit = unit.lower().rstrip("s")  # "lakh" or "crore"
        if unit in ("crore", "cr"):
            return int(value * 1_00_00_000)
        return int(value * 1_00_000)  # lakh

    @staticmethod
    def _extract_budget(slug: str) -> tuple[int | None, int | None]:
        """Return (budget_min, budget_max) in rupees, or (None, None)."""
        m = UrlParser._BUDGET_BETWEEN_RE.search(slug)
        if m:
            lo = UrlParser._amount_in_rupees(float(m.group(1)), m.group(2))
            hi = UrlParser._amount_in_rupees(float(m.group(3)), m.group(4))
            return lo, hi
        m = UrlParser._BUDGET_UNDER_RE.search(slug)
        if m:
            hi = UrlParser._amount_in_rupees(float(m.group(1)), m.group(2))
            return None, hi
        return None, None

    @staticmethod
    def _budget_label(budget_min: int | None, budget_max: int | None) -> str:
        """Human-readable budget label for H1 / title."""
        def _fmt(n: int) -> str:
            if n >= 1_00_00_000:
                v = n / 1_00_00_000
                return f"₹{int(v) if v == int(v) else v} Cr"
            v = n / 1_00_000
            return f"₹{int(v) if v == int(v) else v} Lakh"

        if budget_min is not None and budget_max is not None:
            return f"Between {_fmt(budget_min)} to {_fmt(budget_max)}"
        if budget_max is not None:
            return f"Under {_fmt(budget_max)}"
        return ""

    @staticmethod
    def _extract_slug(url: str) -> str:
        """Strip scheme, host, and /sale/ prefix; return the slug in lower-case."""
        url = url.strip().lower()
        # Remove scheme and host
        url = re.sub(r"^https?://[^/]+", "", url)
        # Remove /sale/ prefix
        url = re.sub(r"^/sale/", "", url)
        return url

    @staticmethod
    def _extract_property_type(slug: str) -> str | None:
        """Scan the slug for property type tokens; return canonical name or None."""
        # Sort by length descending so longer patterns match first (e.g.
        # "builder-floors" before "builder")
        for token in sorted(UrlParser._PROPERTY_TYPE_MAP, key=len, reverse=True):
            if token in slug:
                return UrlParser._PROPERTY_TYPE_MAP[token]
        return None

    @staticmethod
    def _extract_bhk(slug: str) -> str | None:
        """Detect BHK / RK / Studio pattern; return canonical label or None."""
        # Studio is also caught by property type map — check here first
        if "studio" in slug:
            return "Studio"
        for token in sorted(UrlParser._BHK_MAP, key=len, reverse=True):
            if token in slug:
                return UrlParser._BHK_MAP[token]
        return None

    @staticmethod
    def _extract_furnishing(slug: str) -> str | None:
        # Sort longest-first so "semi-furnished" is checked before "furnished"
        for token in sorted(UrlParser._FURNISHING_MAP, key=len, reverse=True):
            if token in slug:
                return UrlParser._FURNISHING_MAP[token]
        return None

    @staticmethod
    def _extract_amenities(slug: str) -> list[str]:
        found: list[str] = []
        if "-with-" in slug:
            for token, label in UrlParser._AMENITY_MAP.items():
                if f"with-{token}" in slug:
                    found.append(label)
        return found

    @staticmethod
    def _extract_ownership(slug: str) -> str | None:
        if "owner-properties" in slug or "without-brokerage" in slug:
            return "Owner"
        return None

    @staticmethod
    def _build_filters_label(
        property_type: str | None,
        bhk_config: str | None,
        budget_min: int | None,
        budget_max: int | None,
        furnishing_type: str | None,
        amenities: list[str],
        ownership_type: str | None,
    ) -> str:
        """Assemble a clean human-readable label for all active filters.

        Example outputs:
            "2 BHK Flats"
            "3 BHK Villas Under ₹2 Cr"
            "Furnished Properties"
            "Properties with Swimming Pool"
            "2 BHK Apartments Between ₹50 Lakh to ₹1 Cr"
        """
        parts: list[str] = []

        if property_type:
            friendly = UrlParser._PROPERTY_TYPE_H1_LABEL.get(property_type, property_type)
        else:
            friendly = None

        # Skip prepending bhk_config when it is redundant with the property type label.
        # e.g. "Studio" BHK + "Studio" property type → "Studio Apartments" not "Studio Studio Apartments"
        _bhk_is_redundant = (
            bhk_config is not None
            and property_type is not None
            and bhk_config.lower() == property_type.lower()
        )
        if bhk_config and not _bhk_is_redundant:
            parts.append(bhk_config)

        if furnishing_type and not property_type:
            parts.append(f"{furnishing_type} Properties")
        elif furnishing_type and property_type:
            parts.append(f"{furnishing_type} {friendly or 'Properties'}")
        elif friendly:
            parts.append(friendly)
        else:
            parts.append("Properties")

        if ownership_type:
            parts.append(f"by {ownership_type}")

        budget_str = UrlParser._budget_label(budget_min, budget_max)
        if budget_str:
            parts.append(budget_str)

        if amenities:
            parts.append("with " + " & ".join(amenities))

        return " ".join(parts)

    @classmethod
    def parse(cls, url: str) -> dict[str, Any]:
        """Parse a Square Yards sale URL and return a PageFilters dict.

        Returns
        -------
        dict with keys:
            page_url          str — original URL
            slug              str — path after /sale/
            property_type     str | None — canonical property type (e.g. "Apartment")
            bhk_config        str | None — e.g. "2 BHK", "Studio"
            budget_min        int | None — minimum budget in rupees
            budget_max        int | None — maximum budget in rupees
            budget_label      str — human-readable budget string (e.g. "Under ₹50 Lakh")
            furnishing_type   str | None — "Furnished" | "Semi-Furnished" | "Gated Community"
            amenities         list[str] — e.g. ["Gym", "Swimming Pool"]
            ownership_type    str | None — "Owner"
            filters_label     str — compact human-readable filter string for H1 use
            scope             str — "specific" if any filter detected, else "all"
            property_type_h1  str | None — buyer-friendly property type label for H1
        """
        slug = cls._extract_slug(url)

        property_type = cls._extract_property_type(slug)
        bhk_config = cls._extract_bhk(slug)
        budget_min, budget_max = cls._extract_budget(slug)
        furnishing_type = cls._extract_furnishing(slug)
        amenities = cls._extract_amenities(slug)
        ownership_type = cls._extract_ownership(slug)

        has_filter = bool(
            property_type or bhk_config or budget_min or budget_max
            or furnishing_type or amenities or ownership_type
        )

        filters_label = cls._build_filters_label(
            property_type, bhk_config, budget_min, budget_max,
            furnishing_type, amenities, ownership_type,
        )

        return {
            "page_url": url,
            "slug": slug,
            "property_type": property_type,
            "bhk_config": bhk_config,
            "budget_min": budget_min,
            "budget_max": budget_max,
            "budget_label": cls._budget_label(budget_min, budget_max),
            "furnishing_type": furnishing_type,
            "amenities": amenities,
            "ownership_type": ownership_type,
            "filters_label": filters_label,
            "scope": "specific" if has_filter else "all",
            "property_type_h1": (
                cls._PROPERTY_TYPE_H1_LABEL.get(property_type) if property_type else None
            ),
        }
