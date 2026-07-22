from fastapi.testclient import TestClient


def test_donors_donation_types_and_donations_crud(
    client: TestClient,
    admin_headers: dict[str, str],
    finance_headers: dict[str, str],
) -> None:
    created_type = client.post(
        "/api/v1/donation-types",
        headers=admin_headers,
        json={"type_name": "Food Aid", "description": "Food support"},
    )
    assert created_type.status_code == 201
    type_id = created_type.json()["id"]

    assert client.get("/api/v1/donation-types?search=Food", headers=admin_headers).status_code == 200
    assert client.get(f"/api/v1/donation-types/{type_id}", headers=admin_headers).status_code == 200
    patched_type = client.patch(
        f"/api/v1/donation-types/{type_id}",
        headers=admin_headers,
        json={"description": "Updated support"},
    )
    assert patched_type.status_code == 200

    donor = client.post(
        "/api/v1/donors",
        headers=admin_headers,
        json={
            "first_name": "Amina",
            "last_name": "Donor",
            "phones": [{"phone_number": "+15550002", "is_primary": True}],
            "addresses": [{"address_line": "12 Main Street", "city": "Doha", "country": "QA"}],
        },
    )
    assert donor.status_code == 201
    donor_id = donor.json()["id"]

    filtered = client.get(
        f"/api/v1/donors?name=Amina&phone=50002&id={donor_id}",
        headers=admin_headers,
    )
    assert filtered.status_code == 200
    assert filtered.json()["total"] == 1
    assert client.get(f"/api/v1/donors/{donor_id}", headers=admin_headers).status_code == 200

    updated_donor = client.patch(
        f"/api/v1/donors/{donor_id}",
        headers=admin_headers,
        json={"last_name": "Updated"},
    )
    assert updated_donor.status_code == 200
    assert updated_donor.json()["normalized_full_name"] == "amina updated"

    noted_donor = client.post(
        f"/api/v1/donors/{donor_id}/notes",
        headers=admin_headers,
        json={"note": "Prefers email receipts"},
    )
    assert noted_donor.status_code == 200
    assert noted_donor.json()["notes"][0]["note"] == "Prefers email receipts"

    donation = client.post(
        "/api/v1/donations",
        headers=admin_headers,
        json={
            "donor_id": donor_id,
            "donation_type_id": type_id,
            "amount": "125.50",
            "currency": "EGP",
            "donation_date": "2026-01-15T10:30:00Z",
            "payment_method": "transfer",
            "receipt_number": "RCT-100",
        },
    )
    assert donation.status_code == 201
    donation_id = donation.json()["id"]

    listed_donations = client.get(
        f"/api/v1/donations?donor_id={donor_id}&donation_type_id={type_id}&status=confirmed&amount_min=100",
        headers=admin_headers,
    )
    assert listed_donations.status_code == 200
    assert listed_donations.json()["total"] == 1
    assert client.get(f"/api/v1/donations/{donation_id}", headers=admin_headers).status_code == 200

    updated_donation = client.patch(
        f"/api/v1/donations/{donation_id}",
        headers=finance_headers,
        json={"amount": "150.00", "receipt_number": "RCT-101"},
    )
    assert updated_donation.status_code == 200
    assert updated_donation.json()["amount"] == "150.00"

    noted_donation = client.post(
        f"/api/v1/donations/{donation_id}/notes",
        headers=admin_headers,
        json={"note": "Receipt reissued"},
    )
    assert noted_donation.status_code == 200
    assert noted_donation.json()["notes"][0]["note"] == "Receipt reissued"
    donor_history = client.get(f"/api/v1/donors/{donor_id}/donations", headers=admin_headers)
    assert donor_history.status_code == 200
    assert donor_history.json()[0]["id"] == donation_id

    assert client.delete(f"/api/v1/donations/{donation_id}", headers=finance_headers).status_code == 200
    assert client.delete(f"/api/v1/donations/{donation_id}", headers=finance_headers).status_code == 400

    assert client.delete(f"/api/v1/donation-types/{type_id}", headers=admin_headers).status_code == 200
    inactive = client.get("/api/v1/donation-types?include_inactive=false", headers=admin_headers)
    assert inactive.status_code == 200
    assert all(item["id"] != type_id for item in inactive.json())

    assert client.delete(f"/api/v1/donors/{donor_id}", headers=admin_headers).status_code == 200
    assert client.get(f"/api/v1/donors/{donor_id}", headers=admin_headers).status_code == 404
