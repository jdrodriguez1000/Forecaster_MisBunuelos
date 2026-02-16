---
description: Defines the engineering standards, storage hierarchy, and QA protocols to ensure the project is reproducible, modular, and auditable under the Lab-to-Prod methodology.
---

# Skill: Arquitecto de Infraestructura MLOps (Mis Buñuelos)

Esta habilidad define los estándares de ingeniería, la jerarquía de almacenamiento y los protocolos de control de calidad para asegurar que el proyecto sea reproducible, modular y auditable bajo la metodología Lab-to-Prod.

## 📂 Estándar de Almacenamiento (Data Layers)
Garantiza la inmutabilidad y el orden del flujo de datos:
* **`data/01_raw/`**: Datos crudos de Supabase (Inmutables).
* **`data/02_cleansed/`**: Datos mensuales limpios tras la Fase 2 (Agregación MS).
* **`data/03_features/`**: Datasets intermedios con ingeniería de variables.
* **`data/04_processed/`**: Dataset final enriquecido y proyectado listo para `skforecast`.

## 🏗️ Arquitectura de Código y Calidad (QA)
Define el ecosistema de desarrollo siguiendo el ciclo: **Notebook -> Refactor -> Main -> Test**.

### Módulos de Producción (`src/`)
1. **`connectors/supabase_connector.py`**: Gestión de conexiones a Supabase y carga de variables de entorno.
2. **`loader.py`**: Encargado de cargar los datos desde la base de datos (Supabase).
3. **`preprocessor.py`**: Lógica de limpieza, tratamiento de centinelas y agregación mensual.
4. **`features.py`**: Ingeniería de variables (Novenas, Primas, etc.) y proyecciones macro $MA(2)$.
5. **`models.py`**: Entrenamiento, Backtesting rodante (Rolling) y generación de pronósticos.
6. **`utils.py`**: Helpers compartidos para logging, manejo de JSON y lectura de `config.yaml`.

### Capa de Validación (`tests/`)
Cada módulo en `src/` debe tener su espejo de pruebas unitarias para cerrar la fase:
* `test_loader.py`, `test_preprocessor.py`, `test_features.py`, `test_models.py`.
* **Herramienta**: Ejecución obligatoria vía `pytest`.

## 🤖 Protocolos de Comunicación y Configuración
* **Zero Hardcoding**: Absolutamente todos los parámetros (rutas, umbral de 36 meses, modelos, hiperparámetros) residen en `config.yaml`.
* **Conventional Commits**: Uso estricto de `feat:`, `fix:`, `refactor:`, `test:`, `chore:`.
* **Gestión de Entorno**: Aislamiento en `.venv`. Sincronización continua de `requirements.txt`.
* **Seguridad**: Credenciales de Supabase exclusivamente en `.env` (nunca versionadas en Git).

## 📊 Segregación y Organización de Salidas (Lab vs. Prod)

### 🔬 Entorno de Experimentación (`experiments/`)
Salidas exclusivas de la ejecución de **Notebooks**. Cada fase (`01` a `05`) tiene su carpeta propia:
* **`experiments/phase_0X_name/artifacts/`**: Reportes JSON generados por el laboratorio.
* **`experiments/phase_0X_name/figures/`**: Gráficas y visualizaciones exploratorias.

### 🏭 Entorno de Producción (`outputs/`)
Salidas oficiales de la ejecución de módulos **.py** y el orquestador **main.py**:
* **`outputs/reports/phase_0X_name/`**: Reportes JSON oficiales con estatus de validación y métricas.
* **`outputs/figures/phase_0X_name/`**: Gráficas oficiales (Feature Importance, Backtesting, etc.).
* **`outputs/models/`**: Binarios del modelo campeón (`.joblib`).
* **`outputs/forecasts/`**: Resultados de la predicción final de 6 meses.
* **`outputs/metrics/`**: Resumen comparativo de errores (WAPE/MAE) históricos.
