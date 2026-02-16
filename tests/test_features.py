import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import os
from src.features import FeatureEngineer

@pytest.fixture
def mock_config():
    return {
        'project': {
            'random_state': 42,
            'target_column': 'total_unidades_entregadas'
        },
        'paths': {
            'data': {
                'cleansed': 'data/02_cleansed/',
                'features': 'data/03_features/'
            }
        },
        'feature_engineering': {
            'cyclical_columns': ['month', 'quarter', 'semester'],
            'marketing_lags': [
                {'column': 'inversion_total', 'lag': 1, 'fill_value': 0}
            ]
        },
        'business_events': {
            'primas': {'months': [6, 12]},
            'pandemic': {
                'start_date': '2020-04-01',
                'end_date': '2021-12-31'
            }
        }
    }

@pytest.fixture
def sample_df():
    dates = pd.date_range(start='2020-01-01', end='2022-12-01', freq='MS')
    df = pd.DataFrame(index=dates)
    df['total_unidades_entregadas'] = np.random.randint(100, 1000, size=len(dates))
    df['inversion_total'] = np.random.randint(1000, 5000, size=len(dates))
    return df

def test_cyclical_features(mock_config, sample_df):
    engineer = FeatureEngineer(mock_config)
    df = engineer.add_cyclical_features(sample_df.copy())
    
    assert 'month_sin' in df.columns
    assert 'month_cos' in df.columns
    assert 'quarter_sin' in df.columns
    assert 'semester_sin' in df.columns
    
    # Check bounds
    assert df['month_sin'].max() <= 1.0
    assert df['month_sin'].min() >= -1.0

def test_business_flags(mock_config, sample_df):
    engineer = FeatureEngineer(mock_config)
    df = engineer.add_business_flags(sample_df.copy())
    
    assert 'is_novenas' in df.columns
    assert 'is_primas' in df.columns
    assert 'is_pandemic' in df.columns
    
    # Test Novenas logic
    december_mask = df.index.month == 12
    assert (df.loc[december_mask, 'is_novenas'] == 1).all()
    assert (df.loc[~december_mask, 'is_novenas'] == 0).all()
    
    # Test Pandemic logic
    pandemic_mask = (df.index >= '2020-04-01') & (df.index <= '2021-12-31')
    assert (df.loc[pandemic_mask, 'is_pandemic'] == 1).all()
    assert (df.loc[~pandemic_mask, 'is_pandemic'] == 0).all()

def test_marketing_lags(mock_config, sample_df):
    engineer = FeatureEngineer(mock_config)
    df = engineer.add_marketing_lags(sample_df.copy())
    
    col_name = 'inversion_total_lag_1'
    assert col_name in df.columns
    
    # Check value at t=1 (should be value of inversion_total at t=0)
    assert df.iloc[1][col_name] == sample_df.iloc[0]['inversion_total']
    
    # Check fill value at t=0
    assert df.iloc[0][col_name] == 0

def test_report_generation(mock_config, sample_df, tmp_path):
    # Adjust paths to use tmp_path/data for the test
    test_config = mock_config.copy()
    test_config['paths']['data']['cleansed'] = str(tmp_path / "data/02_cleansed")
    test_config['paths']['data']['features'] = str(tmp_path / "data/03_features")
    
    # Reports directory
    report_dir = Path(os.getcwd()) / "outputs" / "reports" / "phase_04_feature_engineering"
    report_dir.mkdir(parents=True, exist_ok=True)
    
    engineer = FeatureEngineer(test_config)
    original_cols = sample_df.columns.tolist()
    
    # Add some features
    df = engineer.add_cyclical_features(sample_df.copy())
    
    engineer.generate_report(df, original_cols)
    
    report_file = report_dir / "phase_04_feature_engineering_prod.json"
    assert report_file.exists()
