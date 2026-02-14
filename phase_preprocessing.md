---
description: Automatiza la creación del notebook `02_preprocessing.ipynb` para la limpieza, imputación de anomalías y agregación mensual de los datos crudos.
---

# Workflow: Fase 2 - Preprocesamiento Robusto (Cleaning & Aggregation)

Este flujo de trabajo tiene como objetivo generar automáticamente el notebook `notebooks/02_preprocessing.ipynb`. Su misión es transformar los datos crudos validados en la Fase 1 en un **Dataset Analítico Mensual** limpio, consistente y listo para la ingeniería de características.

## 🛠️ Pasos de Ejecución

### Paso 1: Validación de Preparativos (Pre-flight Check)
* **Acción:** Verificar que `config.yaml` contenga la sección `preprocessing` con:
    * `frequency`: Frecuencia de agregación (MS).
    * `filters`: Reglas de filtrado (exclude_ids, min_date).
    * `aggregation_rules`: Métodos de agregación por variable.
* **Acción:** Verificar que existan los datos crudos en `data/01_raw/`:
    * `ventas_diarias.parquet`
    * `redes_sociales.parquet`
    * `promocion_diaria.parquet`
    * `macro_economia.parquet`

### Paso 2: Generación del Notebook (`notebooks/02_preprocessing.ipynb`)
El notebook debe ser autocontenido y estructurado celda por celda:

* **Celda 1: Setup:**
    * Imports (`pandas`, `yaml`, `pathlib`, `numpy`).
    * Cargar configuración desde `config.yaml`.
    * Definir rutas (`RAW_DATA_PATH`, `CLEANSED_DATA_PATH`).
    * Configurar pandas options (display max columns).

* **Celda 2: Carga de Datos Crudos:**
    * Leer los archivos `.parquet` desde `data/01_raw/`.
    * Imprimir shape inicial de cada dataframe.

* **Celda 3: Validación de Contrato de Datos (Critical Check):**
    * Leer sección `data_contract` desde `config.yaml`.
    * Para cada DataFrame cargado (`ventas`, `marketing`, `promo`, `macro`):
        * Obtener lista de columnas obligatorias del contrato.
        * Verificar que TODAS las columnas del contrato estén presentes en el DataFrame.
        * **Regla Crítica:**
            * Si falta alguna columna:
                * Imprimir ERROR CRÍTICO detallando columnas faltantes.
                * Lanzar excepción (`raise RuntimeError`) para detener la ejecución inmediatamente.
            * Si sobran columnas: Permitido (Log de advertencia opcional).
    * Imprimir "Validación de Contrato Exitosa" si supera el chequeo.

* **Celda 4: Estandarización de Nombres (Cleaning):**
    * Aplicar `rename_map` del config (ej. `campaña` -> `campana`).
    * Convertir nombres de columnas a snake_case si es necesario.
    * Verificar que las columnas clave existan post-renombramiento.

* **Celda 5: Selección de Columnas (Schema Enforcement):**
    * Obtener la lista de columnas esperadas del `data_contract` para cada tabla.
    * Aplicar el mismo `rename_map` a esta lista de columnas esperadas (actualizar lista con los nuevos nombres).
    * Filtrar el DataFrame para conservar **únicamente** las columnas de esta lista válida.
    * Eliminar columnas huérfanas o extrañas (ej. `id` u otras no contractuadas).
    * Reportar columnas eliminadas.

* **Celda 6: Limpieza de Filas (Duplicados y Ruido):**
    * **Deduplicación:**
        * Eliminar duplicados exactos (`drop_duplicates()`).
        * **Regla Temporal:** Validar unicidad de índice temporal. Si existen fechas repetidas, conservar el **último** registro insertado (`keep='last'`).
    * **Filtrado (Config):**
        * Aplicar reglas de `filters` del config (especialmente `min_date`).
        * **Nota:** El filtrado de IDs (ej. 999) ya no aplica porque la columna `id` fue removida en el paso de Selección de Columnas.
    * **Logging:**
        * Reportar conteo detallado de filas eliminadas por duplicidad y por filtrado fecha para cada archivo.

* **Celda 7: Tratamiento de Valores Centinela (Sentinel Handling):**
    * Leer `sentinel_values` desde `config.yaml` (bloque `quality`).
    * Iterar sobre cada DataFrame y sus columnas:
        * Identificar el tipo de dato de la columna.
        * Comparar valores con la lista de centinelas configurada (ej. `numeric`: [-1, 999]).
        * **Regla de Excepción:**
            * Si la columna es `confianza_consumidor` (macro_economia) y el valor es `-1`, **NO** transformar a NaN (es un valor válido de negocio/encuesta negativa).
        * Para los demás casos: Reemplazar el valor centinela por `np.nan` (o `None`).
    * Reportar cuántos valores fueron transformados a NaN por columna.

* **Celda 8: Garantizar Completitud Temporal (Reindexing Inteligente):**
    * Definir el rango de fechas global (desde `min_date` hasta última fecha).
    * Leer diccionario de frecuencias desde `config['preprocessing']['data_frequency']`.
    * **Para cada DataFrame:**
        * Identificar su frecuencia natural (ej. `macro_economia` -> 'MS', `ventas_diarias` -> 'D').
        * Generar el índice completo específico para esa frecuencia (`pd.date_range(..., freq=freq)`).
        * Reindexar para exponer huecos (nulos) respetando la granularidad temporal de la fuente.
        * *Nota:* Esto evita generar ~30 filas nulas por mes en datos mensuales.
    * Reportar filas añadidas por reindexado para cada fuente.

* **Celda 9: Imputación de Nulos (Business Logic - Pre-Aggregation):**
    * **Macroeconomía (`macro_economia`):**
        * Iterar sobre columnas numéricas (`ipc_mensual`, `trm_promedio`, etc.).
        * Si existe un valor nulo: Imputar con el **Promedio de los 2 meses anteriores**.
            * *Nota Técnica:* Usar `.rolling(window=2, min_periods=1).mean().shift(1)` o lógica similar iterativa para asegurar causalidad.
    * **Promociones (`promocion_diaria`):**
        * Si existe valor nulo en `es_promo`:
            * Verificar el mes de la fecha (`dt.month`).
            * Si mes es 4 (Abr), 5 (May), 9 (Sep) o 10 (Oct) -> Imputar **1**.
            * En cualquier otro caso -> Imputar **0**.
    * **Redes Sociales (`redes_sociales`):**
        * **1. Imputación de `campaña`:**
            * Si `campaña` es Nulo y existe inversión (`inversion_facebook > 0` o `inversion_instagram > 0`):
                * Si mes in [3, 4, 5]: Imputar "Ciclo Abr-May".
                * Si mes in [8, 9, 10]: Imputar "Ciclo Sep-Oct".
                * Else: "Sin Campaña".
        * **2. Imputación de Inversiones (`inversion_facebook`, `inversion_instagram`):**
            * Definir rangos activos:
                * Rango 1: 15-Marzo a 25-Mayo.
                * Rango 2: 15-Agosto a 25-Octubre.
            * Lógica:
                * Si fecha dentro de rango activo y valor es Nulo: **Imputar usando Interpolación Lineal** (para simular el valor usado en esa fecha).
                * Si fecha fuera de rango activo y valor es Nulo: Imputar **0**.
        * **3. Consistencia de `inversion_total_diaria`:**
            * Primero, si `inversion_total_diaria` es Nulo, calcular = `inversion_facebook` + `inversion_instagram`.
            * **Regla Final:** Si se modificó FB o IG, **recalcular forzosamente** `inversion_total_diaria` = `inversion_facebook` + `inversion_instagram` para mantener consistencia matemática.
    * **Ventas Diarias (`ventas_diarias`):**
        * **Precios y Costos (`precio_unitario`, `costo_unitario`):**
            * Aplicar **Forward Fill (`ffill`)**: El precio de hoy es igual al de ayer.
            * Si faltan al inicio, usar Backward Fill (`bfill`).
        * **Paso 1: Imputar Total (`total_unidades_entregadas`):**
            * Si hay huecos pequeños (<= 2 días): **Interpolación Lineal**.
            * Si hay huecos grandes (> 2 días): **Promedio Móvil 7 días**.
        * **Paso 2: Imputar Componentes (Desglose):**
            * `unidades_promo_pagadas` y `unidades_promo_bonificadas`: Si es Null -> Imputar **0** (Asunción conservadora: ante duda, no hubo promo).
            * `unidades_precio_normal`: Si es Null -> Calcular como **Residual**.
                * *Fórmula:* `unidades_precio_normal` = `total_unidades_entregadas` - (`unidades_promo_pagadas` + `unidades_promo_bonificadas`).
            * *Validación:* Asegurar que `unidades_precio_normal` no sea negativo (clipping a 0 si fuera necesario, aunque improbable con esta lógica).
    * Reportar estadísticas de imputación para todas las fuentes.

* **Celda 10: Recálculo Financiero Selectivo (Targeted Correction):**
    * Identificar filas modificadas en el paso anterior sobre el archvio Ventas Diarias (`ventas_diarias`) (usar máscara de nulos original o flag).
    * **Solo en filas imputadas:**
        * Recalcular `costo_total` = `total_unidades_entregadas` * `costo_unitario`.
        * Recalcular `ingresos_totales` = (`unidades_precio_normal` + `unidades_promo_pagadas`) * `precio_unitario_full`.
        * Recalcular `utilidad` = `ingresos_totales` - `costo_total`.
    * *Validación:* Verificar que no queden valores negativos en `utilidad` salvo casos excepcionales explicables.
    * Reportar estadísticas: "Filas recalentadas financieramente: X".

* **Celda 11: Agregación Mensual (Resampling Strategy):**
    * Iterar sobre cada dataset (`ventas`, `marketing`, `promo`, `macro`).
    * Set index a `fecha` (asegurar datetime).
    * Aplicar `.resample('MS').agg(rules)` usando las reglas específicas del config.
    * **Nota:** Para `promocion_diaria`, la suma de `es_promo` se convierte en `dias_en_promo`.
    * **Nota:** Para `macro_economia`, usar `first` para alinear al día 1 (tras haber imputado nulos en Celda 9).

* **Celda 12: Unificación de Fuentes (Merging):**
    * Realizar `pd.merge` (left/outer) usando la tabla de ventas agreagada como base (Master).
    * Unir con Marketing, Promos y Macro.
    * Validar que el índice temporal sea continuo (sin huecos de meses inesperados).

* **Celda 13: Imputación de Nulos (Post-Merge Gaps):**
    * Detectar nulos generados por el merge (meses sin datos en alguna fuente).
    * Aplicar reglas generales de imputación del config (`numeric` -> `interpolate` o `mean`).
    * Esta es una imputación de "seguridad" para huecos estructurales, distinta a la lógica de negocio de la Celda 9.

* **Celda 14: Exportación de Datos:**
    * Guardar el DataFrame final en `data/02_cleansed/master_monthly.parquet`.
    * Guardar también en formato CSV para inspección rápida (opcional).

* **Celda 15: Generación de Reporte JSON (Mandatory):**
    * Construir el diccionario de reporte siguiendo estrictamente `projectrules.md`.
    * Estructura:
        ```json
        {
          "phase": "Phase 2 - Preprocessing",
          "timestamp": "ISO 8601",
          "description": "Limpieza, recálculo financiero y agregación mensual.",
          "preprocessing_stats": {
            "rows_original": "...",
            "rows_reindexed_filled": "...",
            "rows_filtered": "...",
            "sentinels_cleaned": "...",
            "imputed_values_pre_agg": "...",
            "financial_corrections": "...",
            "monthly_steps": "..."
          },
          "validation_status": "PASS/FAIL"
        }
        ```
    * Guardar en `experiments/phase_02_preprocessing/artifacts/phase_02_preprocessing.json`.

### Paso 4: Limpieza de Archivos Temporales
* **Acción:** Eliminar cualquier archivo temporal generado durante la ejecución (`.py`, `.txt`, `.log`) que no forme parte del repositorio.
* **Comando Sugerido:** `Remove-Item -Path "notebooks/run_*.py", "notebooks/*.log", "notebooks/*.txt" -ErrorAction SilentlyContinue`
* **Motivo:** Mantener el entorno de notebooks limpio.