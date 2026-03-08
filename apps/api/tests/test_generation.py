from pathlib import Path

from fastapi.testclient import TestClient
from seo_content_engine.main import app

client = TestClient(app)


def test_blueprint_generation() -> None:
    project_root = Path(__file__).resolve().parents[3]
    main_json = project_root / "data" / "samples" / "raw" / "andheri-west-locality.json"
    rates_json = project_root / "data" / "samples" / "raw" / "andheri-west-property-rates.json"

    assert main_json.exists(), f"Missing sample file: {main_json}"
    assert rates_json.exists(), f"Missing sample file: {rates_json}"

    response = client.post(
        "/v1/generate/blueprint",
        json={
            "main_datacenter_json_path": str(main_json),
            "property_rates_json_path": str(rates_json),
            "listing_type": "resale",
            "write_artifact": False,
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["success"] is True
    assert payload["blueprint"]["entity"]["entity_name"] == "Andheri West"
    assert payload["blueprint"]["page_type"] == "resale_locality"