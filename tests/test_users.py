
def test_user_registration(client):
    response = client.post(
        "/users",
        json={
            "name": "Test User",
            "email": "testuser@example.com"
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Test User"
    assert data["email"] == "testuser@example.com"
    assert data["question_balance"] == 3
    assert "id" in data


def test_duplicate_email_registration(client):
    user_data = {
        "name": "Test User",
        "email": "duplicate@example.com"
    }

    first_response = client.post("/users", json=user_data)
    second_response = client.post("/users", json=user_data)

    assert first_response.status_code == 201
    assert second_response.status_code == 409



def test_initial_question_balance(client):
    registration = client.post(
        "/users",
        json={
            "name": "Balance User",
            "email": "balance@example.com"
        }
    )

    print("Registration:", registration.status_code, registration.json())

    user_id = registration.json()["id"]

    response = client.get(f"/users/{user_id}/balance")

    print("Balance response:", response.status_code, response.json())

    assert response.status_code == 200
    assert response.json()["question_balance"] == 3



def test_balance_for_nonexistent_user(client):
    response = client.get("/users/9999/balance")

    assert response.status_code == 404
