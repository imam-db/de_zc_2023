## Week 2 Homework

The goal of this homework is to familiarise users with workflow orchestration and observation. 


## Question 1. Load January 2020 data

Using the `etl_web_to_gcs.py` flow that loads taxi data into GCS as a guide, create a flow that loads the green taxi CSV dataset for January 2020 into GCS and run it. Look at the logs to find out how many rows the dataset has.

How many rows does that dataset have?

* 447,770 **
* 766,792
* 299,234
* 822,132

**Explanation:**

After encountering some errors due to the absence of folders with color names, I updated the code.

```python
@task()
def write_local(df: pd.DataFrame, color: str, dataset_file: str) -> Path:
    """Write DataFrame out locally as parquet file"""
    if not Path(f"data/{color}/").exists():
        Path(f"data/{color}/").mkdir()
    path = Path(f"data/{color}/{dataset_file}.parquet")
    df.to_parquet(path, compression="gzip")
    return path
```

Additionally, I encountered errors because columns named `tpep_pickup_datetime` and `tpep_dropoff_datetime` were missing, so I updated the code accordingly.

```python
@task(log_prints=True)
def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Fix dtype issues"""
    if "tpep_pickup_datetie" in df.columns:
        df["tpep_pickup_datetime"] = pd.to_datetime(df["tpep_pickup_datetime"])
        df["tpep_dropoff_datetime"] = pd.to_datetime(df["tpep_dropoff_datetime"])
    else:
        df["lpep_pickup_datetime"] = pd.to_datetime(df["lpep_pickup_datetime"])
        df["lpep_dropoff_datetime"] = pd.to_datetime(df["lpep_dropoff_datetime"])
    print(df.head(2))
    print(f"columns: {df.dtypes}")
    print(f"rows: {len(df)}")
    return df
```

The final unexpected value I received was fixed by adding a parameter to the function `etc_web_to_gcs` as it was not being utilized.

```python
@flow()
def etl_web_to_gcs(color: str, year: int, month: int) -> None:
    """The main ETL function"""
    # color = "yellow"
    # year = 2021
    # month = 1
    dataset_file = f"{color}_tripdata_{year}-{month:02}"
    dataset_url = f"https://github.com/DataTalksClub/nyc-tlc-data/releases/download/{color}/{dataset_file}.csv.gz"

    df = fetch(dataset_url)
    df_clean = clean(df)
    path = write_local(df_clean, color, dataset_file)
    write_gcs(path)


if __name__ == "__main__":
    etl_web_to_gcs(color="green", year=2020, month=1)
```

After the code has run successfully, you can verify the number of rows in the logs.

![](./images/prefect_flow_runs_success.PNG)

![](./images/prefect_logs.PNG)


## Question 2. Scheduling with Cron

Cron is a common scheduling specification for workflows. 

Using the flow in `etl_web_to_gcs.py`, create a deployment to run on the first of every month at 5am UTC. What’s the cron schedule for that?

- `0 5 1 * *` **
- `0 0 5 1 *`
- `5 * 1 0 *`
- `* * 5 1 0`

**Explanation:**


After creating the deployment, we set the schedule from the UI to run using a cron job as requested. The task is to run at 5:00 AM on the first day of each month in UTC.

![](./images/prefect_cron_job.PNG)


## Question 3. Loading data to BigQuery 

Using `etl_gcs_to_bq.py` as a starting point, modify the script for extracting data from GCS and loading it into BigQuery. This new script should not fill or remove rows with missing values. (The script is really just doing the E and L parts of ETL).

The main flow should print the total number of rows processed by the script. Set the flow decorator to log the print statement.

Parametrize the entrypoint flow to accept a list of months, a year, and a taxi color. 

Make any other necessary changes to the code for it to function as required.

Create a deployment for this flow to run in a local subprocess with local flow code storage (the defaults).

Make sure you have the parquet data files for Yellow taxi data for Feb. 2019 and March 2019 loaded in GCS. Run your deployment to append this data to your BiqQuery table. How many rows did your flow code process?

- 14,851,920 **
- 12,282,990
- 27,235,753
- 11,338,483

**Explanation**

I have already updated the `extract_from_gcs` function to accept a color as a string, a year as an integer, and a list of months(it can now accept multiple numbers of months). Additionally, I have edited the mechanism to retrieve the path, so it will return multiple paths (list of paths) equal to the number of months included in the parameters.

```python
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
```

For the `write_bq` function, I updated the project_id to my project_id in GCP and changed the destination table in BigQuery.

```python
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
```

The function `etl_gcs_to_bq` retrieves trip data from a GCS bucket by calling the `extract_from_gcs` function, and obtains a list of Path objects. Using a list comprehension, the function applies the transform function to each Path object, resulting in a list of DataFrames. The list of DataFrames is then combined into a single large DataFrame, `combined_df`, using `pd.concat`. The number of rows in the `combined_df` is printed, and the `combined_df` is written to BigQuery by calling the write_bq function.

```python
@flow(log_prints=True)
def etl_gcs_to_bq(color: str, year: int, months: list[int]):
    """Main ETL flow to load data into Big Query"""

    paths = extract_from_gcs(color, year, months)
    df = [transform(path) for path in paths]
    combined_df = pd.concat(df, axis=0, ignore_index=True)
    print(f"Total rows transformed into big query : {len(combined_df)}")
    write_bq(combined_df)
```

The total number of rows processed by the flow code is 14,851,920

![](./images/prefect_logs_gcs_to_bq_count.PNG)



## Question 4. Github Storage Block

Using the `web_to_gcs` script from the videos as a guide, you want to store your flow code in a GitHub repository for collaboration with your team. Prefect can look in the GitHub repo to find your flow code and read it. Create a GitHub storage block from the UI or in Python code and use that in your Deployment instead of storing your flow code locally or baking your flow code into a Docker image. 

Note that you will have to push your code to GitHub, Prefect will not push it for you.

Run your deployment in a local subprocess (the default if you don’t specify an infrastructure). Use the Green taxi data for the month of November 2020.

How many rows were processed by the script?

- 88,019
- 192,297
- 88,605 **
- 190,225

**Explanation**

![](./images/prefect_logs_web_to_gcs_no4.PNG)



## Question 5. Email or Slack notifications

Q5. It’s often helpful to be notified when something with your dataflow doesn’t work as planned. Choose one of the options below for creating email or slack notifications.

The hosted Prefect Cloud lets you avoid running your own server and has Automations that allow you to get notifications when certain events occur or don’t occur. 

Create a free forever Prefect Cloud account at app.prefect.cloud and connect your workspace to it following the steps in the UI when you sign up. 

Set up an Automation that will send yourself an email when a flow run completes. Run the deployment used in Q4 for the Green taxi data for April 2019. Check your email to see the notification.

Alternatively, use a Prefect Cloud Automation or a self-hosted Orion server Notification to get notifications in a Slack workspace via an incoming webhook. 

Join my temporary Slack workspace with [this link](https://join.slack.com/t/temp-notify/shared_invite/zt-1odklt4wh-hH~b89HN8MjMrPGEaOlxIw). 400 people can use this link and it expires in 90 days. 

In the Prefect Cloud UI create an [Automation](https://docs.prefect.io/ui/automations) or in the Prefect Orion UI create a [Notification](https://docs.prefect.io/ui/notifications/) to send a Slack message when a flow run enters a Completed state. Here is the Webhook URL to use: https://hooks.slack.com/services/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

Test the functionality.

Alternatively, you can grab the webhook URL from your own Slack workspace and Slack App that you create. 


How many rows were processed by the script?

- `125,268`
- `377,922`
- `728,390`
- `514,392` **

**Explanation**:

After creating a Prefect Cloud account at app.prefect.cloud, set up a workspace and generate API keys to access it from your local machine. Before that, create another profile locally to easily separate it from other configurations. You can check the list of configurations here. After creating a new profile, configure it to set the `PREFECT_API_KEY` and `PREFECT_API_URL` and use them to log in.

Upon successful login via the CLI, recreate the blocks (which can also be done via the UI) and deployments as in the local deployment before. I also created an email block that contains a list of emails to be used later to send notifications about the flow. In Prefect Cloud, there is a menu named Automations that is not present in local / open source version, and you can use it to set up notifications to be sent via email after a flow run is successful or completed.

The flow processed a total of 514,392 rows of data.

Here is an image of the email that was sent after the flow was completed.

![](./images/prefect_email_notif.PNG)


## Question 6. Secrets

Prefect Secret blocks provide secure, encrypted storage in the database and obfuscation in the UI. Create a secret block in the UI that stores a fake 10-digit password to connect to a third-party service. Once you’ve created your block in the UI, how many characters are shown as asterisks (*) on the next page of the UI?

- 5
- 6
- 8
- 10 **

**Explanation**:

![](./images/prefect_secrets.PNG)
