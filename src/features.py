import pandas as pd
import numpy as np
import yaml
from pathlib import Path
import os
import logging
from datetime import datetime
import json
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib
# Use Agg backend for non-interactive plot generation
matplotlib.use('Agg')

class FeatureEngineer:
    """
    Class to handle the Feature Engineering phase (Phase 4).
    Generates cyclical features, business flags, and marketing lags.
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.base_dir = Path(os.getcwd())
        
        # Paths aligned with config.yaml structure
        data_paths = config.get('paths', {}).get('data', {})
        prod_paths = config.get('paths', {}).get('prod', {})
        
        self.input_path = self.base_dir / data_paths.get('cleansed', 'data/02_cleansed/') / "master_monthly.parquet"
        self.output_path = self.base_dir / data_paths.get('features', 'data/03_features/') / "master_features.parquet"
        
        # Output reports and figures to production directories
        self.artifacts_path = self.base_dir / prod_paths.get('reports', 'outputs/reports/') / "phase_04_feature_engineering"
        self.figures_path = self.base_dir / prod_paths.get('figures', 'outputs/figures/') / "phase_04_feature_engineering"
        
        # Ensure directories exist
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.artifacts_path.mkdir(parents=True, exist_ok=True)
        self.figures_path.mkdir(parents=True, exist_ok=True)

    def add_cyclical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Adds sine and cosine transformations for time-based features."""
        self.logger.info("Generating cyclical features...")
        fe_config = self.config.get('feature_engineering', {})
        cyclical_cols = fe_config.get('cyclical_columns', [])
        
        if 'month' in cyclical_cols:
            df['month_sin'] = np.sin(2 * np.pi * df.index.month / 12)
            df['month_cos'] = np.cos(2 * np.pi * df.index.month / 12)
        
        if 'quarter' in cyclical_cols:
            df['quarter_sin'] = np.sin(2 * np.pi * df.index.quarter / 4)
            df['quarter_cos'] = np.cos(2 * np.pi * df.index.quarter / 4)
            
        if 'semester' in cyclical_cols:
            semester = (df.index.month - 1) // 6 + 1
            df['semester_sin'] = np.sin(2 * np.pi * semester / 2)
            df['semester_cos'] = np.cos(2 * np.pi * semester / 2)
            
        return df

    def add_business_flags(self, df: pd.DataFrame) -> pd.DataFrame:
        """Adds binary flags for business events and context."""
        self.logger.info("Generating business flags...")
        biz_events = self.config.get('business_events', {})
        
        # Novenas (Diciembre)
        df['is_novenas'] = (df.index.month == 12).astype(int)
        
        # Primas (Junio y Diciembre)
        primas_months = biz_events.get('primas', {}).get('months', [6, 12])
        df['is_primas'] = (df.index.month.isin(primas_months)).astype(int)
        
        # Pandemia
        p_cfg = biz_events.get('pandemic', {})
        p_start = pd.to_datetime(p_cfg.get('start_date', '2020-04-01'))
        p_end = pd.to_datetime(p_cfg.get('end_date', '2021-12-31'))
        df['is_pandemic'] = ((df.index >= p_start) & (df.index <= p_end)).astype(int)
        
        return df

    def add_marketing_lags(self, df: pd.DataFrame) -> pd.DataFrame:
        """Adds lag features for marketing variables."""
        self.logger.info("Generating marketing lags...")
        fe_config = self.config.get('feature_engineering', {})
        mkt_lags = fe_config.get('marketing_lags', [])
        
        for cfg in mkt_lags:
            col = cfg['column']
            lag = cfg['lag']
            fill_val = cfg.get('fill_value', 0)
            
            if col in df.columns:
                new_col_name = f"{col}_lag_{lag}"
                df[new_col_name] = df[col].shift(lag).fillna(fill_val)
                self.logger.info(f"  - Created {new_col_name}")
            else:
                self.logger.warning(f"Marketing column {col} not found for lag.")
                
        return df

    def generate_report(self, df: pd.DataFrame, original_cols: list):
        """Generates a robust JSON report of the phase."""
        self.logger.info("Creating phase report...")
        new_cols = [c for c in df.columns if c not in original_cols]
        
        report = {
            "phase": "Phase 4 - Feature Engineering (Production)",
            "timestamp": datetime.now().isoformat(),
            "input_file": str(self.input_path.name),
            "output_file": str(self.output_path.name),
            "variables": {
                "original_columns": original_cols,
                "new_features": {col: str(df[col].dtype) for col in new_cols}
            },
            "summary": {
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "new_features_count": len(new_cols),
                "nulls_check": int(df.isnull().sum().sum()),
                "temporal_range": [df.index.min().isoformat(), df.index.max().isoformat()]
            },
            "data_preview": {
                "head_5": df.head(5).reset_index().astype(str).to_dict(orient='records'),
                "tail_5": df.tail(5).reset_index().astype(str).to_dict(orient='records')
            }
        }
        
        report_file = self.artifacts_path / "phase_04_feature_engineering_prod.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=4)
        self.logger.info(f"Report saved to {report_file}")

    def run(self):
        """Orchestrates the feature engineering pipeline."""
        self.logger.info("Starting Phase 4: Feature Engineering...")
        
        # Load data
        if not self.input_path.exists():
            raise FileNotFoundError(f"Cleansed data not found at: {self.input_path}")
        
        df = pd.read_parquet(self.input_path)
        original_cols = df.columns.tolist()
        
        # Apply engineering
        df = self.add_cyclical_features(df)
        df = self.add_business_flags(df)
        df = self.add_marketing_lags(df)
        
        # Generate Visualizations (Parity with Lab)
        self.generate_figures(df)
        
        # Final cleanup/validation
        nulls = df.isnull().sum().sum()
        if nulls > 0:
            self.logger.warning(f"Engineered dataset contains {nulls} nulls. Investigating...")
            
        # Persistence
        df.to_parquet(self.output_path)
        self.logger.info(f"Engineered data saved to {self.output_path}")
        
        # Reporting
        self.generate_report(df, original_cols)
        self.logger.info("Phase 4 completed successfully.")
        return df

    def generate_figures(self, df: pd.DataFrame):
        """Generates validation plots for the engineered features."""
        self.logger.info("Generating validation figures...")
        target_col = self.config.get('project', {}).get('target_column', 'total_unidades_entregadas')
        
        # Set style from config if available
        viz_style = self.config.get('visualization', {}).get('style', 'seaborn-v0_8-darkgrid')
        try:
            plt.style.use(viz_style)
        except:
            plt.style.use('ggplot')

        # 1. Validation of business events vs Target
        plt.figure(figsize=(15, 6))
        plt.plot(df.index, df[target_col], label='Ventas (Target)', color='blue', alpha=0.6)
        
        if 'is_novenas' in df.columns:
            plt.fill_between(df.index, 0, df[target_col].max(), 
                             where=df['is_novenas']==1, color='red', alpha=0.2, label='Novenas')
        if 'is_primas' in df.columns:
            plt.fill_between(df.index, 0, df[target_col].max(), 
                             where=df['is_primas']==1, color='green', alpha=0.1, label='Primas')
        
        plt.title("Validación Visual de Eventos de Negocio (Producción)")
        plt.legend()
        plt.savefig(self.figures_path / "01_validacion_eventos.png")
        plt.close()

        # 2. Cyclical representation
        if 'month_sin' in df.columns and 'month_cos' in df.columns:
            plt.figure(figsize=(6, 6))
            plt.scatter(df['month_sin'], df['month_cos'], c=df.index.month, cmap='twilight')
            plt.title("Representación Cíclica de los Meses (Seno/Coseno)")
            plt.colorbar(label='Mes')
            plt.savefig(self.figures_path / "02_ciclos_mensuales.png")
            plt.close()

        # 3. Correlation Heatmap
        new_cols = [c for c in df.columns if c not in [target_col] and (c.startswith('month_') or c.startswith('is_') or '_lag_' in c)]
        if new_cols:
            plt.figure(figsize=(12, 10))
            corr = df[new_cols + [target_col]].corr()
            sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f")
            plt.title("Correlación: Nuevas Features vs Target")
            plt.savefig(self.figures_path / "03_correlacion_features.png")
            plt.close()
        
        self.logger.info(f"Figures saved to {self.figures_path}")
