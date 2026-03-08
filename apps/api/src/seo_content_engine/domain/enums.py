from enum import Enum


class EntityType(str, Enum):
    CITY = "city"
    MICROMARKET = "micromarket"
    LOCALITY = "locality"


class ListingType(str, Enum):
    RESALE = "resale"


class PageType(str, Enum):
    RESALE_CITY = "resale_city"
    RESALE_MICROMARKET = "resale_micromarket"
    RESALE_LOCALITY = "resale_locality"