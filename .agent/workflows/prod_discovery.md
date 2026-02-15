---
description: Refactorizar y Orquestar la Fase 1 (Discovery) de Notebook a Producción
---

# Flujo de Trabajo: Fase de Descubrimiento en Producción (Refactorizar y Orquestar)

Este flujo de trabajo migra la lógica de extracción de datos, validación y chequeos de salud desde `notebooks/01_data_discovery.ipynb` al código base de producción en `src/loader.py`.

## Pasos

1. **Verificar Configuración**
   - Asegurar que `config.yaml` contenga la sección `financial_health` utilizada en la fase de Laboratorio.

2. **Construir `src/loader.py` basado en Lógica de Notebook**
   - El objetivo principal es trasladar **toda la lógica de negocio y análisis de datos** desarrollada y valida en `notebooks/01_data_discovery.ipynb` al archivo `src/loader.py`.
   - **Componentes Clave a Implementar**:
     - **Detección de Valores Extremos (Outliers)**: Implementar la misma lógica de rango intercuartílico (IQR) o desviación estándar usada en el notebook para identificar y reportar outliers.
     - **Manejo de Valores Centinela**: Incluir la detección de valores centinela (ej. -1, 999) definidos en la fase de exploración.
     - **Análisis de Nulos y Ceros**: Replicar el cálculo de porcentaje de nulos y ceros por columna.
     - **Validación del Contrato de Datos**: Verificar columnas faltantes/extra y discrepancias de tipos.
     - **Salud Financiera**: Implementar estrictamente las reglas de negocio (2.1 - 2.7) para `ventas_diarias`.
     - **Estadísticas Descriptivas**: Calcular media, mediana, min, max, cuantiles, etc.
   - **Estructura de la Clase `DataLoader`**:
     - **Imports**: `pandas`, `yaml`, `pathlib`, `datetime`, `json`, `numpy`, y `src.connectors.supabase_connector`.
     - **Métodos**:
       - `get_remote_max_date`, `download_data`, `sync_table`: Para la sincronización incremental.
       - `validate_contract`, `check_financial_health`: Validaciones de negocio.
       - `generate_statistics`: Método central que agrupa toda la lógica estadística (outliers, sentinelas, nulos, etc.).
       - `run()`: Orquestador que genera el reporte JSON final en `outputs/reports/phase_01_discovery/`.

3. **Orquestar en `main.py`**
   - Actualizar `main.py` para importar `DataLoader` desde `src.loader`.
   - Agregar el paso de ejecución para correr el cargador al inicio del pipeline.

4. **Crear Pruebas Unitarias (`tests/test_loader.py`)**
   - Crear `tests/test_loader.py` para validar:
     - Lógica de carga incremental (simulando respuestas de Supabase).
     - Validación del Contrato de Datos (probando escenarios PASS/FAIL).
     - Lógica de Salud Financiera (verificando que detecte filas inválidas).
     - Generación del reporte JSON.

5. **Ejecutar Pruebas (Happy & Sad Paths)**
   - Ejecutar `pytest tests/test_loader.py` para asegurar que el código refactorizado sea robusto.
   - **Pruebas de Éxito (Happy Path):** Verificar que la ingesta, validación y reporte funcionan con datos correctos.
   - **Pruebas de Fallo (Sad Path):** Verificar que el sistema maneja errores gracefulmente:
     - Tablas vacías o inexistentes.
     - Fallos de conexión a Supabase.
     - Archivos corruptos o con esquema incorrecto (validación de contrato fallida).
     - Validación financiera fallida (reglas de negocio no cumplidas).

6. **Limpieza de Archivos Temporales**
   - El flujo de trabajo debe asegurar la eliminación de cualquier archivo temporal creado durante la ejecución o pruebas (ej: scripts de debug `debug_*.py`, archivos de salida temporal `*.txt`, `*.log`).
   - Mantener el entorno de producción limpio, dejando únicamente los artefactos finales oficiales en `outputs/`.
