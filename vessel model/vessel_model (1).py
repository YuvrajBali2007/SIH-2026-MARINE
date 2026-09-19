import pandas as pd


# ============================================================
# 1. LOAD DATASET
# ============================================================

df = pd.read_csv("data/vessels.csv")


# ============================================================
# 2. BASIC DATASET CHECKS
# ============================================================

print("Dataset shape:", df.shape)

print("\nColumns:")
print(df.columns.tolist())

print("\nFirst 5 rows:")
print(df.head())

print("\nMissing values:")
print(df.isnull().sum())

print("\nData types:")
print(df.dtypes)

print("\nUnique vessel IDs:", df["vessel_id"].nunique())
print("Total rows:", len(df))

print("\nNumerical summary:")
print(df.describe().T)

print("\nDuplicate rows:", df.duplicated().sum())


# ============================================================
# 3. CHECK NUMERICAL VALUES
# ============================================================

columns_to_check = [
    "dwt",
    "engine_power",
    "vessel_age",
    "draft",
    "speed",
    "distance_nm",
    "fuel_price",
    "fuel_consumed_tpd",
    "charter_rate_usd_day"
]

print("\nMinimum values:")
print(df[columns_to_check].min())


# ============================================================
# 4. VESSEL INFORMATION
# ============================================================

print("\nVessel types:")
print(df["vessel_type"].value_counts())

print("\nRecords per vessel:")
print(df["vessel_id"].value_counts().head(10))


# ============================================================
# 5. VESSEL SUMMARY
# ============================================================

vessel_summary = df.groupby("vessel_id").agg({
    "vessel_type": "first",
    "dwt": "mean",
    "engine_power": "mean",
    "vessel_age": "mean",
    "draft": "mean",
    "speed": "mean",
    "fuel_consumed_tpd": "mean"
})

print("\nVessel summary:")
print(vessel_summary.head())


# ============================================================
# 6. CHECK VARIATION WITHIN VESSELS
# ============================================================

variation = df.groupby("vessel_id").agg({
    "dwt": "nunique",
    "engine_power": "nunique",
    "vessel_age": "nunique",
    "draft": "nunique",
    "speed": "nunique",
    "fuel_consumed_tpd": "nunique"
})

print("\nNumber of different values per vessel:")
print(variation.head(10))


# ============================================================
# 7. SUITABILITY FUNCTION
# ============================================================

def check_suitability(
    vessel,
    cargo_tonnes,
    distance_nm,
    max_allowed_draft,
    required_days
):
    voyage_days = distance_nm / vessel["speed"] / 24

    if vessel["dwt"] < cargo_tonnes:
        return False, "Insufficient capacity"

    if vessel["draft"] > max_allowed_draft:
        return False, "Draft exceeds limit"

    if voyage_days > required_days:
        return False, "Too slow"

    return True, "Suitable"


def normalize_higher_better(series):
    if series.max() == series.min():
        return pd.Series(100, index=series.index)

    return (
        (series - series.min())
        / (series.max() - series.min())
        * 100
    )


def normalize_lower_better(series):
    if series.max() == series.min():
        return pd.Series(100, index=series.index)

    return (
        (series.max() - series)
        / (series.max() - series.min())
        * 100
    )


def rank_vessels(
    vessel_data,
    cargo_tonnes,
    distance_nm,
    max_allowed_draft,
    required_days,
    fuel_predictions=None
):

    df = vessel_data.copy()

    if fuel_predictions is not None:
        df["fuel_consumed_tpd"] = fuel_predictions

    # --------------------------------
    # 1. Suitability
    # --------------------------------

    results = []

    for _, vessel in df.iterrows():

        suitable, reason = check_suitability(
            vessel,
            cargo_tonnes,
            distance_nm,
            max_allowed_draft,
            required_days
        )

        results.append({
            "candidate_id": vessel["candidate_id"],
            "suitable": suitable,
            "reason": reason
        })

    suitability_df = pd.DataFrame(results)

    df["suitable"] = suitability_df["suitable"].values
    df["suitability_reason"] = suitability_df["reason"].values

    # --------------------------------
    # 2. Remove unsuitable vessels
    # --------------------------------

    suitable = df[df["suitable"]].copy()

    if len(suitable) == 0:
        return pd.DataFrame()

    # --------------------------------
    # 3. Temporary fuel efficiency
    # --------------------------------

    suitable["fuel_efficiency"] = (
        suitable["fuel_consumed_tpd"]
        / suitable["dwt"]
    )

    # --------------------------------
    # 4. Normalize factors
    # --------------------------------

    suitable["capacity_score"] = normalize_higher_better(
        suitable["dwt"]
    )

    suitable["speed_score"] = normalize_higher_better(
        suitable["speed"]
    )

    suitable["fuel_score"] = normalize_lower_better(
        suitable["fuel_efficiency"]
    )

    suitable["charter_cost_score"] = normalize_lower_better(
        suitable["charter_rate_usd_day"]
    )

    suitable["age_score"] = normalize_lower_better(
        suitable["vessel_age"]
    )

    # --------------------------------
    # 5. Final score
    # --------------------------------

    suitable["vessel_score"] = (
        suitable["capacity_score"] * 0.20
        + suitable["speed_score"] * 0.15
        + suitable["fuel_score"] * 0.25
        + suitable["charter_cost_score"] * 0.30
        + suitable["age_score"] * 0.10
    )

    # --------------------------------
    # 6. Rank
    # --------------------------------

    ranked = suitable.sort_values(
        "vessel_score",
        ascending=False
    ).copy()

    ranked["rank"] = range(1, len(ranked) + 1)

    # --------------------------------
    # 7. Output columns
    # --------------------------------

    output_columns = [
        "rank",
        "candidate_id",
        "vessel_id",
        "vessel_type",
        "dwt",
        "speed",
        "draft",
        "vessel_age",
        "charter_rate_usd_day",
        "fuel_efficiency",
        "vessel_score"
    ]

    return ranked[output_columns]

ranked_vessels = rank_vessels(
    df,
    cargo_tonnes=60000,
    distance_nm=8500,
    max_allowed_draft=12,
    required_days=30
)

print("\nTOP 10 VESSELS:")
print(ranked_vessels.head(10))