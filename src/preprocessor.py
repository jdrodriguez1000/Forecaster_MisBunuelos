
import pandas as pd
import numpy as np
import yaml
from pathlib import Path
import os
from datetime import datetime
import platform
import json

class Preprocessor:
    """
    Handles the preprocessing pipeline: loading, cleaning, validation, imputation,
    and aggregation of raw data.
    """

    def __init__(self, config: dict):
        """
        Initialize the Preprocessor with configuration.

        Args:
            config (dict): The configuration dictionary.
        """
        self.config = config
        self.base_dir = Path(os.getcwd())
        self.raw_data_path = self.base_dir / "data" / "01_raw"
        self.cleansed_data_path = self.base_dir / "data" / "02_cleansed"
        self.artifacts_path = self.base_dir / "outputs" / "reports" / "phase_02_preprocessing"
        
        # Ensure output directories exist
        self.cleansed_data_path.mkdir(parents=True, exist_ok=True)
        self.artifacts_path.mkdir(parents=True, exist_ok=True)

        self.dataframes = {}
        self.stats_cleaning = {"duplicates": {}, "filtered": {}}
        self.sentinel_stats = {}
        self.reindex_stats = {}
        self.imputed_sales_count = 0
        self.file_map = {
            "ventas": "ventas_diarias",
            "marketing": "redes_sociales",
            "promo": "promocion_diaria",
            "macro": "macro_economia"
        }
        self.files = {
            "ventas": self.raw_data_path / "ventas_diarias.parquet",
            "marketing": self.raw_data_path / "redes_sociales.parquet",
            "promo": self.raw_data_path / "promocion_diaria.parquet",
            "macro": self.raw_data_path / "macro_economia.parquet"
        }


    def run(self):
        """
        Executes the full preprocessing pipeline.
        """
        print("Starting Preprocessing Pipeline...")
        self._load_data()
        self._validate_contract()
        self._standardize_names()
        self._enforce_schema()
        self._clean_rows()
        self._handle_sentinels()
        self._ensure_temporal_completeness()
        self._impute_business_logic()
        self._recalculate_financials()
        self._aggregate_monthly()
        df_master = self._unify_sources()
        df_master = self._impute_post_merge(df_master)
        self._export_and_report(df_master)
        print("Preprocessing Pipeline Completed.")

    def _load_data(self):
        """Loads raw data from parquet files."""
        print("Loading raw data...")
        for key, path in self.files.items():
            if path.exists():
                df = pd.read_parquet(path)
                self.dataframes[key] = df
                print(f"  - {key}: {df.shape}")
            else:
                raise FileNotFoundError(f"File not found: {path}")

    def _validate_contract(self):
        """Validates that loaded dataframes have the expected columns."""
        print("Validating Data Contracts...")
        data_contract = self.config.get("data_contract", {})

        for key, df in self.dataframes.items():
            config_name = self.file_map.get(key)
            expected_cols = list(data_contract.get(config_name, {}).keys())
            
            missing_cols = [col for col in expected_cols if col not in df.columns]
            
            if missing_cols:
                error_msg = f"CRITICAL ERROR in {key}: Missing columns {missing_cols}"
                print(error_msg)
                raise RuntimeError(error_msg)
            else:
                print(f"  - {key}: Contract Validation OK")

    def _standardize_names(self):
        """Renames columns based on configuration and converts to snake_case."""
        rename_map = self.config.get("preprocessing", {}).get("rename_map") or {}
        print(f"Applying rename_map: {rename_map}")

        for key, df in self.dataframes.items():
            df.rename(columns=rename_map, inplace=True)
            df.columns = [col.lower().replace(" ", "_") for col in df.columns]
            self.dataframes[key] = df
            
        print("Names standardized.")

    def _enforce_schema(self):
        """Selects only expected columns and logs removed ones."""
        print("Applying Schema Enforcement...")
        columns_removed_log = {}
        data_contract = self.config.get("data_contract", {})
        rename_map = self.config.get("preprocessing", {}).get("rename_map") or {}

        for key, df in self.dataframes.items():
            config_name = self.file_map.get(key)
            original_expected_cols = list(data_contract.get(config_name, {}).keys())
            
            final_expected_cols = []
            for col in original_expected_cols:
                new_name = rename_map.get(col, col).lower().replace(" ", "_")
                final_expected_cols.append(new_name)
            
            cols_to_keep = [col for col in df.columns if col in final_expected_cols]
            removed = [col for col in df.columns if col not in final_expected_cols]
            
            if removed:
                columns_removed_log[key] = removed
            
            self.dataframes[key] = df[cols_to_keep].copy()

        print("Columns removed:", columns_removed_log)

    def _clean_rows(self):
        """Removes duplicates and filters data by date."""
        print("Cleaning Rows...")
        filters = self.config.get("preprocessing", {}).get("filters", {})
        min_date = pd.to_datetime(filters.get("min_date", "2018-01-01"))

        for key, df in self.dataframes.items():
            initial_rows = len(df)
            
            # 1. Exact Deduplication
            df = df.drop_duplicates()
            
            # 2. Temporal Deduplication (Keep Last)
            if "fecha" in df.columns:
                df = df.copy()
                df["fecha"] = pd.to_datetime(df["fecha"])
                df = df.sort_values("fecha")
                duplicates_date = df.duplicated(subset=["fecha"], keep="last")
                df = df[~duplicates_date]
            
            rows_after_dedup = len(df)
            self.stats_cleaning["duplicates"][key] = initial_rows - rows_after_dedup
            
            # 3. Date Filtering
            if "fecha" in df.columns:
                df = df[df["fecha"] >= min_date].copy()
                self.stats_cleaning["filtered"][key] = rows_after_dedup - len(df)
            
            self.dataframes[key] = df
            
        print("Cleaning Statistics:", self.stats_cleaning)

    def _handle_sentinels(self):
        """Replaces sentinel values with NaN."""
        print("Handling Sentinel Values...")
        sentinel_values = self.config.get("quality", {}).get("sentinel_values", {})
        numeric_sentinels = sentinel_values.get("numeric", [])
        text_sentinels = sentinel_values.get("text", [])

        for key, df in self.dataframes.items():
            count_replaced = 0
            for col in df.columns:
                is_confianza = (key == "macro" and col == "confianza_consumidor")
                
                if pd.api.types.is_numeric_dtype(df[col]):
                    for val in numeric_sentinels:
                        if is_confianza and val == -1:
                            continue
                        
                        mask = (df[col] == val)
                        if mask.any():
                            count_replaced += mask.sum()
                            df.loc[mask, col] = np.nan
                            
                elif pd.api.types.is_string_dtype(df[col]):
                     for val in text_sentinels:
                        mask = (df[col] == val)
                        if mask.any():
                            count_replaced += mask.sum()
                            df.loc[mask, col] = np.nan
            
            self.sentinel_stats[key] = int(count_replaced)
            self.dataframes[key] = df
            
        print("Sentinels replaced:", self.sentinel_stats)

    def _ensure_temporal_completeness(self):
        """Reindexes dataframes to ensure temporal completeness."""
        print("Ensuring Temporal Completeness...")
        filters = self.config.get("preprocessing", {}).get("filters", {})
        min_date = pd.to_datetime(filters.get("min_date", "2018-01-01"))
        all_max_dates = [df["fecha"].max() for df in self.dataframes.values() if "fecha" in df.columns and not df.empty]
        global_max_date = max(all_max_dates) if all_max_dates else datetime.now()

        freq_map = self.config.get("preprocessing", {}).get("data_frequency", {})

        for key, df in self.dataframes.items():
            if "fecha" in df.columns and not df.empty:
                config_key = self.file_map.get(key)
                freq = freq_map.get(config_key, "D")
                
                print(f"  - Reindexing {key} with frequency: {freq}")
                
                full_idx = pd.date_range(start=min_date, end=global_max_date, freq=freq, name="fecha")
                
                df = df.set_index("fecha")
                df = df[~df.index.duplicated(keep='last')]
                
                original_len = len(df)
                df = df.reindex(full_idx)
                df.index.name = "fecha"
                df = df.reset_index()
                
                new_len = len(df)
                self.reindex_stats[key] = new_len - original_len
                self.dataframes[key] = df
        
        print("Rows added by reindexing:", self.reindex_stats)

    def _impute_business_logic(self):
        """Applies business-specific imputation logic."""
        print("Executing Business Imputation...")
        
        df_ventas = self.dataframes["ventas"]
        df_marketing = self.dataframes["marketing"]
        df_promo = self.dataframes["promo"]
        df_macro = self.dataframes["macro"]

        # --- Macro ---
        cols_num_macro = df_macro.select_dtypes(include=np.number).columns
        for col in cols_num_macro:
            if df_macro[col].isna().any():
                df_macro[col] = df_macro[col].fillna(
                    df_macro[col].rolling(window=60, min_periods=1).mean().shift(1)
                )
                df_macro[col] = df_macro[col].fillna(method='bfill')

        # --- Promos ---
        if "es_promo" in df_promo.columns:
            mask_null_promo = df_promo["es_promo"].isna()
            if mask_null_promo.any():
                meses_promo = [4, 5, 9, 10]
                months = df_promo["fecha"].dt.month
                df_promo.loc[mask_null_promo & months.isin(meses_promo), "es_promo"] = 1
                df_promo.loc[mask_null_promo & ~months.isin(meses_promo), "es_promo"] = 0

        # --- Marketing ---
        target_col_campana = "ciclo" if "ciclo" in df_marketing.columns else "campana"
        mask_camp_null = df_marketing[target_col_campana].isna()
        fb_val = df_marketing["inversion_facebook"].fillna(0)
        ig_val = df_marketing["inversion_instagram"].fillna(0)
        has_inv = (fb_val > 0) | (ig_val > 0)
        
        months = df_marketing["fecha"].dt.month
        mask_abr_may = months.isin([3, 4, 5])
        mask_sep_oct = months.isin([8, 9, 10])
        
        df_marketing.loc[mask_camp_null & has_inv & mask_abr_may, target_col_campana] = "Ciclo Abr-May"
        df_marketing.loc[mask_camp_null & has_inv & mask_sep_oct, target_col_campana] = "Ciclo Sep-Oct"
        df_marketing.loc[mask_camp_null & df_marketing[target_col_campana].isna(), target_col_campana] = "Sin Campaña"

        fechas = df_marketing["fecha"]
        rango1 = (((fechas.dt.month == 3) & (fechas.dt.day >= 15)) | (fechas.dt.month == 4) | ((fechas.dt.month == 5) & (fechas.dt.day <= 25)))
        rango2 = (((fechas.dt.month == 8) & (fechas.dt.day >= 15)) | (fechas.dt.month == 9) | ((fechas.dt.month == 10) & (fechas.dt.day <= 25)))
        rango_activo = rango1 | rango2
        
        for col in ["inversion_facebook", "inversion_instagram"]:
            if col in df_marketing.columns:
                mask_null_in_range = df_marketing[col].isna() & rango_activo
                if mask_null_in_range.any():
                    df_marketing[col] = df_marketing[col].interpolate(method='linear')
                
                mask_null_out_range = df_marketing[col].isna() & ~rango_activo
                if mask_null_out_range.any():
                    df_marketing.loc[mask_null_out_range, col] = 0
        
        target_col_marketing = "inversion_marketing_total" if "inversion_marketing_total" in df_marketing.columns else "inversion_total_diaria"
        if target_col_marketing in df_marketing.columns:
             # Recalculate total if possible, otherwise keep as is
             if "inversion_facebook" in df_marketing.columns and "inversion_instagram" in df_marketing.columns:
                df_marketing[target_col_marketing] = df_marketing["inversion_facebook"] + df_marketing["inversion_instagram"]
        
        # --- Ventas Diarias ---
        self.imputed_sales_mask = df_ventas["total_unidades_entregadas"].isna()
        
        for col in ["precio_unitario_full", "costo_unitario"]:
            if col in df_ventas.columns:
                df_ventas[col] = df_ventas[col].ffill().bfill()
        
        if "total_unidades_entregadas" in df_ventas.columns:
            s_total = df_ventas["total_unidades_entregadas"]
            s_interp = s_total.interpolate(method='linear')
            df_ventas["total_unidades_entregadas"] = s_interp.fillna(0)
            
        for col in ["unidades_promo_pagadas", "unidades_promo_bonificadas"]:
            if col in df_ventas.columns:
                df_ventas[col] = df_ventas[col].fillna(0)
                
        if "unidades_precio_normal" in df_ventas.columns:
            residual = df_ventas["total_unidades_entregadas"] - (df_ventas["unidades_promo_pagadas"] + df_ventas["unidades_promo_bonificadas"])
            df_ventas["unidades_precio_normal"] = df_ventas["unidades_precio_normal"].fillna(residual)
            df_ventas["unidades_precio_normal"] = df_ventas["unidades_precio_normal"].clip(lower=0)
            
        print("Business Imputation Completed.")

    def _recalculate_financials(self):
        """Recalculates financial fields if configured."""
        print("Recalculating Financials Selectively...")
        recalc_flag = self.config.get("preprocessing", {}).get("recalc_financials", False)
        df_ventas = self.dataframes["ventas"]

        if recalc_flag:
            if hasattr(self, 'imputed_sales_mask') and self.imputed_sales_mask.any():
                count = self.imputed_sales_mask.sum()
                print(f"Recalculating {count} imputed rows...")
                
                idx = df_ventas[self.imputed_sales_mask].index
                
                # Check for necessary columns before calc
                if {"total_unidades_entregadas", "costo_unitario", "unidades_precio_normal", "unidades_promo_pagadas", "precio_unitario_full"}.issubset(df_ventas.columns):
                    df_ventas.loc[idx, "costo_total"] = (
                        df_ventas.loc[idx, "total_unidades_entregadas"] * 
                        df_ventas.loc[idx, "costo_unitario"]
                    )
                    
                    unidades_pagas = (
                        df_ventas.loc[idx, "unidades_precio_normal"] + 
                        df_ventas.loc[idx, "unidades_promo_pagadas"]
                    )
                    
                    df_ventas.loc[idx, "ingresos_totales"] = (
                        unidades_pagas * df_ventas.loc[idx, "precio_unitario_full"]
                    )
                    
                    df_ventas.loc[idx, "utilidad"] = (
                        df_ventas.loc[idx, "ingresos_totales"] - 
                        df_ventas.loc[idx, "costo_total"]
                    )
                else:
                    print("Skipping recalculation due to missing columns.")
            else:
                print("No imputed rows to recalculate.")
        else:
            print("Financial recalculation disabled.")

    def _aggregate_monthly(self):
        """Aggregates dataframes to monthly frequency."""
        print("Aggregating Monthly (MS)...")
        agg_rules = self.config.get("preprocessing", {}).get("aggregation_rules", {})
        self.monthly_dfs = {}

        for key, df in self.dataframes.items():
            if "fecha" in df.columns:
                df = df.set_index("fecha")
            
            # Filter rules for current DF
            current_rules = {col: agg_rules[col] for col in df.columns if col in agg_rules}
            
            # Special rules
            if key == "promo" and "es_promo" in df.columns:
                current_rules["es_promo"] = "sum"
            elif key == "macro":
                current_rules = {col: "first" for col in df.columns}
            
            if current_rules:
                df_monthly = df.resample("MS").agg(current_rules)
            else:
                df_monthly = df.resample("MS").sum(numeric_only=True)
            
            if key == "promo" and "es_promo" in df_monthly.columns:
                df_monthly.rename(columns={"es_promo": "dias_en_promo"}, inplace=True)
                
            self.monthly_dfs[key] = df_monthly
            
        print("Aggregation completed.")

    def _unify_sources(self):
        """Merges all monthly dataframes into a master dataframe."""
        print("Merging Datasets...")
        df_master = self.monthly_dfs["ventas"].copy()

        for key in ["marketing", "promo", "macro"]:
            other_df = self.monthly_dfs[key]
            df_master = df_master.merge(other_df, left_index=True, right_index=True, how="left")
            
        print(f"Master Dataset Shape: {df_master.shape}")
        return df_master

    def _impute_post_merge(self, df_master):
        """Final imputation for any remaining structural gaps."""
        print("Final Imputation...")
        df_master = df_master.interpolate(method='linear').ffill().bfill()
        
        nulos = df_master.isna().sum().sum()
        if nulos > 0:
            print(f"WARNING: {nulos} null values remaining.")
        else:
            print("Dataset clean.")
        return df_master

    def _export_and_report(self, df_master):
        """Exports the master dataframe and generates a JSON report."""
        output_file = self.cleansed_data_path / "master_monthly.parquet"
        df_master.to_parquet(output_file)
        print(f"Saved to: {output_file}")
        
        final_shape = df_master.shape
        if isinstance(df_master.index, pd.DatetimeIndex):
            date_min = df_master.index.min().isoformat() if not df_master.empty else None
            date_max = df_master.index.max().isoformat() if not df_master.empty else None
        else:
            date_min = None
            date_max = None
            
        columns_list = df_master.columns.tolist()
        missing_values = int(df_master.isna().sum().sum())
        file_size_bytes = output_file.stat().st_size if output_file.exists() else 0
        
        report = {
            "phase": "Phase 2 - Preprocessing",
            "timestamp": datetime.now().isoformat(),
            "environment_info": {
                "platform": platform.system(),
                "python_version": platform.python_version(),
                "pandas_version": pd.__version__
            },
            "execution_context": {
                "description": "Exhaustive cleaning, business imputation, and monthly aggregation.",
                "validation_status": "SUCCESS" if missing_values == 0 else "WARNING_WITH_NULLS"
            },
            "data_quality_audit": {
                "cleaning_stats": {
                    "rows_filtered_logic": self.stats_cleaning.get("filtered", {}),
                    "duplicates_removed": self.stats_cleaning.get("duplicates", {}),
                    "sentinel_values_replaced": self.sentinel_stats,
                    "temporal_gaps_reindexed": self.reindex_stats
                },
                "imputation_metrics": {
                    "financial_records_recalculated": int(self.imputed_sales_mask.sum()) if hasattr(self, 'imputed_sales_mask') else 0,
                    "remaining_nulls_final": missing_values
                }
            },
            "output_artifact_details": {
                "file_name": output_file.name,
                "full_path": str(output_file.absolute()),
                "file_size_bytes": file_size_bytes,
                "shape": {
                    "rows": final_shape[0],
                    "columns": final_shape[1]
                },
                "temporal_coverage": {
                    "start_date": date_min,
                    "end_date": date_max,
                    "frequency": "MS (Month Start)",
                    "total_months": len(df_master)
                },
                "schema_columns": columns_list
            }
        }
        
        report_path = self.artifacts_path / "phase_02_preprocessing.json"
        with open(report_path, "w", encoding='utf-8') as f:
            json.dump(report, f, indent=4)
            
        print(f"Detailed Report generated at: {report_path}")

