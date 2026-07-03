<div align="center">

<img src="https://cdn.simpleicons.org/amazonaws/FF9900" alt="AWS" width="64" height="64" />
<img src="https://cdn.simpleicons.org/python/3776AB" alt="Python" width="64" height="64" />
<img src="https://cdn.simpleicons.org/postgresql/336791" alt="PostgreSQL" width="64" height="64" />

# 1IB_AWS_DataQuery_xtension

### Fast, lightweight AWS data querying for Redshift and S3 in VS Code

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-SSO%20%2B%20SSM-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white)
![Redshift](https://img.shields.io/badge/Redshift-Query-8C4FFF?style=for-the-badge&logo=amazonredshift&logoColor=white)
![S3](https://img.shields.io/badge/S3-Data%20Preview-569A31?style=for-the-badge&logo=amazons3&logoColor=white)
![DuckDB](https://img.shields.io/badge/DuckDB-SQL%20on%20Files-FFF000?style=for-the-badge&logo=duckdb&logoColor=black)

</div>

## What This Project Does

This project is intentionally simple and terminal-first:
- Stores AWS login and tunnel command strings in `.env` and YAML
- Runs AWS SSO and SSM commands manually (or step-by-step from YAML)
- Queries Redshift and S3 with small Python CLI scripts
- Returns clean pandas DataFrames for scripts and notebooks

## Feature Highlights

- Config-driven Redshift connection by environment (`REDSHIFT_ENV`)
- One-by-one AWS command runner from `aws_commands.yaml`
- Direct Redshift SQL execution from CLI
- S3 preview and S3 SQL querying (CSV/JSON/Parquet)
- Notebook support with ready-to-run `.ipynb` example

## 5-Minute Quickstart

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

## Project Layout

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

## First-Time Setup

1. Open this folder in VS Code.
2. Create a virtual environment and activate it.

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies.

```bash
pip install -r requirements.txt
```

4. Create local config files.

```bash
cp .env.example .env
cp aws_commands.yaml.example aws_commands.yaml
```

5. Fill `.env` values for your environment.

Required Redshift keys:
- `REDSHIFT_HOST_<ENV>`
- `REDSHIFT_PORT_<ENV>`
- `REDSHIFT_DB_<ENV>`
- `REDSHIFT_USER_<ENV>`
- `REDSHIFT_PASSWORD_<ENV>`
- `REDSHIFT_SCHEMA_<ENV>`

6. Set default environment in `.env`.

```dotenv
REDSHIFT_ENV=data_analyst_dev
```

## AWS Login And Tunnel Flow

Run in this order:
1. AWS SSO login
2. SSM tunnel command
3. Data query script

Manual SSO example:

```bash
aws sso login --sso-session infoblox
```

Manual SSM tunnel example:

```bash
aws ssm --profile data-analyst-dev --region us-east-1 start-session --target i-0e8761941fc57c652 --document-name AWS-StartPortForwardingSession --parameters portNumber=54391,localPortNumber=54391
```

Optional tunnel check:

```bash
nc -zv localhost 54391
```

## AWS Command Runner (YAML)

List commands:

```bash
python scripts/run_aws_commands.py --file aws_commands.yaml
```

Run one command:

```bash
python scripts/run_aws_commands.py --file aws_commands.yaml --name sso_login
```

Run all commands in order:

```bash
python scripts/run_aws_commands.py --file aws_commands.yaml --all
```

Run all without confirmation:

```bash
python scripts/run_aws_commands.py --file aws_commands.yaml --all --yes
```

Dry run preview:

```bash
python scripts/run_aws_commands.py --file aws_commands.yaml --all --dry-run
```

## Query Redshift

```bash
python scripts/run_redshift_query.py --env data_analyst_dev --sql "select current_date"
```

With CSV export:

```bash
python scripts/run_redshift_query.py --env data_analyst_dev --sql "select * from your_table limit 100" --csv output.csv
```

If `--env` is omitted, `REDSHIFT_ENV` from `.env` is used.

## Query S3

Preview file:

```bash
python scripts/run_s3_query.py --path s3://your-bucket/path/file.parquet --preview --limit 20
```

Query with DuckDB SQL:

```bash
python scripts/run_s3_query.py --path s3://your-bucket/path/file.parquet --sql "select * from read_parquet('s3://your-bucket/path/file.parquet') limit 20"
```

Export S3 output to CSV:

```bash
python scripts/run_s3_query.py --path s3://your-bucket/path/file.parquet --preview --csv s3_preview.csv
```

## Notebook Usage

- Python cell notebook-style script: [examples/notebook_example.py](examples/notebook_example.py)
- Real Jupyter notebook: [examples/data_query_notebook.ipynb](examples/data_query_notebook.ipynb)

## Environment Variables

AWS command storage:
- `AWS_SSO_LOGIN_CMD`
- `AWS_SSM_CMD_DATA_ANALYST_DEV`
- `AWS_SSM_CMD_DATA_QA_DEV`
- `AWS_SSM_CMD_DATA_ANALYST_PREPROD`

Redshift selector:
- `REDSHIFT_ENV`

Redshift values:
- `REDSHIFT_HOST_<ENV>`
- `REDSHIFT_PORT_<ENV>`
- `REDSHIFT_DB_<ENV>`
- `REDSHIFT_USER_<ENV>`
- `REDSHIFT_PASSWORD_<ENV>`
- `REDSHIFT_SCHEMA_<ENV>`

S3 defaults:
- `AWS_REGION`
- `AWS_PROFILE`
- `S3_DEFAULT_BUCKET`
- `S3_DEFAULT_PREFIX`
- `DEFAULT_ROW_LIMIT`

## Troubleshooting

`.env` missing keys:
- Symptom: config errors for `REDSHIFT_*`
- Fix: copy `.env.example` to `.env` and fill all keys

Redshift connection refused:
- Symptom: localhost port connection failure
- Fix: ensure SSM tunnel is running and port matches `REDSHIFT_PORT_<ENV>`

AWS login expired:
- Symptom: S3/SSM auth errors
- Fix: run `aws sso login --sso-session infoblox`

Module import error:
- Symptom: `ModuleNotFoundError`
- Fix: activate `.venv` and run `pip install -r requirements.txt`

Unsupported S3 format:
- Symptom: preview/query errors for file type
- Fix: use CSV, JSON, or Parquet inputs

## Quick Health Check

```bash
python scripts/run_redshift_query.py --sql "select current_date"
python scripts/run_s3_query.py --path s3://your-bucket/path/file.parquet --preview --limit 5
```

## Developer

<div align="left">

<img src="https://raw.githubusercontent.com/simple-icons/simple-icons/develop/icons/github.svg" alt="GitHub" width="18" height="18" /> Krishna K  
<img src="https://raw.githubusercontent.com/simple-icons/simple-icons/develop/icons/gmail.svg" alt="Email" width="18" height="18" /> kkrishna@infoblox.com

</div>
