
import pytest
import pandas as pd
import numpy as np
import yaml
from pathlib import Path
from src.preprocessor import Preprocessor
from src.utils import load_config
from datetime import datetime
from unittest.mock import patch

# --- Fixtures ---

@pytest.fixture
def mock_config():
    """Provides a minimal config for testing."""
    return {
        "data_contract": {
            "ventas_diarias": {
                "fecha": "datetime",
                "total_unidades_entregadas": "int"
            },
            "redes_sociales": {
                "fecha": "datetime",
                "inversion_facebook": "float"
            },
            "promocion_diaria": {
                "fecha": "datetime",
                "es_promo": "int"
            },
            "macro_economia": {
                "fecha": "datetime",
                "ipc_mensual": "float"
            }
        },
        "preprocessing": {
            "rename_map": {},
            "data_frequency": {
                "ventas_diarias": "D",
                "redes_sociales": "D",
                "promocion_diaria": "D",
                "macro_economia": "MS"
            },
            "filters": {
                "min_date": "2023-01-01"
            },
            "recalc_financials": False,
            "aggregation_rules": {
                "total_unidades_entregadas": "sum",
                "inversion_facebook": "sum",
                "es_promo": "sum",
                "ipc_mensual": "first"
            }
        },
        "quality": {
            "sentinel_values": {
                "numeric": [-1, 999],
                "text": ["NULL"]
            }
        }
    }

@pytest.fixture
def mock_dataframes():
    """Creates mock dataframes for testing."""
    dates_d = pd.date_range("2023-01-01", "2023-01-10", freq="D")
    
    df_ventas = pd.DataFrame({
        "fecha": dates_d,
        "total_unidades_entregadas": [10, 20, np.nan, 40, 50, 60, 70, 80, 90, 100],
        "unidades_precio_normal": [5, 10, 15, 20, 25, 30, 35, 40, 45, 50],
         # Add required columns for recalc logic checks even if not strictly used in basic tests
        "unidades_promo_pagadas": [5, 10, np.nan, 20, 25, 30, 35, 40, 45, 50],
        "unidades_promo_bonificadas": [0] * 10
    })
    
    df_marketing = pd.DataFrame({
        "fecha": dates_d,
        "inversion_facebook": [100.0] * 10,
        "inversion_instagram": [50.0] * 10,
        "ciclo": ["C1"] * 10
    })
    
    df_promo = pd.DataFrame({
        "fecha": dates_d,
        "es_promo": [0, 0, 1, 1, 0, 0, 1, 1, 0, 0]
    })
    
    # Macro is monthly usually
    dates_m = pd.date_range("2023-01-01", "2023-02-01", freq="MS")
    df_macro = pd.DataFrame({
        "fecha": dates_m,
        "ipc_mensual": [5.0, 5.1],
        "confianza_consumidor": [50, 52] # Add extra col to test preservation
    })
    
    return {
        "ventas": df_ventas,
        "marketing": df_marketing,
        "promo": df_promo,
        "macro": df_macro
    }

class TestPreprocessor:
    
    def test_init(self, mock_config):
        """Test initialization of Preprocessor."""
        prep = Preprocessor(mock_config)
        assert prep.config == mock_config
        assert len(prep.file_map) > 0

    def test_clean_rows_dedup(self, mock_config):
        """Test deduplication logic."""
        prep = Preprocessor(mock_config)
        
        # Create DF with duplicates
        df = pd.DataFrame({
            "fecha": ["2023-01-01", "2023-01-01", "2023-01-02"],
            "val": [1, 1, 2]
        })
        prep.dataframes = {"test": df}
        
        prep._clean_rows()
        
        cleaned = prep.dataframes["test"]
        assert len(cleaned) == 2
        assert prep.stats_cleaning["duplicates"]["test"] == 1

    def test_sentinels(self, mock_config):
        """Test sentinel replacement."""
        prep = Preprocessor(mock_config)
        
        df = pd.DataFrame({
            "val": [10, -1, 999, 20],
            "text": ["A", "NULL", "B", "C"]
        })
        prep.dataframes = {"test": df}
        
        prep._handle_sentinels()
        
        res = prep.dataframes["test"]
        assert np.isnan(res.iloc[1, 0]) # -1
        assert np.isnan(res.iloc[2, 0]) # 999
        assert pd.isna(res.iloc[1, 1]) # NULL
        assert prep.sentinel_stats["test"] == 3

    def test_reindexing(self, mock_config):
        """Test temporal reindexing."""
        prep = Preprocessor(mock_config)
        
        # Gap in dates: 01, 03 (missing 02)
        df = pd.DataFrame({
            "fecha": pd.to_datetime(["2023-01-01", "2023-01-03"]),
            "val": [1, 3]
        })
        prep.dataframes = {"ventas": df} # Config says 'ventas' is 'D'
        
        # Override file_map just to be sure we match config keys
        prep.file_map = {"ventas": "ventas_diarias"} 
        
        prep._ensure_temporal_completeness()
        
        res = prep.dataframes["ventas"]
        # Should now have 01, 02, 03 (if max date allows)
        # But wait, max date calculation uses all DFs. If this is the only one...
        # 01 to 03 is 3 days.
        assert len(res) >= 3
        assert pd.Timestamp("2023-01-02") in res["fecha"].values
        assert prep.reindex_stats["ventas"] > 0

    def test_aggregation(self, mock_config, mock_dataframes):
        """Test monthly aggregation."""
        prep = Preprocessor(mock_config)
        prep.dataframes = mock_dataframes
        
        prep._aggregate_monthly()
        
        monthly = prep.monthly_dfs["ventas"]
        # 2023-01-01 to 2023-01-10 is all in Jan 2023. So 1 month result.
        assert len(monthly) == 1
        assert monthly.index.freqstr == "MS"
        assert monthly.index[0] == pd.Timestamp("2023-01-01")
        
        # Sum of 10, 20, 40...
        expected_sum = mock_dataframes["ventas"]["total_unidades_entregadas"].sum() 
        assert monthly["total_unidades_entregadas"].iloc[0] == expected_sum

    def test_full_imputation_flow(self, mock_config, mock_dataframes):
        """Test business imputation logic."""
        prep = Preprocessor(mock_config)
        prep.dataframes = mock_dataframes
        
        # Inject validation attributes usually set by full run
        prep.files = {} # so _load_data doesn't fail
        
        # Mock macro imputation needs rolling window, so extend data
        if "ipc_mensual" in prep.dataframes["macro"].columns:
             # Just simple check for sales imputation
             pass

        prep._impute_business_logic()
        
        # Sales nan was at index 2
        df_ventas = prep.dataframes["ventas"]
        assert not df_ventas["total_unidades_entregadas"].isna().any()
        # Should be interpolated between 20 and 40 -> 30
        assert df_ventas["total_unidades_entregadas"].iloc[2] == 30.0

    def test_anti_data_leakage(self, mock_config):
        """Test anti-data leakage functionality."""
        prep = Preprocessor(mock_config)
        
        # Scenario: Current date is 2023-05-15
        mock_now = datetime(2023, 5, 15)
        
        # 1. Data ends in current month (2023-05-01) -> Should drop last row
        dates_leak = pd.date_range("2023-01-01", "2023-05-01", freq="MS")
        df_leak = pd.DataFrame({"val": range(5)}, index=dates_leak)
        
        # 2. Data ends in previous month (2023-04-01) -> Should keep all
        dates_ok = pd.date_range("2023-01-01", "2023-04-01", freq="MS")
        df_ok = pd.DataFrame({"val": range(4)}, index=dates_ok)

        # Patch 'src.preprocessor.datetime'
        # Since 'from datetime import datetime' is used in src/preprocessor.py,
        # 'datetime' is a name in that namespace.
        with patch('src.preprocessor.datetime') as mock_dt:
            mock_dt.now.return_value = mock_now
            
            # Test 1: Leakage detected
            res_leak = prep._apply_anti_leakage_rule(df_leak.copy())
            assert len(res_leak) == 4
            assert res_leak.index.max() == pd.Timestamp("2023-04-01")
            
            # Test 2: No leakage
            res_ok = prep._apply_anti_leakage_rule(df_ok.copy())
            assert len(res_ok) == 4
            assert res_ok.index.max() == pd.Timestamp("2023-04-01")
