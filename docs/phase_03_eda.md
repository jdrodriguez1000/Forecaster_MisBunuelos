# Reporte de Auditoría: Phase 03 - EDA
**Utilidad:** Interpretación del análisis exploratorio avanzado y validación de hipótesis de negocio.
**Fecha de Auditoría:** 2026-02-16
**Archivo Fuente:** phase_03_eda_20260215_175342.json
**Fecha de Creación Fuente:** 2026-02-15T17:53:40.498230
---

## 1. Resumen Ejecutivo
**Estado:** ✅ **APROBADO**

El análisis exploratorio de datos (EDA) confirma las hipótesis planteadas en el Project Charter. Se detectó una fuerte estacionalidad y variaciones significativas entre los conjuntos de entrenamiento, validación y prueba, lo que justifica el uso de la estrategia de backtesting rodante.

## 2. Lo Bueno (The Good)
* **Validación de Particiones:** Se aplicó una partición clara (Train: 73 meses, Val: 12 meses, Test: 12 meses), lo que permite evaluar el modelo en un ciclo anual completo.
* **Estadística Descriptiva:** Se observa una media de ~10,761 unidades mensuales en entrenamiento, con un incremento notable hacia el periodo de validación y test (~13,184 unidades), sugiriendo una tendencia de crecimiento anual.
* **Outliers Identificados:** Se detectaron outliers razonables (aprox. 6-8% en entrenamiento), principalmente asociados a temporadas de alto volumen de ventas.

## 3. Lo No Tan Bueno (The Bad)
* **Diferencia entre Splits:** Existe un salto estadístico entre el entrenamiento y el test (Drift). La media de ventas sube un 22% en el split de test, lo que podría dificultar la capacidad de generalización si no se usan las variables exógenas adecuadas.
* **Alta Volatilidad:** La desviación estándar es elevada en todos los splits, indicando que existen factores de choque (promociones o eventos) que causan saltos bruscos en la demanda.

## 4. Análisis de Gráficas e Hipótesis
* **Estacionalidad:** Las gráficas analizadas durante la fase confirman el pico de demanda en Diciembre y Enero, tal como se esperaba por las festividades.
* **Efecto Pandemia:** Se confirma visualmente la caída en el periodo 2020-2021, lo que refuerza la necesidad de la variable `is_pandemic` en la siguiente fase.
* **Variables Macro:** La TRM presenta una tendencia alcista constante que debe ser evaluada como predictor.

## 5. Recomendaciones
1. **Feature Engineering Necesario:** Es obligatorio crear variables dummy para Diciembre y Junio.
2. **Aislamiento de Pandemia:** Dado que el comportamiento es muy distinto, se recomienda no omitir la feature `is_pandemic` para que el modelo no intente aprender de ese ruido.
3. **Escalamiento:** Considerar escalamiento de datos para los modelos de regresión lineal (Ridge) debido a la magnitud de los ingresos e inversiones.
