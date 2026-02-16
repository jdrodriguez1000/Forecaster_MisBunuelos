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
* **Acción**: Sincronización incremental desde Supabase (formato Parquet) y Auditoría integral de salud de datos.
* **Controles Críticos**:
    * **Sync Logic**: Validar descarga incremental vs local, manejo de duplicados por `id`.
    * **Data Contract**: Validación estricta de esquema (columnas faltantes/extra) según `data_contract` en `config.yaml`.
    * **Mínimo Histórico**: Validar existencia de al menos **36 meses** de datos (especialmente en `ventas_diarias`).
    * **Salud Estadística**: Perfilado de nulos, valores centinela (0, -1, 999), varianza cero, alta cardinalidad y detección de huecos temporales.
    * **Auditoría Financiera**: Validación de integridad de negocio (Unidades: Normal + Promo = Total; Promos: Pagadas = Bonificadas; Cálculos: Ingresos, Costos y Utilidad concuerdan).
* **Salidas Lab**: JSON en `experiments/phase_01_discovery/artifacts/` y Parquets en `data/01_raw/`.
* **Salidas Prod**: JSON en `outputs/reports/phase_01_discovery/`.

### Phase 02: Robust Preprocessing (Cleansing)
* **Acción**: Limpieza profunda, estandarización, imputación lógica y agregación mensual.
* **Controles Críticos**:
    * **Data Contract**: Validación de esquema y tipos antes de procesar.
    * **Cleaning & Standard**: Deduplicación exacta y temporal (keep last), estandarización a snake_case.
    * **Temporal Reindexing**: Reindexar series diarias para recuperar huecos antes de la agregación.
    * **Imputación de Negocio**: Lógica específica para Macro (Rolling Mean), Promo (inferencia por mes) y Marketing (interpolación en rangos activos).
    * **Recálculo Financiero**: Corrección selectiva de Ingresos/Costos solo en filas imputadas/corregidas.
    * **Anti-Data Leakage**: Recorte obligatorio del mes en curso (incompleto) para evitar sesgos.
    * **Agregación**: Resample a granularidad Mensual (MS) aplicando reglas específicas (sum para ventas, first para macro).
* **Salidas Lab**: JSON y Parquets en `experiments/phase_02_preprocessing/`.
* **Salidas Prod**: Dataset maestro `master_monthly.parquet` en `data/02_cleansed/` y reportes en `outputs/reports/phase_02_preprocessing/`.

### Phase 03: Exploratory Data Analysis (EDA)
* **Acción**: Análisis visual y estadístico profundo en Notebook bajo el principio **"Only Eyes on the Past"**.
* **Controles Críticos**:
    * **Partición Estricta**: Definición de límites Train/Val/Test. El EDA se limita al **Train set**.
    * **Estadística Avanzada**: Test de Dickey-Fuller (estacionariedad), detección de atípicos por IQR y análisis de Drift.
    * **Visualización de Negocio**: Descomposición estacional, Boxplots por mes (picos Dic/Jun) y KDE de impacto de Promociones.
    * **Dinámica Temporal**: Análisis de Correlación Cruzada (Lags) para Marketing y gráficos ACF/PACF.
    * **Contexto Histórico**: Identificación de la Pandemia como shock exógeno.
* **Salidas Lab**: Reporte JSON timestampped y figuras en `experiments/phase_03_eda/`.

### Phase 04: Feature Engineering (Enrichment)
* **Acción**: Creación de variables exógenas y proyecciones macro en `src/features.py`.
* **Controles Críticos**:
    * **Eventos**: Novenas (16-23 Dic), Primas (15-20 Jun/Dic), Días Pico (Sáb+Dom+Fest).
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
