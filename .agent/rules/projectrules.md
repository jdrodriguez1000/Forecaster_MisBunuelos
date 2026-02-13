---
trigger: always_on
---

# Project Rules: Pronóstico Buñuelos "Mis Buñuelos"

Este archivo constituye la autoridad máxima de restricciones cognitivas y técnicas para el proyecto. Todo agente o colaborador debe asegurar el cumplimiento estricto de estas reglas antes de ejecutar cualquier Skill o Workflow.

---

## 1. 🎯 Restricciones de Dominio y Negocio
* **Variable Objetivo:** `total_unidades_entregadas` (Forecasting de demanda mensual).
* **Regla de Oro (Anti-Data Leakage):** El entrenamiento para el mes $X$ debe detenerse estrictamente en el cierre del mes $X-1$. Queda prohibido el uso de información parcial o total del mes en curso para predecir el futuro.
* **Horizonte de Predicción:** El sistema debe generar siempre un pronóstico de 6 meses (mes actual $X$ hasta $X+5$).
* **Métricas de Éxito:** El modelo final es válido solo si supera al baseline *Seasonal Naive* y mantiene un **WAPE < 30%**.

## 2. 🏗️ Arquitectura de Software y Estándares
* **Estrategia de Modelado:** Uso obligatorio de la librería `skforecast` mediante la estrategia `ForecasterDirect`.
* **Batería de Modelos Autorizados:** Solo se permite la experimentación y competencia entre:
    * `Ridge`, `RandomForestRegressor`, `LGBMRegressor`, `XGBRegressor`, `GradientBoostingRegressor` y `HistGradientBoostingRegressor`.
* **Configuración:** Prohibido el uso de valores "hardcoded". Rutas, hiperparámetros, fechas de corte y nombres de variables deben residir en `config.yaml`.
* **Idioma:** Código y estructura de archivos en **Inglés**; contexto y reglas de negocio en **Español**.
* **Persistencia:** La fuente de verdad histórica es **Supabase (PostgreSQL)**.

## 3. 🔬 Rigor en Ciencia de Datos y Validación
* **Estrategia de Partición (Backtesting):** Se debe aplicar un esquema de validación cruzada temporal con lógica rodante (Rolling Window):
    * **Test:** Últimos 12 meses del dataset.
    * **Validación:** 12 meses inmediatamente anteriores al bloque de Test.
    * **Entrenamiento:** Todo el histórico restante previo a Validación.
* **Umbral de Datos Mínimos:** El pipeline debe validar la existencia de al menos **36 meses** de datos históricos antes de proceder con el modelado.
* **Tratamiento de Exógenas Futuras:** Las variables macroeconómicas para el horizonte de 6 meses deben proyectarse mediante **Promedio Móvil Recursivo de 2 meses**.
* **Precedencia Metodológica:** No se permite la ejecución de fases de modelado sin un reporte previo de "Auditoría de Salud de Datos" (detección de nulos y valores centinela).
* **Reproducibilidad:** Se debe garantizar un comportamiento determinista utilizando la semilla global `random_state=42`.

## 4. ⚙️ Ciclo de Desarrollo Obligatorio (Metodología Lab-to-Prod)
Toda fase técnica (excepto la Fase 3: EDA) debe completar satisfactoriamente este ciclo para ser considerada "Cerrada":
1. **Lab:** Experimentación y validación de lógica en `notebooks/`.
2. **Refactor:** Traslado de la lógica validada a módulos modulares `.py` en `src/`.
3. **Orchestrate:** Integración de los módulos en el orquestador central `main.py`.
4. **Test:** Creación y ejecución exitosa de pruebas unitarias en `tests/`.
5. **Close:** Emisión del reporte JSON de trazabilidad tras la validación de `pytest`.

## 5. 📂 Segregación de Salidas (Ambientes Lab vs. Prod)
Queda estrictamente prohibido mezclar salidas de experimentación con las de producción:
* **Entorno Lab (Notebooks):** Todas las salidas deben dirigirse a `experiments/phase_0X_name/`.
    * Los reportes JSON de experimentación van en la subcarpeta `artifacts/` y su nombre inicia por phase_0X_name.json.
    * Toda visualización o gráfica exploratoria va en la subcarpeta `figures/`.
* **Entorno Prod (Módulos .py y main.py):** Todas las salidas oficiales deben dirigirse a `outputs/`.
    * Los reportes JSON finales se guardan en `outputs/reports/` dentro de una subcarpeta con el nombre de la fase.
    * Toda gráfica o visualización oficial se guarda en `outputs/figures/` dentro de una subcarpeta con el nombre de la fase.
    * Los binarios de modelos, pronósticos y métricas van en sus respectivas carpetas raíz de `outputs/`.

## 6. 📤 Protocolo de Entregables y Trazabilidad
* **Reportes de Fase:** Cada proceso debe generar un artefacto `.json` con el encabezado obligatorio:
    ```json
    {
      "phase": "Nombre de la fase",
      "timestamp": "ISO 8601",
      "description": "Breve resumen de la ejecución y status de pruebas"
    }
    ```
* **Gestión de Entorno:** Ejecución obligatoria dentro de ambiente virtual `.venv` y mantenimiento riguroso de `requirements.txt`.
* **Aprobación de Fase (Gatekeeper):** Queda estrictamente prohibido avanzar a una nueva fase del proyecto sin la **aprobación explícita y completa** del usuario sobre los entregables de la fase actual.
