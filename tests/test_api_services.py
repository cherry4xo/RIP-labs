import io
from fastapi.testclient import TestClient


def create_service_helper(client: TestClient, headers: dict) -> int:
    service_data = {
        "title": "New Pentest", "short_description": "short", "description": "long",
        "price": 15000, "impact_level": 3, "assessment_type": "web_app_pentest"
    }
    response = client.post("/services/", json=service_data, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Pentest"
    return data["id"]


def test_create_service_as_moderator(client: TestClient, test_moderator_token_headers: dict):
    service_id = create_service_helper(client, test_moderator_token_headers)
    assert isinstance(service_id, int)


def test_create_service_as_user_fails(client: TestClient, test_user_token_headers):
    service_data = {"title": "Forbidden Service", "price": 100, "impact_level": 1, "assessment_type": "network_scan", "description": "d", "short_description": "sd"}
    response = client.post("/services/", json=service_data, headers=test_user_token_headers)
    assert response.status_code == 403


def test_update_service(client: TestClient, test_moderator_token_headers):
    service_id = create_service_helper(client, test_moderator_token_headers)
    update_data = {"title": "Updated Pentest", "price": 20000, "impact_level": 2, "assessment_type": "network_scan", "description": "d", "short_description": "sd"}
    response = client.put(f"/services/{service_id}", json=update_data, headers=test_moderator_token_headers)
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Pentest"


def test_delete_service(
    client: TestClient, 
    test_moderator_token_headers: dict
):
    service_id = create_service_helper(client, test_moderator_token_headers)
    
    dummy_image = io.BytesIO(b"dummy data")
    upload_resp = client.post(
        f"/services/{service_id}/image",
        files={"image": ("test.png", dummy_image, "image/png")},
        headers=test_moderator_token_headers
    )
    assert upload_resp.status_code == 200
    image_url = upload_resp.json()["image_url"]

    response = client.delete(f"/services/{service_id}", headers=test_moderator_token_headers)
    assert response.status_code == 204
    
    get_resp = client.get(f"/services/{service_id}")
    assert get_resp.status_code == 404


def test_upload_image(
    client: TestClient,
    test_moderator_token_headers: dict
):
    service_id = create_service_helper(client, test_moderator_token_headers)
    dummy_image = io.BytesIO(b"this is a test image")
    
    response = client.post(
        f"/services/{service_id}/image",
        files={"image": ("test.jpg", dummy_image, "image/jpeg")},
        headers=test_moderator_token_headers
    )
    
    assert response.status_code == 200
    image_url = response.json()["image_url"]
    assert image_url is not None
    assert image_url.startswith("http://test-storage.com")


def test_get_service_list_and_filter(client: TestClient, test_moderator_token_headers):
    client.post("/services/", json={"title": "Web Scan", "price": 100, "impact_level": 1, "assessment_type": "network_scan", "description": "d", "short_description": "sd"}, headers=test_moderator_token_headers)
    client.post("/services/", json={"title": "Web Pentest", "price": 200, "impact_level": 2, "assessment_type": "web_app_pentest", "description": "d", "short_description": "sd"}, headers=test_moderator_token_headers)
    
    response = client.get("/services/")
    assert response.status_code == 200
    assert len(response.json()) >= 2
    
    response = client.get("/services/", params={"title": "Scan"})
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Web Scan"