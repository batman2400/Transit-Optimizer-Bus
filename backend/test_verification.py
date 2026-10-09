import json
from fastapi.testclient import TestClient
from main import app, _load_artifacts

_load_artifacts()
client = TestClient(app)

print("=== 1. Health / Root Endpoint ===")
res_root = client.get("/")
assert res_root.status_code == 200, f"Expected 200, got {res_root.status_code}"
root_json = res_root.json()
print("Service:", root_json["service"])
print("Framework:", root_json["framework"])
print("Input dim:", root_json["input_dim"])
print("Stops:", len(root_json["stops"]), "stops")

print("\n=== 2. Single Predict Endpoint ===")
res_pred = client.post("/predict", json={
    "date": "2026-10-07",
    "hour": 8,
    "direction": "Inbound_to_Pettah",
    "stop_name": "Kollupitiya",
    "weather": "Clear"
})
assert res_pred.status_code == 200
pax = res_pred.json()["passenger_count"]
print(f"Predicted single stop (Kollupitiya 08:00): {pax:.1f} pax")
assert pax > 0, "Passenger count should be > 0"

print("\n=== 3. Batch Predict Endpoint ===")
res_batch = client.post("/predict/batch", json={
    "requests": [
        {"date": "2026-10-07", "hour": 8, "direction": "Inbound_to_Pettah", "stop_name": "Panadura"},
        {"date": "2026-10-07", "hour": 8, "direction": "Inbound_to_Pettah", "stop_name": "Pettah"}
    ]
})
assert res_batch.status_code == 200
preds = res_batch.json()["predictions"]
print("Batch predictions count:", len(preds), f"(Panadura: {preds[0]:.1f}, Pettah: {preds[1]:.1f})")

print("\n=== 4. Dispatch Scenario A: Weekday 08:00 AM Peak (Rush Hour) ===")
res_am = client.post("/dispatch", json={
    "date": "2026-10-07",
    "hour": 8,
    "direction": "Inbound_to_Pettah",
    "weather": "Clear"
})
assert res_am.status_code == 200
data_am = res_am.json()
d_am = data_am["dispatch_recommendation"]
cal_am = data_am["calendar_context"]
print(f"Calendar Day: {cal_am['day_name']} (Weekend: {cal_am['is_weekend']}, Holiday: {cal_am['is_public_holiday']})")
print(f"Peak Period: {cal_am['peak_period']}")
print(f"Peak Load: {d_am['peak_load']} at stop: {d_am['peak_stop']}")
print(f"Buses Needed: {d_am['buses_needed']}")
print(f"Headway: {d_am['headway_minutes']} minutes (Expected tight: headway <= 15)")
print(f"Corridor ETA: {d_am['corridor_eta_minutes']} min (Congestion: {d_am['congestion_factor']}x)")
assert d_am["headway_minutes"] <= 15, "Rush hour headway should be tight"
assert d_am["buses_needed"] >= 2, "Peak rush should need >= 2 buses"

print("\n=== 5. Dispatch Scenario B: Off-Peak / Night (02:00) ===")
res_night = client.post("/dispatch", json={
    "date": "2026-10-07",
    "hour": 2,
    "direction": "Inbound_to_Pettah"
})
d_night = res_night.json()["dispatch_recommendation"]
print(f"Night Peak Load: {d_night['peak_load']} pax, Buses: {d_night['buses_needed']}, Headway: {d_night['headway_minutes']} min")
assert d_night["headway_minutes"] == 30, "Night headway should clamp at max 30 min"

print("\n=== 6. Dispatch Scenario C: Poya Day Holiday Override ===")
res_poya = client.post("/dispatch", json={
    "date": "2026-10-07",
    "hour": 8,
    "direction": "Inbound_to_Pettah",
    "holiday_mode": "poya"
})
d_poya = res_poya.json()["dispatch_recommendation"]
cal_poya = res_poya.json()["calendar_context"]
print(f"Poya Holiday Type: {cal_poya['holiday_type']}, Peak Load: {d_poya['peak_load']} pax, Headway: {d_poya['headway_minutes']} min")
assert cal_poya["is_public_holiday"] == 1
assert d_poya["peak_load"] < d_am["peak_load"], "Poya demand should be lower than regular weekday"

print("\n=== 7. Dispatch Scenario D: Event Override ===")
res_event = client.post("/dispatch", json={
    "date": "2026-10-07",
    "hour": 8,
    "direction": "Inbound_to_Pettah",
    "event_override": 1
})
d_event = res_event.json()["dispatch_recommendation"]
print(f"Event Peak Load: {d_event['peak_load']} pax (vs Normal: {d_am['peak_load']} pax), Buses: {d_event['buses_needed']}")
assert d_event["peak_load"] > d_am["peak_load"], "Special event should spike demand"

print("\n>>> ALL 7 SYSTEM VERIFICATION CHECKS PASSED PERFECTLY! <<<")
