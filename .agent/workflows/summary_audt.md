---
description: Pipeline de Auditoría de Calidad (Resumen). Genera informes ejecutivos en 'docs/' analizando los resultados técnicos de las fases de Discovery, Preprocessing, EDA y Features.
---

# Workflow: Resumen de Auditoría (summary_audt)

Este workflow automatiza la revisión de los artefactos generados en el laboratorio y la creación de reportes de auditoría en la carpeta `docs/`.

## Pasos del Workflow

### 1. Preparación del Entorno
* Asegurar la existencia de la carpeta `docs/` en la raíz del proyecto.
* Consultar la habilidad `forecasting_quality_auditor.md` para aplicar los criterios de evaluación.
* **Nota de Calidad**: Los reportes generados DEBEN ser altamente detallados, incluyendo secciones de "Auditoría Técnica Detallada", "Valor Agregado (Beyond the Skills)" y "Brechas y Pendientes (The Gaps)".
* **Timestamp**: La fecha de auditoría debe incluir obligatoriamente **Hora, Minutos y Segundos** (Formato: `YYYY-MM-DD HH:MM:SS`).
* **Comunicación**: Es imperativo incluir una sección de **"Relaciones de Impacto (Simple Terms)"** y una **"Estrategia de Features"** (Lags/Windows) justificando cada decisión mediante la **triangulación** del Project Charter, los resultados del JSON y las Gráficas generadas.

### 2. Auditoría de la Fase 01: Discoverer
* **Ruta**: `experiments/phase_01_discovery/artifacts/`
* Buscar `phase_01_discovery.json`.
* **Acción**: 
    - Si existe: Analizar y generar `docs/phase_01_discoverer.md`.
    - Si NO existe: Notificar estado **CRÍTICO** y omitir reporte.

### 3. Auditoría de la Fase 02: Preprocessing
* **Ruta**: `experiments/phase_02_preprocessing/artifacts/`
* Buscar `phase_02_preprocessing.json`.
* **Acción**: 
    - Si existe: Analizar y generar `docs/phase_02_preprocessing.md`.
    - Si NO existe: Notificar estado **CRÍTICO**.

### 4. Auditoría de la Fase 03: EDA (Selección Temporal)
* **Ruta**: `experiments/phase_03_eda/artifacts/` y `experiments/phase_03_eda/figures/`
* **Buscar**: El JSON más actual (`phase_03_eda_YYYYMMDD_HHMMSS.json`).
* **Acción**: 
    - Identificar y listar las gráficas analizadas de la carpeta `figures/`.
    - **Análisis de Modelado**: Dictar recomendaciones sobre variables exógenas (basado en Project Charter), grilla de rezagos, transformaciones de serie y esquema de pesos por Eras (3 eras).
    - Generar `docs/phase_03_eda.md` con un enfoque táctico para la siguiente fase.

### 5. Auditoría de la Fase 04: Featurer
* **Ruta**: `experiments/phase_04_feature_engineering/artifacts/` y `experiments/phase_04_feature_engineering/figures/`
* **Buscar**: `phase_04_feature_engineering.json`.
* **Acción**: 
    - Si existe: 
        - Analizar tipos de datos y previsualización de `data_preview`.
        - Validar la representatividad de las 10 nuevas variables.
        - Analizar proactivamente las 3 gráficas críticas: `01_validacion_eventos.png`, `02_ciclos_mensuales.png` y `03_correlacion_features.png`.
        - Generar `docs/phase_04_featurer.md`.
    - Si NO existe: Notificar estado **CRÍTICO**.

### 6. Finalización
* Mostrar un resumen de los documentos creados y las fases pendientes de implementación.
