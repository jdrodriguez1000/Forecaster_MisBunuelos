---
description: Refactorizar y Orquestar la Fase 2 (Preprocessing) de Notebook a Producción
---

# Flujo de Trabajo: Fase de Preprocesamiento en Producción (Refactorizar y Orquestar)

Este flujo de trabajo migra la lógica de limpieza, imputación y agregación validada en `notebooks/02_preprocessing.ipynb` (generado por `scripts/gen_preprocessor.py`) al código base de producción en `src/preprocessor.py`.

## Pasos

1. **Crear `src/preprocessor.py` (Refactor)**
   - El objetivo es trasladar la lógica secuencial del notebook a una clase robusta `Preprocessor` o funciones modulares.
   - **Funcionalidades Clave a Implementar (basadas en el notebook)**:
     - **Carga de Datos**: Leer parquets desde `data/01_raw/`.
     - **Validación de Contrato**: Verificar columnas requeridas vs `config.yaml` antes de procesar.
     - **Estandarización**: Aplicar `rename_map` y selección de columnas (Schema Enforcement).
     - **Limpieza de Filas**: Deduplicación (exacta y temporal) y filtros de fecha (`min_date`).
     - **Tratamiento de Centinelas**: Reemplazo de valores numéricos (ej: -1, 999) y texto por `NaN`.
     - **Completitud Temporal (Reindexing)**: **CRÍTICO**. Asegurar frecuencia diaria/mensual sin huecos reindexando con `pd.date_range`.
     - **Imputación de Negocio**:
       - *Macro*: Rolling mean shift.
       - *Promo*: Lógica de meses promo (4, 5, 9, 10).
       - *Marketing*: Asignación de campañas y ciclos; interpolación de inversiones activas.
       - *Ventas*: Imputación lineal para `total_unidades_entregadas`, desglose de residuales.
     - **Recálculo Financiero**: Si `recalc_financials=True`, recalcular costos, ingresos y utilidad para filas imputadas.
     - **Agregación Mensual**: Resample a 'MS' usando reglas específicas (ej: `sum`, `first`).
     - **Unificación (Merge)**: Join de ventas, marketing, promo y macro en un `master_monthly`.
     - **Exportación**: Guardar `data/02_cleansed/master_monthly.parquet` y generar reporte JSON.

2. **Orquestar en `main.py`**
   - Actualizar `main.py` para importar el módulo `preprocessor`.
   - Insertar la ejecución de la Fase 2 inmediatamente después de la Fase 1 (Discovery).
   - Asegurar que la configuración (`config.dict`) se pase correctamente.

3. **Crear Pruebas Unitarias (`tests/test_preprocessor.py`)**
   - Crear validaciones para:
     - **Contrato de Datos**: Fallo si faltan columnas críticas.
     - **Reindexado**: Verificar que no existan huecos de fechas en el output.
     - **Imputación**: Verificar que los nulos en ventas sean 0 tras el proceso.
     - **Agregación**: Verificar que el output tenga frecuencia 'MS' y `shape` esperado.
     - **Integración**: Ejecución completa del pipeline con datos mock.

4. **Validación y Limpieza**
   - Ejecutar el pipeline completo: `python main.py`.
   - Verificar la creación del reporte en `outputs/reports/phase_02_preprocessing/`.
   - Eliminar archivos temporales generados durante el desarrollo.
