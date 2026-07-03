from src.redshift_client import run_redshift_query

# Uses REDSHIFT_ENV from .env unless env_name is provided.
# Example override: run_redshift_query("select current_date", env_name="data_analyst_dev")
df = run_redshift_query("select current_date as run_date")

print(df)
