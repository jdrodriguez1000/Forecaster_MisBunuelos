---
description: Manages the sequential execution of the forecasting pipeline, ensuring adherence to the Lab-to-Prod protocol and rigorous data science standards for each project phase.
---

# Skill: Gestor del Pipeline de Forecasting (Pipeline Manager)

Esta habilidad dirige la ejecución secuencial del ciclo de vida del proyecto, asegurando que cada fase técnica se complete con rigor científico y pase de la experimentación (Lab) a la producción (Prod) mediante el protocolo Lab-to-Prod.

## 🔄 Protocolo de Desarrollo por Fase
Para las fases 1, 2, 4 y 5, el agente debe certificar el cumplimiento de estos 5 pasos:
1. **[LAB]**: Desarrollo y validación en `notebooks/`. Las salidas van a `experiments/`.
2. **[REFACTOR]**: Migración de lógica a funciones/clases en `src/`.
3. **[ORCHESTRATE]**: Integración y llamada desde el orquestador `main.py`.
4. **[TEST]**: Ejecución de pruebas unitarias en `tests/` vía `pytest`.
5. **[CLOSE]**: Generación de reporte JSON oficial en `outputs/reports/`.

## 🔬 Fases Obligatorias del Pipeline

### Phase 01: Discovery & Audit (Data Health)
* **Acción**: Extracción de Supabase y Auditoría Médica de salud de datos.
* **Controles Críticos**:
    * **Mínimo Histórico**: Validar la existencia de al menos **36 meses** de datos.
    * **Salud**: Detectar valores centinela (0, -1, 999) e integridad temporal (sin huecos).
* **Salidas Lab**: JSON en `experiments/phase_01_discovery/artifacts/`.
* **Salidas Prod**: JSON en `outputs/reports/phase_01_discovery/`.

### Phase 02: Robust Preprocessing (Cleansing)
* **Acción**: Limpieza, tratamiento de anomalías y agregación mensual en `src/preprocessing.py`.
* **Controles Críticos**:
    * **Agregación**: Resample a granularidad Mensual (MS) mediante suma.
    * **Limpieza**: Aplicar imputación de nulos/centinelas según parámetros de `config.yaml`.
* **Salidas Lab**: JSON y figuras en `experiments/phase_02_preprocessing/`.
* **Salidas Prod**: JSON y figuras en `outputs/reports/phase_02_preprocessing/` y `outputs/figures/phase_02_preprocessing/`.

### Phase 03: Exploratory Data Analysis (EDA)
* **Acción**: Análisis visual profundo en Notebook. **Nota**: Finaliza en paso [LAB].
* **Controles Críticos**: Descomposición estacional (Trend/Season/Resid), Boxplots de meses pico y validación estadística de impactos (Novenas/Primas).
* **Artefacto**: Figuras en `experiments/phase_03_eda/figures/`.

### Phase 04: Feature Engineering (Enrichment)
* **Acción**: Creación de variables exógenas y proyecciones macro en `src/features.py`.
* **Controles Críticos**:
    * **Eventos**: Novenas (16-24 Dic), Primas (15-20 Jun/Dic), Días Pico (Sáb+Dom+Fest).
    * **Proyección**: Aplicar **Promedio Móvil Recursivo de 2 meses** para el horizonte $X$ a $X+5$.
* **Salidas Prod**: Dataset final en `data/04_processed/` y reportes en `outputs/reports/phase_04_features/`.

### Phase 05: Modeling & Forecasting (Execution)
* **Acción**: Entrenamiento competitivo, Tuning y Backtesting en `src/models.py`.
* **Controles Críticos**:
    * **Batería**: Evaluar Ridge, RandomForest, LGBM, XGB, GradientBoosting, HistGradientBoosting.
    * **Backtesting Rodante**: Partición 12 (Test) / 12 (Val) usando `ForecasterDirect`.
    * **Selección**: El modelo campeón debe superar el WAPE del **Seasonal Naive**.
* **Salidas Prod**: Resultados en `outputs/forecasts/`, `outputs/models/` y reportes por fase.

## 📊 Protocolo de Artefactos (Trazabilidad)
El gestor debe asegurar que cada fase genere su reporte JSON con el estatus de validación:
* **Ambiente Lab**: Los reportes se dirigen a `experiments/phase_0X_name/artifacts/`.
* **Ambiente Prod**: Los reportes oficiales se dirigen a `outputs/reports/phase_0X_name/`.
* **Contenido**: Debe incluir el status de `pytest`, métricas de la fase y timestamp ISO 8601.
