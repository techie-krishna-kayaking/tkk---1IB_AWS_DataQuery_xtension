# %%
# Notebook-style example for VS Code Python/Jupyter extension.
# Open this file and run cells, or copy to a real .ipynb notebook.

from src.config import get_aws_sso_login_cmd, get_aws_ssm_commands, get_selected_redshift_env

print("Default Redshift env:", get_selected_redshift_env())
print("Run manually in terminal for login:")
print(get_aws_sso_login_cmd())
print("\nStored SSM commands (run manually in terminal):")
for env_key, cmd in get_aws_ssm_commands().items():
    print(f"- {env_key}: {cmd}")

# %%
import pandas as pd
from src.redshift_client import run_redshift_query

df_redshift = run_redshift_query("select current_date as run_date")
df_redshift

# %%
from src.s3_client import read_s3_file

# Replace with your real path.
# df_s3 = read_s3_file("s3://your-bucket/path/file.parquet", limit=20)
# df_s3

# %%
from src.s3_client import query_s3_path

# Replace with your real path and optional SQL.
# df_s3_sql = query_s3_path(
#     "s3://your-bucket/path/file.parquet",
#     sql="select * from read_parquet('s3://your-bucket/path/file.parquet') limit 20"
# )
# df_s3_sql
