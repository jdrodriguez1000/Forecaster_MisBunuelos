
import pytest
import pandas as pd
import numpy as np
import shutil
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch
from src.loader import DataLoader
from datetime import datetime

# --- Fixtures ---

@pytest.fixture
def mock_config():
    """Provides a controlled configuration for testing."""
    return {
        'paths': {
            'data': {'raw': 'tests/data/raw'},
            'prod': {'reports': 'tests/reports'}
        },
        'data': {
            'date_column': 'fecha',
            'source_tables': ['ventas_diarias'],
            'full_update': False
        },
        'quality': {
             'sentinel_values': {'numeric': [999]},
             'high_cardinality_threshold': 0.9,
             'zero_presence_threshold': 0.3
        },
        'preprocessing': {
            'data_frequency': {'ventas_diarias': 'D'}
        },
        'data_contract': {
            'ventas_diarias': {
                'fecha': 'datetime',
                'unidades': 'int',
                'precio': 'float'
            }
        },
        'financial_health': {
            'target_files': ['ventas_diarias']
        }
    }

@pytest.fixture
def loader(mock_config):
    """Initializes DataLoader with mocked Supabase client."""
    with patch('src.loader.get_supabase_client') as mock_client:
        loader = DataLoader(mock_config)
        loader.supabase = mock_client
        # Ensure directories exist
        loader.raw_data_path.mkdir(parents=True, exist_ok=True)
        loader.report_path.mkdir(parents=True, exist_ok=True)
        yield loader
    
    # Teardown: Clean up temporary test directories
    if Path('tests/data').exists():
        shutil.rmtree('tests/data')
    if Path('tests/reports').exists():
        shutil.rmtree('tests/reports')

# --- HAPPY PATH TESTS ---

def test_generate_statistics_happy_path(loader):
    """
    Happy Path: Verifies that statistics are generated correctly for a valid DataFrame.
    Checks numeric, temporal, and logic indicators.
    """
    df = pd.DataFrame({
        'fecha': pd.to_datetime(['2023-01-01', '2023-01-02']),
        'unidades': [100, 1000],
        'categoria': ['A', 'A'],
        'constante': [1, 1],
        'sentinel': [999, 10]
    })
    
    stats = loader.generate_statistics(df, 'ventas_diarias')
    
    # Validation & History
    assert 'validation' in stats
    # 2 dates < 36 months, so history_check SHOULD be FAIL based on rules, 
    # but the calculation itself (months_diff) should be correct.
    assert 'history_months' in stats['validation']
    
    # Numeric Stats (updated key)
    assert 'numerical_stats' in stats
    assert stats['numerical_stats']['unidades']['mean'] == 550.0
    assert stats['numerical_stats']['unidades']['min'] == 100.0
    
    # Zero Variance Detection (updated key)
    assert 'constante' in stats['zero_variance_columns']
    
    # Sentinel Value Detection
    sentinels = [x for x in stats['sentinel_values'] if x['column'] == 'sentinel']
    assert len(sentinels) == 1
    assert sentinels[0]['matches'][0]['value'] == 999

def test_validate_data_contract_happy_path(loader):
    """
    Happy Path: DataFrame matches the contract exactly.
    """
    df = pd.DataFrame({
        'fecha': pd.to_datetime(['2023-01-01']),
        'unidades': [100],
        'precio': [10.5]
    })
    result = loader.validate_data_contract(df, 'ventas_diarias')
    assert result['status'] == 'PASS'
    assert not result['details']

def test_check_financial_health_happy_path(loader):
    """
    Happy Path: Valid financial data should pass strict rules.
    """
    # Columns required for rules 2.1 - 2.6
    df = pd.DataFrame({
        'total_unidades_entregadas': [100],
        'unidades_precio_normal': [80],
        'unidades_promo_pagadas': [10],
        'unidades_promo_bonificadas': [10],
        'costo_unitario': [5.0],
        'precio_unitario_full': [10.0],
        'costo_total': [500.0], # 100 * 5
        'ingresos_totales': [900.0], # (80+10) * 10
        'utilidad': [400.0] # 900 - 500
    })
    result = loader.check_financial_health(df, 'ventas_diarias')
    assert result['status'] == 'PASS'
    for key, status in result['details'].items():
        assert status == 'PASS', f"{key} failed"

# --- SAD PATH TESTS (FAILURE SCENARIOS) ---

def test_sync_table_empty_or_failure(loader):
    """
    Sad Path: Supabase returns no data or fails.
    Should handle elegantly without crashing and return empty DataFrame.
    """
    # Mocking supabase response to be empty structure as expected by loader
    # The loader expects response.data to be list of dicts
    mock_response = MagicMock()
    mock_response.data = []
    
    # Mock the chain: table().select().order().range().execute()
    # Note: download_data implementation:
    # query = self.supabase.table(table_name).select("*").order(date_col).range(offset, offset + page_size - 1)
    # if greater_than: ...
    # response = query.execute()
    
    # We mock the return of execute()
    loader.supabase.table.return_value \
        .select.return_value \
        .order.return_value \
        .range.return_value \
        .execute.return_value = mock_response

    df = loader.download_data('ventas_diarias', 'fecha')
    assert df.empty
    assert isinstance(df, pd.DataFrame)

def test_validate_data_contract_broken_schema(loader):
    """
    Sad Path: DataFrame is missing columns and has type mismatches.
    """
    df = pd.DataFrame({
        'fecha': ['not-a-date'], # Type mismatch (object vs datetime)
        # Missing 'unidades', 'precio'
        'extra_col': [1] # Extra column
    })
    result = loader.validate_data_contract(df, 'ventas_diarias')
    
    assert result['status'] == 'FAIL'
    
    # Check details text
    details_str = str(result['details'])
    assert "Missing columns" in details_str
    assert "'unidades'" in details_str or "unidades" in details_str
    assert "Type mismatches" in details_str
    assert "fecha" in details_str

def test_check_financial_health_violations(loader):
    """
    Sad Path: Financial rules are violated (Rule 2.1 and Rule 2.7).
    """
    df = pd.DataFrame({
        'total_unidades_entregadas': [100.0], # Should be 150
        'unidades_precio_normal': [100.0],
        'unidades_promo_pagadas': [25.0], 
        'unidades_promo_bonificadas': [25.0],
        'costo_unitario': [-10.0], # Rule 2.7 violation (negative cost)
        # Add other cols to satisfy "all(cols)" checks if needed, 
        # but the rules check for existence first.
        # To fail Rule 2.1, we need all its cols.
        # To fail Rule 2.7, we need numeric cols with negative values.
        'precio_unitario_full': [10.0],
        'ingresos_totales': [1000.0]
    })
    
    result = loader.check_financial_health(df, 'ventas_diarias')
    
    assert result['status'] == 'FAIL'
    
    # Rule 2.1: Sum parts = 150, Total = 100. Diff = -50.
    assert "FAIL" in result['details']['rule_2_1_units_integrity']
    
    # Rule 2.7: Negative values
    assert "FAIL" in result['details']['rule_2_7_non_negative']

def test_run_orchestration_empty_data(loader, caplog):
    """
    Sad Path: Running the full orchestration when tables are empty.
    Should log warnings but not crash.
    """
    # Mock sync_table to return empty df
    with patch.object(loader, 'sync_table', return_value=pd.DataFrame()):
        with caplog.at_level(logging.WARNING):
             loader.run()
    
    # Verify warning was logged
    assert "Table ventas_diarias is empty after sync." in caplog.text
