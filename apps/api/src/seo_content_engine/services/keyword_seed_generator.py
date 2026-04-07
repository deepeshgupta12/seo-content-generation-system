from __future__ import annotations

from seo_content_engine.domain.enums import PageType


class KeywordSeedGenerator:
    @staticmethod
    def generate(normalized: dict) -> list[str]:
        entity = normalized["entity"]
        page_type = PageType(entity["page_type"])

        entity_name = entity["entity_name"]
        city_name = entity["city_name"]
        micromarket_name = entity.get("micromarket_name")
        pincode = entity.get("pincode")

        base_location = f"{entity_name} {city_name}".strip()
        seeds: list[str] = []

        if page_type.value == "resale_locality":
            seeds.extend(
                [
                    f"resale properties in {base_location}",
                    f"properties for sale in {base_location}",
                    f"resale flats in {base_location}",
                    f"flats for sale in {base_location}",
                    f"apartments for sale in {base_location}",
                    f"property prices in {base_location}",
                    f"ready to move flats in {base_location}",
                    f"1 bhk flats for sale in {base_location}",
                    f"2 bhk flats for sale in {base_location}",
                    f"3 bhk flats for sale in {base_location}",
                    f"4 bhk flats for sale in {base_location}",
                    f"resale flat in {entity_name} with parking",
                    f"resale apartment in {base_location} ready possession",
                    f"affordable flats for sale in {base_location}",
                ]
            )
            if pincode:
                seeds.append(f"{entity_name} flat for sale {pincode}")
                seeds.append(f"resale property {entity_name} {pincode}")
            if micromarket_name:
                seeds.append(f"property for sale in {entity_name} {city_name}")

        elif page_type.value == "resale_micromarket":
            seeds.extend(
                [
                    f"resale properties in {entity_name} {city_name}",
                    f"resale property in {entity_name}",
                    f"properties for sale in {entity_name} {city_name}",
                    f"flats for sale in {entity_name} {city_name}",
                    f"property prices in {entity_name} {city_name}",
                    f"ready to move properties in {entity_name} {city_name}",
                    f"localities in {entity_name} for resale",
                    f"1 bhk flats for sale in {entity_name} {city_name}",
                    f"2 bhk flats for sale in {entity_name} {city_name}",
                    f"3 bhk flats for sale in {entity_name} {city_name}",
                    f"affordable flats in {entity_name} {city_name}",
                    f"resale flats {entity_name} {city_name} ready possession",
                ]
            )

        elif page_type.value == "resale_city":
            seeds.extend(
                [
                    f"resale properties in {city_name}",
                    f"properties for sale in {city_name}",
                    f"flats for sale in {city_name}",
                    f"resale flats in {city_name}",
                    f"property prices in {city_name}",
                    f"ready to move properties in {city_name}",
                    f"best area to buy resale property in {city_name}",
                    f"resale property {city_name} by zone",
                    f"1 bhk resale flat {city_name}",
                    f"2 bhk flats for sale in {city_name}",
                    f"3 bhk flats for sale in {city_name}",
                    f"4 bhk resale flat {city_name}",
                    f"affordable resale flat {city_name}",
                    f"resale flat {city_name} under budget",
                ]
            )

        deduped: list[str] = []
        seen = set()
        for seed in seeds:
            normalized_seed = " ".join(seed.lower().split())
            if normalized_seed not in seen:
                seen.add(normalized_seed)
                deduped.append(seed)

        return deduped
