import pandas as pd
import numpy as np
import os

STATES = [
    ("Lagos", 6.5244, 3.3792, 15388000, "SW"),
    ("Kano", 12.0022, 8.5920, 13076000, "NW"),
    ("Kaduna", 10.5222, 7.4383, 8252000, "NW"),
    ("Rivers", 4.8156, 7.0498, 7303000, "SS"),
    ("Oyo", 7.3775, 3.9470, 7840000, "SW"),
    ("Abuja FCT", 9.0765, 7.3986, 3564000, "NC"),
    ("Anambra", 6.2104, 6.9623, 5527000, "SE"),
    ("Borno", 11.8846, 13.1571, 5860000, "NE"),
    ("Imo", 5.4527, 7.0201, 4856000, "SE"),
    ("Delta", 5.5320, 5.8987, 5663000, "SS"),
    ("Adamawa", 9.3265, 12.3984, 4253000, "NE"),
    ("Plateau", 9.2182, 9.5179, 4200000, "NC"),
    ("Bauchi", 10.3158, 9.8442, 6537000, "NE"),
    ("Sokoto", 13.0059, 5.2476, 4998000, "NW"),
    ("Katsina", 12.9908, 7.6018, 8036000, "NW"),
    ("Jigawa", 12.2280, 9.5616, 5829000, "NW"),
    ("Kebbi", 11.4943, 4.2333, 4459000, "NW"),
    ("Zamfara", 12.1222, 6.2236, 4515000, "NW"),
    ("Niger", 10.0008, 5.5981, 5559000, "NC"),
    ("Kwara", 8.9669, 4.3873, 3194000, "NC"),
    ("Nassarawa", 8.4994, 8.1997, 2523000, "NC"),
    ("Kogi", 7.7337, 6.6906, 4473000, "NC"),
    ("Benue", 7.3369, 8.7404, 5741000, "NC"),
    ("Taraba", 7.9993, 10.7741, 3066000, "NE"),
    ("Yobe", 12.2939, 11.4390, 3294000, "NE"),
    ("Gombe", 10.2791, 11.1673, 3256000, "NE"),
    ("Ogun", 6.9980, 3.4737, 5217000, "SW"),
    ("Osun", 7.5629, 4.5624, 4705000, "SW"),
    ("Ekiti", 7.6218, 5.2311, 3270000, "SW"),
    ("Ondo", 7.0003, 5.0000, 4671000, "SW"),
    ("Edo", 6.3350, 5.6037, 4737000, "SS"),
    ("Bayelsa", 4.7719, 6.0699, 2278000, "SS"),
    ("Cross River", 5.9631, 8.3305, 4059000, "SS"),
    ("Akwa Ibom", 5.0527, 7.9335, 5450000, "SS"),
    ("Enugu", 6.4584, 7.5464, 4411000, "SE"),
    ("Ebonyi", 6.2649, 8.0137, 2880000, "SE"),
    ("Abia", 5.3671, 7.4948, 3728000, "SE"),
]

FACILITY_TYPES = ["Primary Health Centre", "General Hospital", "Teaching Hospital",
                  "Specialist Clinic", "Private Hospital", "Maternity Centre"]


def generate_facilities(n: int = 800) -> pd.DataFrame:
    np.random.seed(42)
    records = []
    for _ in range(n):
        state = STATES[np.random.randint(len(STATES))]
        state_name, slat, slon, pop, zone = state
        is_urban = np.random.random() < 0.6
        ftype = np.random.choice(FACILITY_TYPES,
                                 p=[0.40, 0.25, 0.05, 0.08, 0.12, 0.10])
        records.append({
            "facility_id": f"NG-{_+1:05d}",
            "name": f"{state_name} {ftype} {_+1}",
            "type": ftype,
            "state": state_name,
            "zone": zone,
            "lat": slat + np.random.uniform(-0.8, 0.8),
            "lon": slon + np.random.uniform(-0.8, 0.8),
            "is_urban": is_urban,
            "beds": int(np.random.choice([10, 20, 50, 100, 200, 500],
                                          p=[0.25, 0.30, 0.25, 0.12, 0.05, 0.03])),
            "doctors": int(np.random.exponential(8)),
            "nurses": int(np.random.exponential(20)),
            "has_emergency": np.random.choice([True, False], p=[0.35, 0.65]),
            "has_maternity": np.random.choice([True, False], p=[0.55, 0.45]),
            "operational": np.random.choice([True, False], p=[0.85, 0.15]),
            "year_established": int(np.random.randint(1960, 2023)),
        })
    return pd.DataFrame(records)


def generate_population_grid() -> pd.DataFrame:
    np.random.seed(42)
    records = []
    for state_name, slat, slon, total_pop, zone in STATES:
        for _ in range(20):
            records.append({
                "state": state_name,
                "zone": zone,
                "lat": slat + np.random.uniform(-1.0, 1.0),
                "lon": slon + np.random.uniform(-1.0, 1.0),
                "population": int(total_pop / 20 * np.random.uniform(0.3, 1.7)),
                "is_rural": np.random.random() < 0.55,
                "nearest_facility_km": None,
                "access_score": None,
            })
    return pd.DataFrame(records)


def generate_health_gaps() -> pd.DataFrame:
    np.random.seed(42)
    records = []
    for state_name, slat, slon, pop, zone in STATES:
        doctor_pop_ratio = np.random.uniform(0.1, 8.0)
        coverage_pct = np.random.uniform(20, 95) if zone in ("SW", "SS", "SE") else np.random.uniform(10, 65)
        records.append({
            "state": state_name,
            "zone": zone,
            "lat": slat, "lon": slon,
            "population": pop,
            "doctors_per_10k": round(doctor_pop_ratio, 2),
            "beds_per_1k": round(np.random.uniform(0.2, 3.5), 2),
            "facilities_per_100k": round(np.random.uniform(2, 45), 1),
            "coverage_pct": round(coverage_pct, 1),
            "avg_travel_time_min": round(np.random.uniform(10, 240), 0),
            "gap_score": round(1 - coverage_pct / 100, 3),
        })
    return pd.DataFrame(records)


def save_all(output_dir: str = "data"):
    os.makedirs(output_dir, exist_ok=True)
    generate_facilities().to_csv(f"{output_dir}/facilities.csv", index=False)
    generate_population_grid().to_csv(f"{output_dir}/population_grid.csv", index=False)
    generate_health_gaps().to_csv(f"{output_dir}/health_gaps.csv", index=False)
    print("Healthcare data generated.")


if __name__ == "__main__":
    save_all()
