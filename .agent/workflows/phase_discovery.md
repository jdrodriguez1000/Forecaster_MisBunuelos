---
description: Automatiza la creación del notebook `01_data_discovery.ipynb` para la extracción incremental de datos desde Supabase hacia `data/01_raw/` en formato Parquet. Toda la lógica de extracción se implementa directamente en el notebook (Fase Lab).
---

# Workflow: Fase 1 - Creación del Notebook de Discovery (Data Extraction)

Este flujo de trabajo tiene como objetivo generar automáticamente el notebook `notebooks/01_data_discovery.ipynb`. En esta fase de exploración (Lab), la lógica de carga incremental se implementa directamente dentro del notebook, utilizando únicamente `src/connectors/supabase_connector.py` como dependencia externa.

## 🛠️ Pasos de Ejecución

### Paso 1: Validación de Preparativos (Pre-flight Check)
* **Acción:** Verificar que `config.yaml` contenga:
    * `data.source_tables`: Lista de tablas a gestionar.
    * `data.full_update`: Flag de carga total.
    * `data.date_column`: Columna pivote para incrementales.
* **Acción:** Verificar que `.env` tenga credenciales válidas.

### Paso 2: Generación del Notebook (`notebooks/01_data_discovery.ipynb`)
El notebook debe ser autocontenido y estructurado celda por celda:

* **Celda 1: Setup:**
    * Imports (`pandas`, `yaml`, `pathlib`).
    * Importar conector: `from src.connectors.supabase_connector import get_supabase_client`.
    * Cargar configuración desde `config.yaml`.
    * Definir rutas (`RAW_DATA_PATH`).

* **Celda 2: Definición de Funciones de Carga (In-Notebook):**
    * Función `get_remote_max_date(table)`: Consulta `select max(fecha)` a Supabase.
    * Función `download_data(table, greater_than=None)`: Descarga datos (total o incremental).
    * Función `sync_table(table_name, full_update)`:
        * Verifica si existe `{table}.parquet` local.
        * Si no existe o `full_update=True` -> `download_data(all)`.
        * Si existe -> Compara `max_local` vs `max_remote`.
            * Iguales -> `Pass`.
            * Remoto > Local -> `download_data(> max_local)` y `append`.

* **Celda 3: Ejecución del Pipeline:**
    * Iterar sobre `config['data']['source_tables']`.
    * Ejecutar `sync_table()` para cada una.
    * Imprimir logs claros: "Tabla X: [STATUS] (Registros: N)".

* **Celda 4: Validación de Salud (Sanity Check):**
    * Leer cada parquet generado en `data/01_raw/`.
    * Mostrar `.info()` y `.head()` de cada uno.
    * **Validación Crítica:** Verificar si la tabla de ventas tiene al menos 36 meses de historia (según la regla de negocio).

* **Celda 5: Análisis Estadístico (Variables Numéricas):**
    * Para cada variable numérica detectada:
        * Calcular: Media, Mediana, Desviación Estándar.
        * Calcular: Mínimo, Máximo.
        * Calcular: Percentiles (25, 50, 75).
    * Almacenar resultados en diccionario de metadatos.

* **Celda 6: Análisis Temporal (Variables Datetime):**
    * Para cada variable datetime detectada:
        * Identificar fecha mínima y máxima.
        * Detectar fechas faltantes (gaps) si aplica (especialmente en series de tiempo diarias).
        * Detectar fechas duplicadas.
    * Almacenar resultados.

* **Celda 7: Análisis Categórico (Variables Object):**
    * Para cada variable categórica (object):
        * Identificar valores únicos.
        * Calcular frecuencia y peso relativo (%) de cada categoría.
    * Almacenar resultados.

* **Celda 8: Detección de Valores Atípicos (Outliers):**
    * Para variables numéricas (int, float):
        * Definir límites (ej. IQR o Z-score).
        * Contar atípicos superiores e inferiores.
        * Identificar límites de corte.
    * Almacenar resultados.

* **Celda 9: Detección de Varianza Cero (Zero Variance):**
    * Para todas las columnas de todos los archivos:
        * Verificar si la columna tiene un único valor (varianza cero).
        * Registrar las columnas que no aportan información.

* **Celda 10: Detección de Alta Cardinalidad:**
    * Leer parámetro `high_cardinality_threshold` desde `config.yaml` (sección `quality`).
    * Para todas las columnas (especialmente categóricas/object y discretas):
        * Calcular cardinalidad (valores únicos).
        * Si cardinalidad > threshold, marcar como Alta Cardinalidad.
        * (Opcional) Calcular ratio de cardinalidad si el threshold es relativo (0-1).

* **Celda 11: Detección de Presencia de Ceros:**
    * Leer parámetro `zero_presence_threshold` desde `config.yaml` (opcional, o usar default).
    * Para todas las variables numéricas:
        * Calcular porcentaje de valores que son exactamente 0.
        * Si supera el umbral, reportar alta presencia de ceros.

* **Celda 12: Detección de Filas Repetidas:**
    * Para cada archivo/tabla:
        * Identificar número de filas duplicadas (exact matches).
        * Reportar si existen duplicados, indicando la cantidad.

* **Celda 13: Detección de Valores Nulos:**
    * Para todas las columnas de todos los archivos:
        * Calcular cantidad y porcentaje de valores `NaN` o `None`.
        * Identificar columnas con alta presencia de nulos.
        * Reportar columnas afectadas y magnitud del problema.

* **Celda 14: Informe de Valores Centinela (Sentinel Values):**
    * Leer diccionario `sentinel_values` desde `config.yaml` (por tipo: `numeric`, `categorical`, `datetime`, `boolean`).
    * Para cada columna del archivo:
        * Determinar tipo de dato.
        * Buscar coincidencias exactas con los valores centinela configurados para ese tipo.
        * Reportar: `{ "columna": "nombre", "valor_centinela": valor, "conteo": n }`.

* **Celda 15: Validación de Contrato de Datos (Data Contract):**
    * Leer sección `data_contract` desde `config.yaml`.
    * Para cada archivo/tabla de datos fuente (`ventas_diarias`, `macro_economia`, `promocion_diaria`, `redes_sociales`):
        * Validar que todas las columnas esperadas estén presentes.
        * Validar que el tipo de datos coincida con lo esperado (`int`, `float`, `datetime`, `object`).
        * Detectar y reportar columnas adicionales (extra columns) no definidas en el contrato.
        * Generar estado `PASS` o `FAIL` para cada tabla.

* **Celda 16: Validación de Salud Financiera (Business Rules):**
    * Iterar `target_files` desde `config['financial_health']`.
    * Aplicar Regla 2.1: `total_unidades_entregadas` == SUM(`unidades_precio_normal`, `unidades_promo_pagadas`, `unidades_promo_bonificadas`).
    * Aplicar Regla 2.2: `unidades_promo_pagadas` == `unidades_promo_bonificadas`.
    * Aplicar Regla 2.3: `precio_unitario_full` >= `costo_unitario`.
    * Aplicar Regla 2.4: `utilidad` == `ingresos_totales` - `costo_total`.
    * Aplicar Regla 2.5: `ingresos_totales` == (`unidades_precio_normal` + `unidades_promo_pagadas`) * `precio_unitario_full`.
    * Aplicar Regla 2.6: `costo_total` == `total_unidades_entregadas` * `costo_unitario`.
    * Aplicar Regla 2.7: NO valores negativos en columnas numéricas.
    * Almacenar resultados de validación en `TABLE_ANALYSIS[table]['financial_health']`.

* **Celda 17: Generación de Reporte JSON:**
    * Recopilar todos los diccionarios de resultados:
        * `download_details`
        * `TABLE_ANALYSIS` (estadísticas, validaciones temporales, categoricas, outliers, varianza cero, cardinalidad, presencia de ceros, duplicados, nulos, centinelas, contrato de datos, salud financiera).
    * Estructurar el JSON final:
        ```json
        {
          "phase": "Phase 1 - Data Discovery",
          "timestamp": "ISO 8601",
          "description": "...",
          "download_details": [...],
          "data_analysis": { ... }
        }
        ```
    * Guardar en `experiments/phase_01_discovery/artifacts/phase_01_discovery.json`.
    * Imprimir mensaje de confirmación.

### Paso 3: Ejecución Manual y Verificación
* **Acción:** El usuario abrirá y ejecutará manualmente el notebook `notebooks/01_data_discovery.ipynb`.

### Paso 4: Limpieza de Archivos Temporales
* **Acción:** Eliminar cualquier archivo temporal generado durante la ejecución (`.py`, `.txt`, `.log`) que no forme parte del repositorio.
* **Comando Sugerido:** `Remove-Item -Path "notebooks/run_*.py", "notebooks/*.log", "notebooks/*.txt" -ErrorAction SilentlyContinue`
* **Motivo:** Mantener el entorno de notebooks limpio y evitar commits de scripts de ejecución temporal.
