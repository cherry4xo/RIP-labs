import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="function", autouse=True)
def setup_for_orders(client: TestClient, test_moderator_token_headers):
    """Создает несколько услуг один раз для всех тестов в этом модуле."""
    client.post("/services/", json={"title": "Service For Cart 1", "price": 100, "impact_level": 1, "assessment_type": "network_scan", "description": "d", "short_description": "sd"}, headers=test_moderator_token_headers)
    client.post("/services/", json={"title": "Service For Cart 2", "price": 200, "impact_level": 2, "assessment_type": "web_app_pentest", "description": "d", "short_description": "sd"}, headers=test_moderator_token_headers)


def test_cart_flow(client: TestClient, test_user_token_headers):
    response = client.get("/report/draft/info", headers=test_user_token_headers)
    assert response.status_code == 200
    assert response.json() == {"report_id": -1, "item_count": 0}

    response = client.post("/report/draft/assessments", json={"assessment_id": 1}, headers=test_user_token_headers)
    assert response.status_code == 200
    cart = response.json()
    order_id = cart["id"]
    assert len(cart["components"]) == 1

    response = client.get("/report/draft/info", headers=test_user_token_headers)
    assert response.status_code == 200
    assert response.json() == {"report_id": order_id, "item_count": 1}

    client.post("/report/draft/assessments", json={"assessment_id": 2}, headers=test_user_token_headers)
    
    update_data = {"protection_level": "full", "comment": "Updated comment"}
    response = client.put(f"/report/draft/assessments/1", json=update_data, headers=test_user_token_headers)
    assert response.status_code == 200
    updated_cart = response.json()
    service1_in_cart = next(item for item in updated_cart["components"] if item["vulnerability_assessment"]["id"] == 1)
    assert service1_in_cart["protection_level"] == "full"
    assert service1_in_cart["comment"] == "Updated comment"

    response = client.delete(f"/report/draft/assessments/2", headers=test_user_token_headers)
    assert response.status_code == 200
    assert len(response.json()["components"]) == 1


def test_full_order_lifecycle(client: TestClient, test_user_token_headers, test_moderator_token_headers):
    client.post("/report/draft/assessments", json={"assessment_id": 1}, headers=test_user_token_headers)
    response = client.post("/report/draft/assessments", json={"assessment_id": 2}, headers=test_user_token_headers)
    order_id = response.json()["id"]

    form_payload = {
        "target_system_info": "e2e-test.com",
        "components": [
            {"assessment_id": 1, "protection_level": "basic", "comment": "check this"},
            {"assessment_id": 2, "protection_level": "none", "comment": None},
        ]
    }
    response = client.put(f"/reports/{order_id}/form", json=form_payload, headers=test_user_token_headers)
    assert response.status_code == 200
    formed_order = response.json()
    assert formed_order["status"] == "formed"
    assert formed_order["target_system_info"] == "e2e-test.com"

    response = client.put(f"/reports/{order_id}/complete", headers=test_user_token_headers)
    assert response.status_code == 403

    response = client.put(f"/reports/{order_id}/complete", headers=test_moderator_token_headers)
    assert response.status_code == 200
    completed_order = response.json()
    assert completed_order["status"] == "completed"
    assert completed_order["moderator_login"] == "moduser"
    assert completed_order["risk_score"] == 6

    response = client.get("/reports", headers=test_user_token_headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1
    assert response.json()[0]["status"] == "completed"
