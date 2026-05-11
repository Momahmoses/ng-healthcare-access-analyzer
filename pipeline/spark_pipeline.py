"""
Healthcare Access PySpark Pipeline — Azure Databricks
Computes facility density, travel-time catchments, and gap scores per state.
"""
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType
import os


def get_spark() -> SparkSession:
    return (SparkSession.builder
            .appName("HealthcareAccessPipeline")
            .config("fs.azure.account.key.<STORAGE_ACCOUNT>.blob.core.windows.net",
                    os.getenv("AZURE_STORAGE_KEY", ""))
            .getOrCreate())


def load_data(spark, path="data/"):
    facilities = spark.read.csv(f"{path}facilities.csv", header=True, inferSchema=True)
    population = spark.read.csv(f"{path}population_grid.csv", header=True, inferSchema=True)
    gaps = spark.read.csv(f"{path}health_gaps.csv", header=True, inferSchema=True)
    return facilities, population, gaps


def compute_facility_density(facilities_df, gaps_df):
    """Facilities per 100k population per state."""
    facility_counts = (
        facilities_df
        .filter(F.col("operational") == True)
        .groupBy("state")
        .agg(
            F.count("*").alias("total_facilities"),
            F.sum("beds").alias("total_beds"),
            F.sum("doctors").alias("total_doctors"),
            F.countDistinct("type").alias("facility_types"),
        )
    )
    return facility_counts.join(gaps_df.select("state", "population", "lat", "lon"),
                                on="state", how="left") \
        .withColumn("facilities_per_100k",
                    (F.col("total_facilities") / F.col("population") * 100000).cast(DoubleType())) \
        .withColumn("beds_per_1k",
                    (F.col("total_beds") / F.col("population") * 1000).cast(DoubleType())) \
        .withColumn("doctors_per_10k",
                    (F.col("total_doctors") / F.col("population") * 10000).cast(DoubleType()))


def identify_underserved_states(density_df, threshold_facilities=10.0, threshold_beds=0.5):
    """Tag states as underserved based on WHO benchmarks."""
    return density_df.withColumn(
        "is_underserved",
        (F.col("facilities_per_100k") < threshold_facilities) |
        (F.col("beds_per_1k") < threshold_beds)
    ).withColumn(
        "priority_tier",
        F.when(F.col("facilities_per_100k") < 5, "Critical")
         .when(F.col("facilities_per_100k") < 10, "High")
         .when(F.col("facilities_per_100k") < 20, "Moderate")
         .otherwise("Adequate")
    )


def compute_coverage_by_type(facilities_df):
    return (
        facilities_df
        .filter(F.col("operational") == True)
        .groupBy("state", "type")
        .agg(F.count("*").alias("count"))
        .groupBy("state")
        .pivot("type")
        .agg(F.first("count"))
        .fillna(0)
    )


def haversine_udf(lat1, lon1, lat2, lon2):
    """Approximate haversine distance in km (used in Spark UDFs)."""
    import math
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def save_results(df, path="data/density_output.csv"):
    df.toPandas().to_csv(path, index=False)
    print(f"Saved to {path}")


if __name__ == "__main__":
    spark = get_spark()
    facilities_df, population_df, gaps_df = load_data(spark)
    density_df = compute_facility_density(facilities_df, gaps_df)
    underserved_df = identify_underserved_states(density_df)
    underserved_df.show(10)
    save_results(underserved_df)
    spark.stop()
