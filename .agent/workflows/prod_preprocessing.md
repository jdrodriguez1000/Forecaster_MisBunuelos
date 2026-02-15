---
description: Refactorizar y Orquestar la Fase 2 (Preprocessing) de Notebook a Producción
---

# Flujo de Trabajo: Fase de Preprocesamiento en Producción (Refactorizar y Orquestar)

Este flujo de trabajo migra la lógica de limpieza, imputación y agregación validada en los experimentos representados en `scripts/gen_preprocessor.py` hacia el código base de producción en `src/preprocessor.py`.

## Pasos

1. **Construir `src/preprocessor.py` (Mapeo desde Lab a Prod)**
   - Trasladar la lógica secuencial contenida en `scripts/gen_preprocessor.py` a la estructura de clase `Preprocessor`.
   - **Mapeo de Funcionalidades**:
     - Carga de datos, validación de contrato, estandarización y esquema.
     - Limpieza de filas (deduplicación y filtros temporales).
     - Tratamiento de centinelas (Ceros/Nulos/-1).
     - **Completitud Temporal (Reindexing)**: Asegurar frecuencia 'D' o 'MS' sin huecos.
     - **Imputación de Negocio**: Lógica para Macro, Promos, Marketing y Ventas.
     - **Recálculo Financiero**: Sincronización de costos/ingresos tras imputaciones.
     - **Agregación y Unificación**: Resample a 'MS' y Join de fuentes.
     - **Regla de Oro (Anti-Data Leakage)**: Eliminación del mes en curso incompleto.
   - **Requisito de Salida**: Generar el reporte JSON extendido en `outputs/reports/phase_02_preprocessing/`.

2. **Orquestar en `main.py`**
   - Actualizar `main.py` para instanciar y ejecutar `Preprocessor` inmediatamente después del `DataLoader`.

3. **Crear Pruebas Unitarias (`tests/test_preprocessor.py`)**
   - Validar el contrato de datos, el reindexado temporal, la imputación de nulos y la agregación mensual.

4. **Validación y Limpieza (Gatekeeper)**
   - Ejecutar el pipeline completo: `python main.py`.
   - Verificar que se genere el reporte JSON en la ruta de producción establecida.
   - Eliminar archivos temporales y logs de debug.
