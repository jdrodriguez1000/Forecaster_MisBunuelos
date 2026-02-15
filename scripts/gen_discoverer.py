
import json
import os
from pathlib import Path

# Define the notebook structure
notebook_content = {
 "cells": [
  {
   "cell_type": "markdown",
   "id": "650e691c",
   "metadata": {},
   "source": [
    "# 1. Setup & Configuration"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "id": "083b156c",
   "metadata": {},
   "outputs": [],
   "source": [
    "import pandas as pd\n",
    "import yaml\n",
    "import numpy as np\n",
    "import json\n",
    "from pathlib import Path\n",
    "from datetime import datetime, date\n",
    "import os\n",
    "import sys\n",
    "\n",
    "# Add project root to path\n",
    "# Assuming notebook is running in standard directory structure: project/notebooks/\n",
    "project_root = Path('..').resolve()\n",
    "if str(project_root) not in sys.path:\n",
    "    sys.path.append(str(project_root))\n",
    "\n",
    "from src.connectors.supabase_connector import get_supabase_client\n",
    "\n",
    "# Load Configuration\n",
    "config_path = Path('../config.yaml')\n",
    "if not config_path.exists():\n",
    "    raise FileNotFoundError(\"config.yaml not found in parent directory\")\n",
    "\n",
    "with open(config_path, 'r') as f:\n",
    "    config = yaml.safe_load(f)\n",
    "\n",
    "# Define Paths\n",
    "RAW_DATA_PATH = Path('../data/01_raw')\n",
    "RAW_DATA_PATH.mkdir(parents=True, exist_ok=True)\n",
    "\n",
    "# Initialize Supabase Client\n",
    "supabase = get_supabase_client()\n",
    "\n",
    "print(\"Setup Complete. Config and Supabase Client Loaded.\")\n"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "73558e9c",
   "metadata": {},
   "source": [
    "# 2. Helper Functions (Data Loading & Sync)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "id": "0ab89db1",
   "metadata": {},
   "outputs": [],
   "source": [
    "def get_remote_max_date(table_name: str, date_col: str):\n",
    "    try:\n",
    "        response = supabase.table(table_name).select(date_col).order(date_col, desc=True).limit(1).execute()\n",
    "        if response.data:\n",
    "            return response.data[0][date_col]\n",
    "        return None\n",
    "    except Exception as e:\n",
    "        print(f\"Error getting max date for {table_name}: {e}\")\n",
    "        return None\n",
    "\n",
    "def download_data(table_name: str, date_col: str, greater_than=None):\n",
    "    all_data = []\n",
    "    page_size = 1000\n",
    "    offset = 0\n",
    "    \n",
    "    print(f\"Downloading {table_name}...\", end=\" \")\n",
    "    \n",
    "    query = supabase.table(table_name).select(\"*\").order(date_col)\n",
    "    \n",
    "    if greater_than:\n",
    "        query = query.gt(date_col, greater_than)\n",
    "        \n",
    "    while True:\n",
    "        response = query.range(offset, offset + page_size - 1).execute()\n",
    "        data = response.data\n",
    "        if not data:\n",
    "            break\n",
    "        all_data.extend(data)\n",
    "        offset += page_size\n",
    "        print(f\".\", end=\"\")\n",
    "        \n",
    "    print(f\" Done. Retrieved {len(all_data)} rows.\")\n",
    "    return pd.DataFrame(all_data)\n",
    "\n",
    "def sync_table(table_name: str, date_col: str, full_update: bool):\n",
    "    file_path = RAW_DATA_PATH / f\"{table_name}.parquet\"\n",
    "    \n",
    "    download_needed = False\n",
    "    start_date = None\n",
    "    existing_df = pd.DataFrame()\n",
    "\n",
    "    if not file_path.exists() or full_update:\n",
    "        download_needed = True\n",
    "        print(f\"[{table_name}] Full download required (File missing or full_update=True).\")\n",
    "    else:\n",
    "        try:\n",
    "            existing_df = pd.read_parquet(file_path)\n",
    "            if not existing_df.empty and date_col in existing_df.columns:\n",
    "                max_local = existing_df[date_col].max()\n",
    "                # Ensure max_local is a string for comparison if needed, or keep as is\n",
    "                if isinstance(max_local, (datetime, date)):\n",
    "                    max_local = max_local.isoformat()\n",
    "                \n",
    "                max_remote = get_remote_max_date(table_name, date_col)\n",
    "                \n",
    "                if max_remote and max_remote > str(max_local):\n",
    "                    download_needed = True\n",
    "                    start_date = max_local\n",
    "                    print(f\"[{table_name}] Incremental update required. Local: {max_local}, Remote: {max_remote}\")\n",
    "                else:\n",
    "                    print(f\"[{table_name}] Up to date.\")\n",
    "            else:\n",
    "                 download_needed = True\n",
    "                 print(f\"[{table_name}] Full download required (Empty file or missing date col).\")\n",
    "        except Exception as e:\n",
    "            print(f\"Error reading {file_path}: {e}\")\n",
    "            download_needed = True\n",
    "\n",
    "    if download_needed:\n",
    "        new_df = download_data(table_name, date_col, greater_than=start_date)\n",
    "        \n",
    "        if not new_df.empty:\n",
    "            if not existing_df.empty and start_date:\n",
    "                # Append\n",
    "                combined_df = pd.concat([existing_df, new_df]).drop_duplicates(subset=['id'], keep='last')\n",
    "                combined_df.to_parquet(file_path, index=False)\n",
    "                print(f\"[{table_name}] Updated. New total rows: {len(combined_df)}\")\n",
    "                return combined_df\n",
    "            else:\n",
    "                new_df.to_parquet(file_path, index=False)\n",
    "                print(f\"[{table_name}] Saved. Total rows: {len(new_df)}\")\n",
    "                return new_df\n",
    "        else:\n",
    "             print(f\"[{table_name}] No new data found.\")\n",
    "             return existing_df\n",
    "    \n",
    "    return existing_df\n"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "58edc562",
   "metadata": {},
   "source": [
    "# 3. Execute Pipeline"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "id": "09cc931d",
   "metadata": {},
   "outputs": [],
   "source": [
    "tables = config['data']['source_tables']\n",
    "date_column = config['data']['date_column']\n",
    "full_update = config['data']['full_update']\n",
    "\n",
    "TABLE_DATA = {}\n",
    "download_metadata = []\n",
    "\n",
    "for table in tables:\n",
    "    # Handle specific date columns if different per table, but config suggests one generic 'date_column'\n",
    "    # Checking if there's override logic in preprocessing config, but for discovery we stick to simple logic or manual override\n",
    "    # Config has 'date_column': 'fecha'\n",
    "    \n",
    "    df = sync_table(table, date_column, full_update)\n",
    "    TABLE_DATA[table] = df\n",
    "    \n",
    "    download_metadata.append({\n",
    "        \"table\": table, \n",
    "        \"rows\": len(df), \n",
    "        \"timestamp\": datetime.now().isoformat()\n",
    "    })\n"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "31de48e7",
   "metadata": {},
   "source": [
    "# 4. Sanity Check & History Validation"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "id": "db3ca998",
   "metadata": {},
   "outputs": [],
   "source": [
    "min_history = config['data']['min_history_months']\n",
    "\n",
    "for table, df in TABLE_DATA.items():\n",
    "    print(f\"--- {table} ---\")\n",
    "    print(df.info())\n",
    "    print(df.head())\n",
    "    \n",
    "    # Try generic date parsing for history check\n",
    "    if 'fecha' in df.columns:\n",
    "        temp_date = pd.to_datetime(df['fecha'], errors='coerce')\n",
    "        if not temp_date.isnull().all():\n",
    "            months = (temp_date.max() - temp_date.min()).days / 30\n",
    "            print(f\"History: {months:.1f} months\")\n",
    "            if table == 'ventas_diarias' and months < min_history:\n",
    "                print(\"WARNING: Insufficient history!\")\n"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "6e871c16",
   "metadata": {},
   "source": [
    "# 5. Statistical Analysis (Numerical)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "id": "ccbbbbe2",
   "metadata": {},
   "outputs": [],
   "source": [
    "TABLE_ANALYSIS = {}\n",
    "\n",
    "for table, df in TABLE_DATA.items():\n",
    "    TABLE_ANALYSIS[table] = {}\n",
    "    \n",
    "    print(f\"Analyzing {table}...\")\n",
    "    num_cols = df.select_dtypes(include=[np.number]).columns\n",
    "    stats = df[num_cols].describe(percentiles=[.25, .5, .75]).to_dict()\n",
    "    \n",
    "    TABLE_ANALYSIS[table]['numerical_stats'] = stats\n"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "4b5be718",
   "metadata": {},
   "source": [
    "# 6. Temporal Analysis"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "id": "a4acd7eb",
   "metadata": {},
   "outputs": [],
   "source": [
    "for table, df in TABLE_DATA.items():\n",
    "    TABLE_ANALYSIS[table]['temporal_stats'] = {}\n",
    "    \n",
    "    # Try to find date columns\n",
    "    date_cols = [col for col in df.columns if 'fecha' in col.lower() or 'date' in col.lower()]\n",
    "    \n",
    "    for col in date_cols:\n",
    "        try:\n",
    "            series = pd.to_datetime(df[col])\n",
    "            stats = {\n",
    "                'min': series.min().isoformat(),\n",
    "                'max': series.max().isoformat(),\n",
    "                'nulls': int(series.isnull().sum())\n",
    "            }\n",
    "            # Check for gaps if it's daily data\n",
    "            if table in ['ventas_diarias', 'redes_sociales']:\n",
    "                expected_range = pd.date_range(start=series.min(), end=series.max())\n",
    "                missing = set(expected_range.date) - set(series.dt.date)\n",
    "                stats['gaps_count'] = len(missing)\n",
    "                \n",
    "            TABLE_ANALYSIS[table]['temporal_stats'][col] = stats\n",
    "        except Exception as e:\n",
    "            print(f\"Error temporal analysis {table}.{col}: {e}\")\n"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "341c2862",
   "metadata": {},
   "source": [
    "# 7. Categorical Analysis"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "id": "8af8d85d",
   "metadata": {},
   "outputs": [],
   "source": [
    "for table, df in TABLE_DATA.items():\n",
    "    TABLE_ANALYSIS[table]['categorical_stats'] = {}\n",
    "    \n",
    "    cat_cols = df.select_dtypes(include=['object']).columns\n",
    "    for col in cat_cols:\n",
    "        if col not in ['fecha']: # Skip date if caught as object\n",
    "            counts = df[col].value_counts(normalize=True).to_dict()\n",
    "            TABLE_ANALYSIS[table]['categorical_stats'][col] = counts\n"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "c4533669",
   "metadata": {},
   "source": [
    "# 8. Outlier Detection"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "id": "75f7b0ee",
   "metadata": {},
   "outputs": [],
   "source": [
    "for table, df in TABLE_DATA.items():\n",
    "    TABLE_ANALYSIS[table]['outliers'] = {}\n",
    "    \n",
    "    num_cols = df.select_dtypes(include=[np.number]).columns\n",
    "    for col in num_cols:\n",
    "        if col == 'id': continue\n",
    "        \n",
    "        Q1 = df[col].quantile(0.25)\n",
    "        Q3 = df[col].quantile(0.75)\n",
    "        IQR = Q3 - Q1\n",
    "        lower_bound = Q1 - 1.5 * IQR\n",
    "        upper_bound = Q3 + 1.5 * IQR\n",
    "        \n",
    "        outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]\n",
    "        TABLE_ANALYSIS[table]['outliers'][col] = {\n",
    "            'count': len(outliers),\n",
    "            'lower_bound': lower_bound,\n",
    "            'upper_bound': upper_bound\n",
    "        }\n"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "bb9ab795",
   "metadata": {},
   "source": [
    "# 9. Zero Variance Check"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "id": "a6bbc113",
   "metadata": {},
   "outputs": [],
   "source": [
    "for table, df in TABLE_DATA.items():\n",
    "    zero_var = []\n",
    "    for col in df.columns:\n",
    "        if df[col].nunique() <= 1:\n",
    "            zero_var.append(col)\n",
    "    TABLE_ANALYSIS[table]['zero_variance'] = zero_var\n"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "86365aef",
   "metadata": {},
   "source": [
    "# 10. High Cardinality Check"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "id": "a819bf61",
   "metadata": {},
   "outputs": [],
   "source": [
    "threshold = config['quality'].get('high_cardinality_threshold', 0.9)\n",
    "\n",
    "for table, df in TABLE_DATA.items():\n",
    "    high_card = []\n",
    "    for col in df.columns:\n",
    "        ratio = df[col].nunique() / len(df)\n",
    "        if ratio > threshold:\n",
    "            high_card.append({'column': col, 'ratio': ratio})\n",
    "    TABLE_ANALYSIS[table]['high_cardinality'] = high_card\n"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "804c7fa1",
   "metadata": {},
   "source": [
    "# 11. Zero Presence Check"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "id": "b5345cf8",
   "metadata": {},
   "outputs": [],
   "source": [
    "threshold = config['quality'].get('zero_presence_threshold', 0.3)\n",
    "\n",
    "for table, df in TABLE_DATA.items():\n",
    "    high_zeros = []\n",
    "    num_cols = df.select_dtypes(include=[np.number]).columns\n",
    "    for col in num_cols:\n",
    "        zeros = (df[col] == 0).sum()\n",
    "        ratio = zeros / len(df)\n",
    "        if ratio > threshold:\n",
    "            high_zeros.append({'column': col, 'ratio': ratio, 'count': int(zeros)})\n",
    "    TABLE_ANALYSIS[table]['high_zeros'] = high_zeros\n"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "2e11249a",
   "metadata": {},
   "source": [
    "# 12. Duplicate Rows Check"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "id": "ea0d645b",
   "metadata": {},
   "outputs": [],
   "source": [
    "for table, df in TABLE_DATA.items():\n",
    "    dupes = df.duplicated().sum()\n",
    "    TABLE_ANALYSIS[table]['duplicate_rows'] = int(dupes)\n"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "83ed49c5",
   "metadata": {},
   "source": [
    "# 13. Null Analysis"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "id": "abb6152e",
   "metadata": {},
   "outputs": [],
   "source": [
    "for table, df in TABLE_DATA.items():\n",
    "    nulls = df.isnull().sum()\n",
    "    null_stats = nulls[nulls > 0].to_dict()\n",
    "    TABLE_ANALYSIS[table]['null_stats'] = null_stats\n"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "e81ecd30",
   "metadata": {},
   "source": [
    "# 14. Sentinel Values Check"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "id": "1c7a7d2c",
   "metadata": {},
   "outputs": [],
   "source": [
    "sentinels = config['quality']['sentinel_values']\n",
    "\n",
    "for table, df in TABLE_DATA.items():\n",
    "    sentinel_report = []\n",
    "    \n",
    "    # Numeric\n",
    "    num_cols = df.select_dtypes(include=[np.number]).columns\n",
    "    for col in num_cols:\n",
    "        for val in sentinels['numeric']:\n",
    "            count = (df[col] == val).sum()\n",
    "            if count > 0:\n",
    "                sentinel_report.append({'column': col, 'value': val, 'count': int(count)})\n",
    "                \n",
    "    # Categorical\n",
    "    cat_cols = df.select_dtypes(include=['object']).columns\n",
    "    for col in cat_cols:\n",
    "        for val in sentinels['categorical']:\n",
    "            count = (df[col] == val).sum()\n",
    "            if count > 0:\n",
    "                sentinel_report.append({'column': col, 'value': val, 'count': int(count)})\n",
    "                \n",
    "    TABLE_ANALYSIS[table]['sentinel_values'] = sentinel_report\n"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "8f64e231",
   "metadata": {},
   "source": [
    "# 15. Data Contract Validation"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "id": "3c8cee85",
   "metadata": {},
   "outputs": [],
   "source": [
    "contracts = config['data_contract']\n",
    "\n",
    "for table, df in TABLE_DATA.items():\n",
    "    report = {'status': 'PASS', 'issues': []}\n",
    "    \n",
    "    if table not in contracts:\n",
    "        continue\n",
    "        \n",
    "    expected_schema = contracts[table]\n",
    "    \n",
    "    # Check missing columns\n",
    "    missing = set(expected_schema.keys()) - set(df.columns)\n",
    "    if missing:\n",
    "        report['status'] = 'FAIL'\n",
    "        report['issues'].append(f\"Missing columns: {missing}\")\n",
    "        \n",
    "    # Check extra columns\n",
    "    extra = set(df.columns) - set(expected_schema.keys())\n",
    "    if extra:\n",
    "        report['issues'].append(f\"Extra columns: {extra}\")\n",
    "        \n",
    "    TABLE_ANALYSIS[table]['data_contract'] = report\n"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "caa4ee0e",
   "metadata": {},
   "source": [
    "# 16. Financial Health Validation"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "id": "d6aae482",
   "metadata": {},
   "outputs": [],
   "source": [
    "financial_targets = config['financial_health']['target_files']\n",
    "\n",
    "for table in financial_targets:\n",
    "    if table not in TABLE_DATA: continue\n",
    "    \n",
    "    df = TABLE_DATA[table].copy()\n",
    "    health_report = {}\n",
    "    \n",
    "    # Rule 2.1: Units Integrity\n",
    "    # total_unidades = normal + promo_pagadas + promo_bonificadas\n",
    "    calc_units = df['unidades_precio_normal'] + df['unidades_promo_pagadas'] + df['unidades_promo_bonificadas']\n",
    "    diff_units = df['total_unidades_entregadas'] - calc_units\n",
    "    health_report['rule_2_1_units_integrity'] = (diff_units.abs().sum() == 0)\n",
    "    \n",
    "    # Rule 2.2: Promo Equality\n",
    "    diff_promos = df['unidades_promo_pagadas'] - df['unidades_promo_bonificadas']\n",
    "    health_report['rule_2_2_promo_equality'] = (diff_promos.abs().sum() == 0)\n",
    "    \n",
    "    # Rule 2.3: Margin Integrity (Price >= Cost)\n",
    "    margin_check = (df['precio_unitario_full'] >= df['costo_unitario']).all()\n",
    "    health_report['rule_2_3_margin_integrity'] = bool(margin_check)\n",
    "    \n",
    "    # Rule 2.4: Utility Calc\n",
    "    # utilidad = ingresos - costo_total\n",
    "    calc_util = df['ingresos_totales'] - df['costo_total']\n",
    "    diff_util = df['utilidad'] - calc_util\n",
    "    health_report['rule_2_4_utility_calc'] = (diff_util.abs() < 1).all() # Float tolerance\n",
    "    \n",
    "    # Rule 2.5: Revenue Calc\n",
    "    # ingresos = (normal + pagadas) * precio_full\n",
    "    calc_rev = (df['unidades_precio_normal'] + df['unidades_promo_pagadas']) * df['precio_unitario_full']\n",
    "    diff_rev = df['ingresos_totales'] - calc_rev\n",
    "    health_report['rule_2_5_revenue_calc'] = (diff_rev.abs() < 1).all()\n",
    "    \n",
    "    # Rule 2.6: Cost Calc\n",
    "    # costo_total = total_unidades * costo_unitario\n",
    "    calc_cost = df['total_unidades_entregadas'] * df['costo_unitario']\n",
    "    diff_cost = df['costo_total'] - calc_cost\n",
    "    health_report['rule_2_6_cost_calc'] = (diff_cost.abs() < 1).all()\n",
    "    \n",
    "    # Rule 2.7: Non-negative\n",
    "    num_cols = df.select_dtypes(include=[np.number]).columns\n",
    "    negatives = (df[num_cols] < 0).any().any()\n",
    "    health_report['rule_2_7_non_negative'] = not negatives\n",
    "    \n",
    "    TABLE_ANALYSIS[table]['financial_health'] = health_report\n"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "7df5e6e5",
   "metadata": {},
   "source": [
    "# 17. Generate Final Report"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "id": "f3805acb",
   "metadata": {},
   "outputs": [],
   "source": [
    "output_path = Path('../experiments/phase_01_discovery/artifacts')\n",
    "output_path.mkdir(parents=True, exist_ok=True)\n",
    "\n",
    "final_report = {\n",
    "    \"phase\": \"Phase 1 - Data Discovery\",\n",
    "    \"timestamp\": datetime.now().isoformat(),\n",
    "    \"description\": \"Data Discovery Execution from Notebook\",\n",
    "    \"download_details\": download_metadata,\n",
    "    \"data_analysis\": TABLE_ANALYSIS\n",
    "}\n",
    "\n",
    "report_file = output_path / 'phase_01_discovery.json'\n",
    "with open(report_file, 'w') as f:\n",
    "    json.dump(final_report, f, indent=4, default=str)\n",
    "\n",
    "print(f\"Report generated at: {report_file}\")\n"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": ".venv",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.12.10"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}

nb_file_path = "notebooks/01_data_discovery.ipynb"

# Crear directorio si no existe
os.makedirs("notebooks", exist_ok=True)

# Escribir archivo
with open(nb_file_path, "w", encoding="utf-8") as f:
    json.dump(notebook_content, f, indent=4)

print(f"Notebook generated correctly at: {os.path.abspath(nb_file_path)}")
