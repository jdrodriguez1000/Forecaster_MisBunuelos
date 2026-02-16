
import json
import os
from pathlib import Path

# Define the notebook structure
notebook_content = {
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Fase 4: Feature Engineering Estratégico\n",
    "\n",
    "Este notebook implementa la ingeniería de variables externas y de negocio para el proyecto **Forecaster Mis Buñuelos**.\n",
    "\n",
    "**Objetivo:** Generar `data/03_features/master_features.parquet` con variables cíclicas, binarias y retardos de marketing."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Celda 1: Setup y Configuración\n",
    "import pandas as pd\n",
    "import numpy as np\n",
    "import yaml\n",
    "from pathlib import Path\n",
    "import os\n",
    "import matplotlib.pyplot as plt\n",
    "import seaborn as sns\n",
    "from datetime import datetime\n",
    "\n",
    "# Definir Rutas\n",
    "BASE_DIR = Path(os.getcwd())\n",
    "if BASE_DIR.name == \"notebooks\":\n",
    "    BASE_DIR = BASE_DIR.parent\n",
    "\n",
    "CONFIG_PATH = BASE_DIR / \"config.yaml\"\n",
    "INPUT_DATA_PATH = BASE_DIR / \"data\" / \"02_cleansed\"\n",
    "OUTPUT_DATA_PATH = BASE_DIR / \"data\" / \"03_features\"\n",
    "ARTIFACTS_PATH = BASE_DIR / \"experiments\" / \"phase_04_feature_engineering\" / \"artifacts\"\n",
    "FIGURES_PATH = BASE_DIR / \"experiments\" / \"phase_04_feature_engineering\" / \"figures\"\n",
    "\n",
    "# Crear directorios\n",
    "OUTPUT_DATA_PATH.mkdir(parents=True, exist_ok=True)\n",
    "ARTIFACTS_PATH.mkdir(parents=True, exist_ok=True)\n",
    "FIGURES_PATH.mkdir(parents=True, exist_ok=True)\n",
    "\n",
    "# Cargar Configuración\n",
    "with open(CONFIG_PATH, \"r\", encoding=\"utf-8\") as f:\n",
    "    config = yaml.safe_load(f)\n",
    "\n",
    "print(\"Configuración cargada y rutas establecidas.\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Celda 2: Carga de Datos\n",
    "input_file = INPUT_DATA_PATH / \"master_monthly.parquet\"\n",
    "if not input_file.exists():\n",
    "    raise FileNotFoundError(f\"No se encontró el archivo maestro: {input_file}\")\n",
    "\n",
    "df = pd.read_parquet(input_file)\n",
    "df.index.name = 'fecha' # Asegurar que el índice tenga nombre si no lo tiene\n",
    "print(f\"Dataset cargado: {df.shape}\")\n",
    "df.head()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Celda 3: Variables Cíclicas (Seno/Coseno)\n",
    "print(\"Generando variables cíclicas...\")\n",
    "fe_config = config.get('feature_engineering', {})\n",
    "cyclical_cols = fe_config.get('cyclical_columns', [])\n",
    "\n",
    "if 'month' in cyclical_cols:\n",
    "    df['month_sin'] = np.sin(2 * np.pi * df.index.month / 12)\n",
    "    df['month_cos'] = np.cos(2 * np.pi * df.index.month / 12)\n",
    "\n",
    "if 'quarter' in cyclical_cols:\n",
    "    df['quarter_sin'] = np.sin(2 * np.pi * df.index.quarter / 4)\n",
    "    df['quarter_cos'] = np.cos(2 * np.pi * df.index.quarter / 4)\n",
    "\n",
    "if 'semester' in cyclical_cols:\n",
    "    # Semestre: (mes-1)//6 + 1 -> 1 o 2\n",
    "    semester = (df.index.month - 1) // 6 + 1\n",
    "    df['semester_sin'] = np.sin(2 * np.pi * semester / 2)\n",
    "    df['semester_cos'] = np.cos(2 * np.pi * semester / 2)\n",
    "\n",
    "print(f\"Columnas cíclicas creadas. Shape actual: {df.shape}\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Celda 4: Banderas Binarias de Negocio\n",
    "print(\"Generando banderas binarias...\")\n",
    "biz_events = config.get('business_events', {})\n",
    "\n",
    "# 4.1 Novenas (Diciembre)\n",
    "df['is_novenas'] = (df.index.month == 12).astype(int)\n",
    "\n",
    "# 4.2 Primas (Junio y Diciembre)\n",
    "primas_months = biz_events.get('primas', {}).get('months', [6, 12])\n",
    "df['is_primas'] = (df.index.month.isin(primas_months)).astype(int)\n",
    "\n",
    "# 4.3 Pandemia (Rango configurable)\n",
    "pandemic_cfg = biz_events.get('pandemic', {})\n",
    "p_start = pd.to_datetime(pandemic_cfg.get('start_date', '2020-04-01'))\n",
    "p_end = pd.to_datetime(pandemic_cfg.get('end_date', '2021-12-31'))\n",
    "df['is_pandemic'] = ((df.index >= p_start) & (df.index <= p_end)).astype(int)\n",
    "\n",
    "print(\"Banderas binarias creadas.\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Celda 5: Marketing Estratégico (Lag 1)\n",
    "print(\"Generando lag de marketing...\")\n",
    "mkt_lags = fe_config.get('marketing_lags', [])\n",
    "\n",
    "for cfg in mkt_lags:\n",
    "    col = cfg['column']\n",
    "    lag = cfg['lag']\n",
    "    fill_val = cfg.get('fill_value', 0)\n",
    "    \n",
    "    new_col_name = f\"{col}_lag_{lag}\"\n",
    "    df[new_col_name] = df[col].shift(lag)\n",
    "    \n",
    "    # Aplicar Backfill/Fillna para cumplir con el requisito de \"0 nulos\"\n",
    "    df[new_col_name] = df[new_col_name].fillna(fill_val)\n",
    "    print(f\"  - Creada {new_col_name} con fill_value={fill_val}\")\n",
    "\n",
    "print(f\"Ingeniería completada. Total columnas: {len(df.columns)}\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Celda 6: Validación y Visualización de Laboratorio\n",
    "print(\"Generando visualizaciones de validación...\")\n",
    "\n",
    "# 6.1 Visualización de Banderas vs Target\n",
    "plt.figure(figsize=(15, 6))\n",
    "plt.plot(df.index, df[config['project']['target_column']], label='Ventas (Target)', color='blue', alpha=0.6)\n",
    "plt.fill_between(df.index, 0, df[config['project']['target_column']].max(), \n",
    "                 where=df['is_novenas']==1, color='red', alpha=0.2, label='Novenas')\n",
    "plt.fill_between(df.index, 0, df[config['project']['target_column']].max(), \n",
    "                 where=df['is_primas']==1, color='green', alpha=0.1, label='Primas')\n",
    "plt.title(\"Validación Visual de Eventos de Negocio\")\n",
    "plt.legend()\n",
    "plt.savefig(FIGURES_PATH / \"01_validacion_eventos.png\")\n",
    "plt.show()\n",
    "\n",
    "# 6.2 Visualización de Ciclos (Month Sin/Cos)\n",
    "plt.figure(figsize=(6, 6))\n",
    "plt.scatter(df['month_sin'], df['month_cos'], c=df.index.month, cmap='twilight')\n",
    "plt.title(\"Representación Cíclica de los Meses (Seno/Coseno)\")\n",
    "plt.colorbar(label='Mes')\n",
    "plt.savefig(FIGURES_PATH / \"02_ciclos_mensuales.png\")\n",
    "plt.show()\n",
    "\n",
    "# 6.3 Correlación de Features Nuevas\n",
    "new_cols = ['month_sin', 'month_cos', 'is_novenas', 'is_primas', 'is_pandemic', 'inversion_total_lag_1']\n",
    "corr = df[new_cols + [config['project']['target_column']]].corr()\n",
    "plt.figure(figsize=(10, 8))\n",
    "sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=\".2f\")\n",
    "plt.title(\"Correlación: Nuevas Features vs Target\")\n",
    "plt.savefig(FIGURES_PATH / \"03_correlacion_features.png\")\n",
    "plt.show()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Celda 7: Exportación de Resultados y Reporte Robusto\n",
    "import json\n",
    "print(\"Exportando datos y generando reporte robusto...\")\n",
    "output_file = OUTPUT_DATA_PATH / \"master_features.parquet\"\n",
    "df.to_parquet(output_file)\n",
    "\n",
    "# Identificar columnas\n",
    "# Se asume que 'original_cols' son las columnas antes de este notebook\n",
    "# Para este ejemplo, se definen las columnas originales de forma explícita o se cargan de un estado anterior\n",
    "# Si no se tiene un estado anterior, se puede inferir las nuevas columnas de otra manera.\n",
    "# Para mantener la robustez, se puede guardar la lista de columnas originales en el config o un artefacto previo.\n",
    "# Aquí, para simplificar, se asume que 'original_cols' es una lista predefinida o cargada.\n",
    "# En un flujo real, 'original_cols' debería venir del reporte de la fase anterior.\n",
    "original_cols = [col for col in df.columns if col not in ['month_sin', 'month_cos', 'quarter_sin', 'quarter_cos', 'semester_sin', 'semester_cos', 'is_novenas', 'is_primas', 'is_pandemic'] and not col.endswith('_lag_1')]\n",
    "new_cols = [c for c in df.columns if c not in original_cols]\n",
    "\n",
    "# Muestra de datos para el JSON (orientado a registros)\n",
    "data_preview = {\n",
    "    \"head_5\": df.head(5).reset_index().astype(str).to_dict(orient='records'),\n",
    "    \"tail_5\": df.tail(5).reset_index().astype(str).to_dict(orient='records'),\n",
    "    \"sample_5\": df.sample(min(5, len(df)), random_state=config['project']['random_state']).reset_index().astype(str).to_dict(orient='records')\n",
    "}\n",
    "\n",
    "# Generar Reporte JSON Robusto\n",
    "report = {\n",
    "    \"phase\": \"Phase 4 - Feature Engineering\",\n",
    "    \"timestamp\": datetime.now().isoformat(),\n",
    "    \"input_file\": \"master_monthly.parquet\",\n",
    "    \"output_file\": \"master_features.parquet\",\n",
    "    \"variables\": {\n",
    "        \"original_columns\": original_cols,\n",
    "        \"new_features\": {col: str(df[col].dtype) for col in new_cols}\n",
    "    },\n",
    "    \"summary\": {\n",
    "        \"total_rows\": len(df),\n",
    "        \"total_columns\": len(df.columns),\n",
    "        \"new_features_count\": len(new_cols),\n",
    "        \"nulls_check\": int(df.isnull().sum().sum()),\n",
    "        \"temporal_range\": [df.index.min().isoformat(), df.index.max().isoformat()]\n",
    "    },\n",
    "    \"data_preview\": data_preview\n",
    "}\n",
    "\n",
    "with open(ARTIFACTS_PATH / \"phase_04_feature_engineering.json\", \"w\") as f:\n",
    "    json.dump(report, f, indent=4)\n",
    "\n",
    "print(f\"✅ Fase completada exitosamente. Archivo guardado en: {output_file}\")"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
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
   "version": "3.12.3"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}

# Write the notebook
notebook_path = Path("notebooks/04_feature_engineering.ipynb")
with open(notebook_path, "w", encoding="utf-8") as f:
    json.dump(notebook_content, f, indent=4)

print(f"Notebook generated at {notebook_path}")
