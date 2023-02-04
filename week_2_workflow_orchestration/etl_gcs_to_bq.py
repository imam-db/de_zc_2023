from pathlib import Path
import pandas as pd
from prefect import flow, task
from prefect_gcp.cloud_storage import GcsBucket
from prefect_gcp import GcpCredentials


@task(log_prints=True, retries=3)
def extract_from_gcs(color: str, year: int, months: list[int]) -> Path:
    """Download trip data from GCS"""
    local_path = "../data/"
    gcs_block = GcsBucket.load("gcs-bucket")
    paths = []
    for month in months:
        gcs_path = f"data/{color}/{color}_tripdata_{year}-{month:02}.parquet"
        gcs_block.get_directory(from_path=gcs_path, local_path=local_path)
        paths.append(Path(f"{local_path}/{gcs_path}"))
    return paths


@task(log_prints=True)
def transform(path: Path) -> pd.DataFrame:
    """Data cleaning example"""
    df = pd.read_parquet(path)
    print(f'Total rows processed : {len(df.index)}')
    return df


@task()
def write_bq(df: pd.DataFrame) -> None:
    """Write DataFrame to BiqQuery"""

    gcp_credentials_block = GcpCredentials.load("gcp-creds")

    df.to_gbq(
        destination_table="dezoomcamp_tripdata.taxi_data",
        project_id="de-learning-2023",
        credentials=gcp_credentials_block.get_credentials_from_service_account(),
        chunksize=500_000,
        if_exists="append",
    )


@flow(log_prints=True)
def etl_gcs_to_bq(color: str, year: int, months: list[int]):
    """Main ETL flow to load data into Big Query"""

    paths = extract_from_gcs(color, year, months)
    df = [transform(path) for path in paths]
    combined_df = pd.concat(df, axis=0, ignore_index=True)
    print(f"Total rows transformed into big query : {len(combined_df)}")
    write_bq(combined_df)


if __name__ == "__main__":
    etl_gcs_to_bq(color, year, months)
