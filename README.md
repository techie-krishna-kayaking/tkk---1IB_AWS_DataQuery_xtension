# 1IB_AWS_DataQuery_xtension

Simple Python-first AWS data query workflow for VS Code.

No VS Code extension is required for this workflow.

This project is intentionally lightweight:
- keep AWS login and tunnel commands in .env
- run AWS commands manually in terminal
- run SQL/S3 queries from Python scripts or notebook-style cells
- get results as pandas DataFrames or printed tables

## Features

- Environment-driven Redshift config from .env
- Manual SSO and SSM command storage in .env
- Redshift query helpers in Python
- Run SQL text from terminal
- S3 list/preview/query helpers (CSV/JSON/Parquet)
- DuckDB support for SQL over S3 paths
- Example Python and notebook-style files

## 5-minute quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
cp aws_commands.yaml.example aws_commands.yaml
python scripts/run_aws_commands.py --file aws_commands.yaml --name sso_login
python scripts/run_aws_commands.py --file aws_commands.yaml --name ssm_data_analyst_dev
python scripts/run_redshift_query.py --env data_analyst_dev --sql "select current_date"
```

## Project structure

```text
1IB_AWS_DataQuery_xtension/
  .env.example
  requirements.txt
  README.md
  scripts/
    run_redshift_query.py
    run_s3_query.py
    run_aws_commands.py
  src/
    __init__.py
    config.py
    redshift_client.py
    s3_client.py
  aws_commands.yaml.example
  examples/
    query_example.py
    notebook_example.py
    data_query_notebook.ipynb
```

## Step-by-step setup (first time)

1. Open the project folder in VS Code.

2. Create and activate virtual environment.

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies.

```bash
pip install -r requirements.txt
```

4. Create .env from template.

```bash
cp .env.example .env
```

5. Edit .env with your real values.
Required values are per environment:
- REDSHIFT_HOST_<ENV>
- REDSHIFT_PORT_<ENV>
- REDSHIFT_DB_<ENV>
- REDSHIFT_USER_<ENV>
- REDSHIFT_PASSWORD_<ENV>
- REDSHIFT_SCHEMA_<ENV>

6. Set default query environment in .env.

```dotenv
REDSHIFT_ENV=data_analyst_dev
```

7. Create AWS command YAML file.

```bash
cp aws_commands.yaml.example aws_commands.yaml
```

Edit aws_commands.yaml with the exact AWS commands your team uses.

## Manual AWS flow (required)

Important:
- .env only stores command strings.
- .env never executes commands automatically.
- You must run login and tunnel commands manually in terminal.

1. Login with AWS SSO.

```bash
aws sso login --sso-session infoblox
```

2. Start the required tunnel for your environment.
Use the command string from .env, for example:

```bash
aws ssm --profile data-analyst-dev --region us-east-1 start-session --target i-0e8761941fc57c652 --document-name AWS-StartPortForwardingSession --parameters portNumber=54391,localPortNumber=54391
```

Keep this tunnel terminal open while querying.

3. Verify local tunnel port is open (optional but recommended).

```bash
nc -zv localhost 54391
```

## Run AWS commands from YAML (one-by-one)

This helper runs saved AWS commands sequentially with confirmation.

Recommended order for a fresh session:
1. `sso_login`
2. one `ssm_*` command for the environment you want

List available commands:

```bash
python scripts/run_aws_commands.py --file aws_commands.yaml
```

Run one command by name:

```bash
python scripts/run_aws_commands.py --file aws_commands.yaml --name sso_login
```

Run all commands in order (asks confirmation for each):

```bash
python scripts/run_aws_commands.py --file aws_commands.yaml --all
```

Run all without confirmation:

```bash
python scripts/run_aws_commands.py --file aws_commands.yaml --all --yes
```

Preview commands without executing:

```bash
python scripts/run_aws_commands.py --file aws_commands.yaml --all --dry-run
```

## Daily usage workflow

1. Activate virtual environment.

```bash
source .venv/bin/activate
```

2. Ensure AWS login is active.

```bash
aws sso login --sso-session infoblox
```

3. Start SSM tunnel for your target environment.

4. Run queries using one of the methods below.

5. Keep the SSM tunnel terminal running while you execute queries.

## Run Redshift SQL text

```bash
python scripts/run_redshift_query.py --env data_analyst_dev --sql "select current_date"
```

Optional CSV export:

```bash
python scripts/run_redshift_query.py --env data_analyst_dev --sql "select * from your_table limit 100" --csv output.csv
```

If --env is omitted, REDSHIFT_ENV from .env is used.

## S3 data preview/query

Preview file directly:

```bash
python scripts/run_s3_query.py --path s3://your-bucket/path/file.parquet --preview --limit 20
```

Query with DuckDB SQL:

```bash
python scripts/run_s3_query.py --path s3://your-bucket/path/file.parquet --sql "select * from read_parquet('s3://your-bucket/path/file.parquet') limit 20"
```

Save S3 output to CSV:

```bash
python scripts/run_s3_query.py --path s3://your-bucket/path/file.parquet --preview --csv s3_preview.csv
```

## Use as Python module

Example Redshift query in Python:

```python
from src.redshift_client import run_redshift_query

df = run_redshift_query("select current_date as run_date", env_name="data_analyst_dev")
print(df)
```

Example S3 usage in Python:

```python
from src.s3_client import read_s3_file, query_s3_path

df_preview = read_s3_file("s3://your-bucket/path/file.parquet", limit=20)
df_sql = query_s3_path(
    "s3://your-bucket/path/file.parquet",
    sql="select * from read_parquet('s3://your-bucket/path/file.parquet') limit 20"
)
```

## Notebook-style usage in VS Code

Open [examples/notebook_example.py](examples/notebook_example.py) and run # %% cells with the Python/Jupyter extension.

For a real Jupyter notebook, open [examples/data_query_notebook.ipynb](examples/data_query_notebook.ipynb). It includes direct Redshift and S3 query cells.

## Environment variable reference

### AWS command storage

- AWS_SSO_LOGIN_CMD
- AWS_SSM_CMD_DATA_ANALYST_DEV
- AWS_SSM_CMD_DATA_QA_DEV
- AWS_SSM_CMD_DATA_ANALYST_PREPROD

### Redshift default selector

- REDSHIFT_ENV

### Redshift per environment

- REDSHIFT_HOST_<ENV>
- REDSHIFT_PORT_<ENV>
- REDSHIFT_DB_<ENV>
- REDSHIFT_USER_<ENV>
- REDSHIFT_PASSWORD_<ENV>
- REDSHIFT_SCHEMA_<ENV>

### S3 defaults

- AWS_REGION
- AWS_PROFILE
- S3_DEFAULT_BUCKET
- S3_DEFAULT_PREFIX
- DEFAULT_ROW_LIMIT

## Troubleshooting

### .env not found or missing keys
- Symptom: config errors for REDSHIFT_* variables
- Fix: copy .env.example to .env and fill values carefully

### Redshift connection refused
- Symptom: localhost port connection failure
- Fix: ensure SSM tunnel is running and localPortNumber matches REDSHIFT_PORT_<ENV>

### AWS login expired
- Symptom: permission/auth errors for S3 or SSM
- Fix: rerun aws sso login --sso-session infoblox

### Query fails due to permissions
- Symptom: Redshift or S3 access denied
- Fix: verify AWS profile permissions and target resources

### Missing package error
- Symptom: ModuleNotFoundError
- Fix: activate .venv and run pip install -r requirements.txt

### Unsupported S3 format
- Symptom: read_s3_file/query error for file type
- Fix: use CSV, JSON, or Parquet paths

## Quick test commands

```bash
python scripts/run_redshift_query.py --sql "select current_date"
python scripts/run_s3_query.py --path s3://your-bucket/path/file.parquet --preview --limit 5
```

## Team onboarding checklist

1. Clone or open this folder in VS Code.
2. Create `.venv` and install dependencies.
3. Copy `.env.example` to `.env` and fill values.
4. Copy `aws_commands.yaml.example` to `aws_commands.yaml` and adjust command strings.
5. Run SSO login command.
6. Run one SSM tunnel command for your chosen environment.
7. Run `scripts/run_redshift_query.py`.
