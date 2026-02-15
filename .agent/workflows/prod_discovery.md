---
description: Refactorizar y Orquestar la Fase 1 (Discovery) de Notebook a Producción
---

# Flujo de Trabajo: Fase de Descubrimiento en Producción (Refactorizar y Orquestar)

Este flujo de trabajo migra la lógica de extracción de datos, validación y salud financiera desde los experimentos representados en `scripts/gen_discoverer.py` hacia el código base de producción en `src/loader.py`.

## Pasos

1. **Verificar Configuración**
   - Asegurar que `config.yaml` contenga las secciones `data`, `data_contract`, `quality` y `financial_health` utilizadas en la fase de Laboratorio.

2. **Construir `src/loader.py` (Mapeo desde Lab a Prod)**
   - Trasladar la lógica contenida en `scripts/gen_discoverer.py` a la estructura de clase `DataLoader`.
   - **Mapeo de Funciones**:
     - `get_remote_max_date`, `download_data`, `sync_table` -> Métodos privados de sincronización incremental.
     - Lógica de las celdas 4 a 15 (Sanity Check, Estadísticas, Outliers, Nulos, Sentinelas, Contrato, Salud Financiera) -> Métodos dedicados dentro de `DataLoader`.
   - **Requisito de Salida**: El método `run()` o equivalente debe generar el reporte JSON final estrictamente en `outputs/reports/phase_01_discovery/`.

3. **Orquestar en `main.py`**
   - Actualizar `main.py` para instanciar y ejecutar `DataLoader` al inicio del pipeline.

4. **Crear Pruebas Unitarias (`tests/test_loader.py`)**
   - Implementar pruebas que validen la lógica de sincronización (mocking Supabase) y todas las reglas de salud de datos mapeadas.

5. **Ejecutar Pruebas y Validación (Gatekeeper)**
   - Ejecutar `pytest tests/test_loader.py`.
   - Verificar que se genere el reporte JSON en la ruta de producción establecida.

6. **Limpieza de Archivos Temporales**
   - Eliminar cualquier archivo `.log`, `.txt` o scripts `debug_*.py` generados durante el proceso.

