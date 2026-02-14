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

* **Celda 4: Validación de Salud (Sanity Check) y Generación de Reporte:**
    * Leer cada parquet generado en `data/01_raw/`.
    * Mostrar `.info()` y `.head()` de cada uno.
    * **Validación Crítica:** Verificar si la tabla de ventas tiene al menos 36 meses de historia (según la regla de negocio).
    * **Generación de Reporte (JSON):**
        * Estructurar el JSON para incluir la sección `download_details` *antes* de `validation_details`.
        * Para cada tabla, registrar:
            * `status`: "Full Download", "Incremental Download" o "Up to Date".
            * `new_rows`: Número de filas descargadas (0 si está al día).
            * `total_rows`: Total de filas en el archivo local despues de la operación.
            * `download_timestamp`: Fecha y hora de la operación.

### Paso 3: Ejecución Manual y Verificación
* **Acción:** El usuario abrirá y ejecutará manualmente el notebook `notebooks/01_data_discovery.ipynb`.

### Paso 4: Limpieza de Archivos Temporales
* **Acción:** Eliminar cualquier archivo temporal generado durante la ejecución (`.py`, `.txt`, `.log`) que no forme parte del repositorio.
* **Comando Sugerido:** `Remove-Item -Path "notebooks/run_*.py", "notebooks/*.log", "notebooks/*.txt" -ErrorAction SilentlyContinue`
* **Motivo:** Mantener el entorno de notebooks limpio y evitar commits de scripts de ejecución temporal.
