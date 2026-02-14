
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
        'fecha': pd.to_datetime(['2023-01-01', '2023-12-31']),
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
    assert stats['validation']['history_months'] > 0
    
    # Numeric Stats
    assert stats['numeric']['unidades']['mean'] == 550.0
    assert stats['numeric']['unidades']['min'] == 100.0
    
    # Zero Variance Detection
    assert 'constante' in stats['zero_variance']
    
    # Sentinel Value Detection
    sentinels = [x for x in stats['sentinel_values'] if x['sentinel'] == 999]
    assert len(sentinels) == 1

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
    assert not result['missing_columns']
    assert not result['type_mismatches']

def test_check_financial_health_happy_path(loader):
    """
    Happy Path: Valid financial data should pass strict rules.
    """
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
    assert not result['violations']

# --- SAD PATH TESTS (FAILURE SCENARIOS) ---

def test_sync_table_empty_or_failure(loader):
    """
    Sad Path: Supabase returns no data or fails.
    Should handle elegantly without crashing and return empty DataFrame.
    """
    # Mocking supabase response to be empty
    mock_response = MagicMock()
    mock_response.data = []
    
    # We need to mock the chain: table().select().order().range().execute()
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
        'fecha': ['not-a-date'], # Type mismatch
        # Missing 'unidades', 'precio'
        'extra_col': [1] # Extra column
    })
    result = loader.validate_data_contract(df, 'ventas_diarias')
    
    assert result['status'] == 'FAIL'
    assert 'unidades' in result['missing_columns']
    assert 'precio' in result['missing_columns']
    assert 'extra_col' in result['extra_columns']
    
    # Note: 'fecha' check might vary depending on if pandas inferred object or not, 
    # but the contract expects datetime.
    # If the df has object, and contract wants datetime, it flags a mismatch.
    assert any("expected datetime" in msg for msg in result['type_mismatches'])

def test_check_financial_health_violations(loader):
    """
    Sad Path: Financial rules are violated (Rule 2.1 and Rule 2.7).
    """
    df = pd.DataFrame({
        'total_unidades_entregadas': [100], # SHOULD BE 150
        'unidades_precio_normal': [100],
        'unidades_promo_pagadas': [25], 
        'unidades_promo_bonificadas': [25],
        'costo_unitario': [-10.0] # Rule 2.7 violation (negative cost)
    })
    
    result = loader.check_financial_health(df, 'ventas_diarias')
    
    assert result['status'] == 'FAIL'
    # Rule 2.1: Sum parts = 150, Total = 100. Diff = -50.
    assert 'rule_2_1_units_sum' in result['violations']
    # Rule 2.7: Negative values
    assert 'rule_2_7_negatives' in result['violations']

def test_run_orchestration_empty_data(loader, caplog):
    """
    Sad Path: Running the full orchestration when tables are empty.
    Should log warnings but not crash.
    """
    # Mock download to return empty
    with patch.object(loader, 'download_data', return_value=pd.DataFrame()):
        loader.run()
    
    # Verify warning was logged
    assert "Table ventas_diarias is empty after sync." in caplog.text

