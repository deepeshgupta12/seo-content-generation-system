from pathlib import Path

from seo_content_engine.domain.enums import ListingType
from seo_content_engine.services.keyword_seed_generator import KeywordSeedGenerator
from seo_content_engine.services.normalizer import EntityNormalizer
from seo_content_engine.services.source_loader import SourceLoader


def test_keyword_seed_generation_for_locality() -> None:
    project_root = Path(__file__).resolve().parents[3]
    main_json = project_root / "data" / "samples" / "raw" / "andheri-west-locality.json"
    rates_json = project_root / "data" / "samples" / "raw" / "andheri-west-property-rates.json"

    normalized = EntityNormalizer.normalize(
        main_data=SourceLoader.load_json(str(main_json)),
        rates_data=SourceLoader.load_json(str(rates_json)),
        listing_type=ListingType.RESALE,
    )

    seeds = KeywordSeedGenerator.generate(normalized)

    assert len(seeds) > 0
    assert any(seed == "resale properties in Andheri West Mumbai" for seed in seeds)
    assert any(seed == "property for sale in Andheri West Mumbai" for seed in seeds)
    assert any(seed == "2 bhk flats for sale in Andheri West Mumbai" for seed in seeds)