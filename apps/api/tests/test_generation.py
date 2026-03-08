from pathlib import Path

from fastapi.testclient import TestClient
from seo_content_engine.main import app

client = TestClient(app)


def test_blueprint_generation() -> None:
    project_root = Path(__file__).resolve().parents[3]
    main_json = "/mnt/data/Andheri West Locality.json"
    rates_json = "/mnt/data/Andheri West Property rates.json"

    response = client.post(
        "/v1/generate/blueprint",
        json={
            "main_datacenter_json_path": main_json,
            "property_rates_json_path": rates_json,
            "listing_type": "resale",
            "write_artifact": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["blueprint"]["entity"]["entity_name"] == "Andheri West"
    assert payload["blueprint"]["page_type"] == "resale_locality"