---
description: Refactorizar y Orquestar la Fase 4 (Feature Engineering) de Notebook a Producción
---

# Flujo de Trabajo: Fase de Ingeniería de Variables en Producción (Refactorizar y Orquestar)

Este flujo de trabajo migra la lógica de enriquecimiento de datos y creación de variables estratégicas validada en los experimentos representados en `scripts/gen_engineering.py` hacia el código base de producción en `src/features.py`.

## Pasos

1. **Construir `src/features.py` (Mapeo desde Lab a Prod)**
   - Trasladar la lógica secuencial contenida en `scripts/gen_engineering.py` a la estructura de clase `FeatureEngineer`.
   - **Mapeo de Funcionalidades**:
     - **Variables Cíclicas**: Implementación de Seno/Coseno para `month`, `quarter` y `semester`.
     - **Banderas de Negocio**: Lógica binaria para eventos críticos (`is_novenas`, `is_primas`, `is_pandemic`).
     - **Marketing Estratégico (Lags)**: Generación de retardos temporales (Lag 1) para inversiones.
     - **Visualizaciones de Producción**: Generación de gráficas de validación de eventos, ciclos y heatmap de correlaciones.
   - **Requisito de Salida**: 
     - Reporte JSON en `outputs/reports/phase_04_feature_engineering/`.
     - Gráficas PNG en `outputs/figures/phase_04_feature_engineering/`.

2. **Orquestar en `main.py`**
   - Actualizar `main.py` para instanciar y ejecutar `FeatureEngineer` inmediatamente después del `Preprocessor`.
   - Asegurar que la fase sea accesible mediante el argumento `--phase engineering`.

3. **Crear Pruebas Unitarias (`tests/test_features.py`)**
   - Validar cálculos trigonométricos de variables cíclicas.
   - Verificar la correcta asignación de banderas binarias según fechas calendario.
   - Confirmar que los retardos (lags) desplazan los datos correctamente y aplican el relleno configurado.

4. **Validación y Limpieza (Gatekeeper)**
   - Ejecutar el pipeline de ingeniería: `python main.py --phase engineering`.
   - Verificar la existencia del reporte JSON y las **3 gráficas de validación** en las rutas de producción.
   - Ejecutar el set de pruebas: `pytest tests/test_features.py`.
   - Eliminar scripts de debug y archivos temporales.
