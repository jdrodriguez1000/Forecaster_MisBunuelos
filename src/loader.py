import pandas as pd
import numpy as np
import yaml
import json
import logging
from pathlib import Path
from datetime import datetime, date
from typing import Dict, Any, List, Optional
import os

from src.connectors.supabase_connector import get_supabase_client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataLoader:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.supabase = get_supabase_client()
        self.raw_data_path = Path(config['paths']['data']['raw'])
        self.raw_data_path.mkdir(parents=True, exist_ok=True)
        self.report_path = Path(config['paths']['prod']['reports']) / "phase_01_discovery"
        self.report_path.mkdir(parents=True, exist_ok=True)
        self.table_analysis = {}
        self.download_details = []

    def get_remote_max_date(self, table_name: str, date_col: str) -> Optional[str]:
        try:
            response = self.supabase.table(table_name).select(date_col).order(date_col, desc=True).limit(1).execute()
            if response.data:
                return response.data[0][date_col]
        except Exception as e:
            logger.error(f"Error getting max date for {table_name}: {e}")
        return None

    def download_data(self, table_name: str, date_col: str, greater_than: Optional[str] = None) -> pd.DataFrame:
        all_data = []
        page_size = 1000
        offset = 0
        
        while True:
            query = self.supabase.table(table_name).select("*").order(date_col).range(offset, offset + page_size - 1)
            if greater_than:
                query = query.gt(date_col, greater_than)
            
            response = query.execute()
            data = response.data
            
            if not data:
                break
                
            all_data.extend(data)
            offset += page_size
            
            if len(data) < page_size:
                break
        
        return pd.DataFrame(all_data)

    def sync_table(self, table_name: str, date_col: str, full_update: bool) -> pd.DataFrame:
        local_file = self.raw_data_path / f"{table_name}.parquet"
        operation_status = "Up to Date"
        new_rows_count = 0
        
        local_df = pd.DataFrame()
        max_local = None
        
        if local_file.exists() and not full_update:
            try:
                local_df = pd.read_parquet(local_file)
                if not local_df.empty and date_col in local_df.columns:
                    max_local = local_df[date_col].max()
                    # Ensure max_local is a string for comparison if needed, or keep as timestamp
                    if isinstance(max_local, (pd.Timestamp, date, datetime)):
                        max_local = max_local.strftime('%Y-%m-%d')
            except Exception as e:
                logger.warning(f"Error reading local file {local_file}: {e}. Triggering full update.")
                max_local = None

        final_df = local_df
        
        if full_update or max_local is None:
            logger.info(f"Full update for {table_name}")
            df_remote = self.download_data(table_name, date_col)
            if not df_remote.empty:
                final_df = df_remote
                operation_status = "Full Download"
                new_rows_count = len(df_remote)
        else:
            # Check remote max
            max_remote = self.get_remote_max_date(table_name, date_col)
            # Standardize format for comparison
            if max_remote:
                 # Check if remote > local
                 # Simple string comparison usually works for ISO dates, but be careful
                 if max_remote > max_local:
                     logger.info(f"Incremental update for {table_name} from {max_local}")
                     df_new = self.download_data(table_name, date_col, greater_than=max_local)
                     if not df_new.empty:
                         final_df = pd.concat([local_df, df_new]).drop_duplicates(subset=[date_col]) # simplistic dedup
                         operation_status = "Incremental Update"
                         new_rows_count = len(df_new)
        
        if not final_df.empty:
            # Enforce datetime type for the date column
            if date_col in final_df.columns:
                 final_df[date_col] = pd.to_datetime(final_df[date_col])
            
            final_df.to_parquet(local_file)
            
        self.download_details.append({
            "table": table_name,
            "status": operation_status,
            "new_rows": new_rows_count,
            "total_rows": len(final_df),
            "timestamp": datetime.now().isoformat()
        })
        
        return final_df

    def validate_data_contract(self, df: pd.DataFrame, table_name: str) -> Dict[str, Any]:
        contract = self.config.get('data_contract', {}).get(table_name, {})
        if not contract:
            return {"status": "SKIPPED", "reason": "No contract defined"}
            
        missing_cols = []
        extra_cols = []
        type_mismatches = []
        
        # Check columns
        expected_cols = set(contract.keys())
        actual_cols = set(df.columns)
        
        missing_cols = list(expected_cols - actual_cols)
        extra_cols = list(actual_cols - expected_cols)
        
        # Check types (simplified)
        for col, expected_type in contract.items():
            if col in df.columns:
                actual_dtype = df[col].dtype
                # Map string types to pandas dtypes
                if expected_type == 'int':
                    if not pd.api.types.is_integer_dtype(actual_dtype):
                         type_mismatches.append(f"{col}: expected int, got {actual_dtype}")
                elif expected_type == 'float':
                    if not pd.api.types.is_float_dtype(actual_dtype):
                         type_mismatches.append(f"{col}: expected float, got {actual_dtype}")
                elif expected_type == 'datetime':
                    if not pd.api.types.is_datetime64_any_dtype(actual_dtype):
                         type_mismatches.append(f"{col}: expected datetime, got {actual_dtype}")
        
        status = "PASS"
        if missing_cols or type_mismatches:
            status = "FAIL"
        elif extra_cols:
            status = "WARNING"
            
        return {
            "status": status,
            "missing_columns": missing_cols,
            "extra_columns": extra_cols,
            "type_mismatches": type_mismatches
        }

    def check_financial_health(self, df: pd.DataFrame, table_name: str) -> Dict[str, Any]:
        rules = self.config.get('financial_health', {}).get('target_files', [])
        if table_name not in rules:
             return {"status": "SKIPPED"}
             
        violations = {}
        
        # Rule 2.1: total_unidades_entregadas == sum of parts
        if all(c in df.columns for c in ['total_unidades_entregadas', 'unidades_precio_normal', 'unidades_promo_pagadas', 'unidades_promo_bonificadas']):
            calculated_total = df['unidades_precio_normal'] + df['unidades_promo_pagadas'] + df['unidades_promo_bonificadas']
            diff = df['total_unidades_entregadas'] - calculated_total
            failed_rows = df[diff.abs() > 0.001]
            if not failed_rows.empty:
                violations['rule_2_1_units_sum'] = len(failed_rows)

        # Rule 2.2: unidades_promo_pagadas == unidades_promo_bonificadas (assuming strict 2x1 logic if that's the rule, or just equality check)
        # Based on config/previous context, rule 2.2 said: unidades_promo_pagadas == unidades_promo_bonificadas
        if 'unidades_promo_pagadas' in df.columns and 'unidades_promo_bonificadas' in df.columns:
             diff = df['unidades_promo_pagadas'] - df['unidades_promo_bonificadas']
             failed = df[diff.abs() > 0.001]
             if not failed.empty:
                 violations['rule_2_2_promo_equality'] = len(failed)

        # Rule 2.3: precio_unitario_full >= costo_unitario
        if 'precio_unitario_full' in df.columns and 'costo_unitario' in df.columns:
            failed = df[df['precio_unitario_full'] < df['costo_unitario']]
            if not failed.empty:
                violations['rule_2_3_price_vs_cost'] = len(failed)

        # Rule 2.4: utilidad = ingresos - costo_total
        if all(c in df.columns for c in ['utilidad', 'ingresos_totales', 'costo_total']):
             calc_util = df['ingresos_totales'] - df['costo_total']
             diff = df['utilidad'] - calc_util
             failed = df[diff.abs() > 0.01] # Currency tolerance
             if not failed.empty:
                 violations['rule_2_4_utility_calc'] = len(failed)
        
        # Rule 2.5: ingresos_totales check
        if all(c in df.columns for c in ['ingresos_totales', 'unidades_precio_normal', 'unidades_promo_pagadas', 'precio_unitario_full']):
            calc_rev = (df['unidades_precio_normal'] + df['unidades_promo_pagadas']) * df['precio_unitario_full']
            diff = df['ingresos_totales'] - calc_rev
            failed = df[diff.abs() > 0.01]
            if not failed.empty:
                violations['rule_2_5_revenue_calc'] = len(failed)

        # Rule 2.6: costo_total check
        if all(c in df.columns for c in ['costo_total', 'total_unidades_entregadas', 'costo_unitario']):
             calc_cost = df['total_unidades_entregadas'] * df['costo_unitario']
             diff = df['costo_total'] - calc_cost
             failed = df[diff.abs() > 0.01]
             if not failed.empty:
                 violations['rule_2_6_cost_calc'] = len(failed)
        
        # Rule 2.7: No negatives
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        negatives = {}
        for col in numeric_cols:
            count = (df[col] < 0).sum()
            if count > 0:
                negatives[col] = int(count)
        if negatives:
            violations['rule_2_7_negatives'] = negatives

        status = "PASS" if not violations else "FAIL"
        return {"status": status, "violations": violations}

    def generate_statistics(self, df: pd.DataFrame, table_name: str) -> Dict[str, Any]:
        stats = {}
        
        # --- 0. Basic Validation & History Check ---
        date_col_name = self.config.get('data', {}).get('date_column', 'fecha')
        val_info = {
            "columns": list(df.columns),
            "rows": len(df)
        }
        
        # History Check (Specific to ventas_diarias)
        if table_name == "ventas_diarias":
            if date_col_name in df.columns:
                min_date = df[date_col_name].min()
                max_date = df[date_col_name].max()
                if pd.notnull(min_date) and pd.notnull(max_date):
                    # Simple robust assumption: dates are timestamps
                    months_diff = (max_date - min_date) / pd.Timedelta(days=30)
                    val_info["history_months"] = round(float(months_diff), 2)
                    
                    if months_diff < 36:
                        val_info["history_check"] = "FAIL"
                    else:
                        val_info["history_check"] = "PASS"
                else:
                    val_info["history_check"] = "FAIL - Dates Null"
            else:
                val_info["history_check"] = "FAIL - No Date Col"
        
        stats["validation"] = val_info

        # --- 1. Numeric Statistics ---
        numeric_stats = {}
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            col_stats = {
                "mean": float(df[col].mean()),
                "median": float(df[col].median()),
                "std": float(df[col].std()),
                "min": float(df[col].min()),
                "max": float(df[col].max()),
                "25%": float(df[col].quantile(0.25)),
                "50%": float(df[col].quantile(0.50)),
                "75%": float(df[col].quantile(0.75))
            }
            numeric_stats[col] = col_stats
        stats["numeric"] = numeric_stats

        # --- 2. Temporal Analysis ---
        temporal_stats = {}
        if date_col_name in df.columns and pd.api.types.is_datetime64_any_dtype(df[date_col_name]):
             col = date_col_name
             ts_stats = {
                 "min_date": str(df[col].min()),
                 "max_date": str(df[col].max()),
                 "duplicates": int(df[col].duplicated().sum())
             }
             # Gaps check (daily)
             if table_name in ["ventas_diarias", "macro_economia"]: # assuming daily
                 full_range = pd.date_range(start=df[col].min(), end=df[col].max(), freq='D')
                 missing = full_range.difference(df[col])
                 ts_stats["gaps_count"] = len(missing)
             
             temporal_stats[col] = ts_stats
        stats["temporal"] = temporal_stats

        # --- 3. Categorical Analysis ---
        categorical_stats = {}
        cat_cols = df.select_dtypes(include=['object', 'category']).columns
        for col in cat_cols:
            counts = df[col].value_counts(normalize=True).head(5).to_dict()
            categorical_stats[col] = {
                "unique_count": int(df[col].nunique()),
                "top_categories_pct": {k: float(v) for k, v in counts.items()}
            }
        stats["categorical"] = categorical_stats

        # --- 4. Outliers (IQR) ---
        outliers_stats = {}
        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            count = len(df[(df[col] < lower_bound) | (df[col] > upper_bound)])
            if count > 0:
                outliers_stats[col] = {
                    "count": count,
                    "lower_bound": float(lower_bound),
                    "upper_bound": float(upper_bound)
                }
        stats["outliers"] = outliers_stats

        # --- 5. Zero Variance ---
        zero_variance = []
        for col in df.columns:
            if df[col].nunique() <= 1:
                zero_variance.append(col)
        stats["zero_variance"] = zero_variance
        
        # --- 6. High Cardinality ---
        high_cardinality = []
        threshold = self.config.get('quality', {}).get('high_cardinality_threshold', 0.9)
        for col in cat_cols:
            ratio = df[col].nunique() / len(df) if len(df) > 0 else 0
            if ratio > threshold:
                high_cardinality.append(col)
        stats["high_cardinality"] = high_cardinality

        # --- 7. Zero Presence ---
        zero_presence = {}
        zero_thresh = self.config.get('quality', {}).get('zero_presence_threshold', 0.3)
        for col in numeric_cols:
            zero_count = (df[col] == 0).sum()
            ratio = zero_count / len(df) if len(df) > 0 else 0
            if ratio > zero_thresh:
                zero_presence[col] = float(ratio)
        stats["zero_presence"] = zero_presence

        # --- 8. Duplicates ---
        stats["duplicates"] = int(df.duplicated().sum())

        # --- 9. Null Analysis ---
        null_analysis = {}
        for col in df.columns:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                null_analysis[col] = {
                    "count": int(null_count),
                    "percentage": float(null_count / len(df))
                }
        stats["null_analysis"] = null_analysis

        # --- 10. Sentinel Values ---
        sentinel_report = []
        sentinels = self.config.get('quality', {}).get('sentinel_values', {})
        
        # Check numeric
        num_sentinels = sentinels.get('numeric', [])
        for col in numeric_cols:
            for val in num_sentinels:
                count = (df[col] == val).sum()
                if count > 0:
                    sentinel_report.append({"column": col, "sentinel": val, "count": int(count)})
        
        # Check categorical
        cat_sentinels = sentinels.get('categorical', [])
        for col in cat_cols:
             for val in cat_sentinels:
                count = (df[col] == val).sum()
                if count > 0:
                    sentinel_report.append({"column": col, "sentinel": val, "count": int(count)})

        stats["sentinel_values"] = sentinel_report

        return stats

    def run(self):
        tables = self.config['data']['source_tables']
        full_update = self.config['data']['full_update']
        date_col = self.config['data']['date_column']
        
        for table in tables:
            logger.info(f"Processing table: {table}")
            df = self.sync_table(table, date_col, full_update)
            
            if not df.empty:
                # 1. Generate Statistics
                stats = self.generate_statistics(df, table)
                
                # 2. Validate Data Contract
                contract_validation = self.validate_data_contract(df, table)
                stats['data_contract'] = contract_validation
                
                # 3. Check Financial Health
                financial_health = self.check_financial_health(df, table)
                stats['financial_health'] = financial_health
                
                self.table_analysis[table] = stats
            else:
                logger.warning(f"Table {table} is empty after sync.")
        
        # Generate Report
        report = {
            "phase": "Phase 1 - Data Discovery",
            "timestamp": datetime.now().isoformat(),
            "description": "Production Data Discovery Execution",
            "download_details": self.download_details,
            "data_analysis": self.table_analysis
        }
        
        report_file = self.report_path / "phase_01_discovery.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=4, ensure_ascii=False)
            
        logger.info(f"Report generated at {report_file}")
