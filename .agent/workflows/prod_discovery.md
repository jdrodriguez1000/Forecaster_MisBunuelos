---
description: Refactorizar y Orquestar la Fase 1 (Discovery) de Notebook a Producción
---

# Flujo de Trabajo: Fase de Descubrimiento en Producción (Refactorizar y Orquestar)

Este flujo de trabajo migra la lógica de extracción de datos, validación y chequeos de salud desde `notebooks/01_data_discovery.ipynb` al código base de producción en `src/loader.py`.

## Pasos

1. **Verificar Configuración**
   - Asegurar que `config.yaml` contenga la sección `financial_health` utilizada en la fase de Laboratorio.

2. **Crear `src/loader.py`**
   - Crear una clase `DataLoader` robusta que encapsule la lógica validada en el notebook.
   - **Componentes Clave**:
     - **Imports**: `pandas`, `yaml`, `pathlib`, `datetime`, `json`, `numpy`, y `src.connectors.supabase_connector`.
     - **Inicialización**: Cargar configuración y establecer conexión con Supabase.
     - **Métodos**:
       - `get_remote_max_date(table, date_col)`: Para la lógica incremental.
       - `download_data(table, date_col, greater_than)`: Manejar la paginación de Supabase.
       - `sync_table(table, date_col, full_update)`: Gestionar Lógica Completa vs Incremental, guardar en `data/01_raw/`.
       - `validate_contract(df, table)`: Verificar columnas faltantes/extra y discrepancias de tipos.
       - `check_financial_health(df, table)`: Implementar **estrictamente** las reglas de negocio (2.1 - 2.7) para `ventas_diarias`.
       - `generate_statistics(df)`: Calcular media, mediana, nulos, ceros, valores atípicos, etc.
       - `run()`: El punto de entrada principal que itera a través de las tablas, realiza la sincronización, validación y guarda el reporte JSON final en `outputs/reports/phase_01_discovery/`.

3. **Orquestar en `main.py`**
   - Actualizar `main.py` para importar `DataLoader` desde `src.loader`.
   - Agregar el paso de ejecución para correr el cargador al inicio del pipeline.

4. **Crear Pruebas Unitarias (`tests/test_loader.py`)**
   - Crear `tests/test_loader.py` para validar:
     - Lógica de carga incremental (simulando respuestas de Supabase).
     - Validación del Contrato de Datos (probando escenarios PASS/FAIL).
     - Lógica de Salud Financiera (verificando que detecte filas inválidas).
     - Generación del reporte JSON.

5. **Verificar Paridad de Reportes (JSON)**
   - **Requisito Crítico:** El archivo JSON generado por `main.py` (`outputs/reports/phase_01_discovery/phase_01_discovery.json`) debe coincidir estrictamente en estructura, métricas y contenido con el reporte generado por el notebook (`experiments/.../artifacts/*.json`).
   - El código de producción debe implementar TODA la lógica de análisis estadístico, validación y reglas de negocio presente en el notebook de laboratorio.
   - Cualquier discrepancia en conteos, nulos, outliers o validaciones financieras debe ser investigada y resuelta antes de aprobar el paso a producción.

6. **Ejecutar Pruebas (Happy & Sad Paths)**
   - Ejecutar `pytest tests/test_loader.py` para asegurar que el código refactorizado sea robusto.
   - **Pruebas de Éxito (Happy Path):** Verificar que la ingesta, validación y reporte funcionan con datos correctos.
   - **Pruebas de Fallo (Sad Path):** Verificar que el sistema maneja errores gracefulmente:
     - Tablas vacías o inexistentes.
     - Fallos de conexión a Supabase.
     - Archivos corruptos o con esquema incorrecto (validación de contrato fallida).
     - Validación financiera fallida (reglas de negocio no cumplidas).

7. **Limpieza de Archivos Temporales**
   - El flujo de trabajo debe asegurar la eliminación de cualquier archivo temporal creado durante la ejecución o pruebas (ej: scripts de debug `debug_*.py`, archivos de salida temporal `*.txt`, `*.log`).
   - Mantener el entorno de producción limpio, dejando únicamente los artefactos finales oficiales en `outputs/`.
