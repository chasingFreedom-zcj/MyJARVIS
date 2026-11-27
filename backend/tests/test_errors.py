from fastapi.testclient import TestClient


def test_validation_error_has_consistent_response_shape(
    client: TestClient,
) -> None:
    response = client.get("/profiles/not-an-integer")

    assert response.status_code == 422

    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert body["error"]["message"] == "请求参数校验失败"
    assert body["error"]["request_id"] == response.headers["X-Request-ID"]
    assert body["error"]["details"]


def test_not_found_error_has_consistent_response_shape(
    client: TestClient,
) -> None:
    response = client.get("/route-that-does-not-exist")

    assert response.status_code == 404

    body = response.json()
    assert body["error"]["code"] == "not_found"
    assert body["error"]["request_id"] == response.headers["X-Request-ID"]
