---
description: Automatiza la creación de la infraestructura del proyecto "Mis Buñuelos". Asegura que la jerarquía de directorios y los archivos base cumplan estrictamente con los estándares definidos en la habilidad de Arquitecto de Infraestructura MLOps.
---

# Workflow: Mago de Inicialización (Project Bootstrap Wizard)

Este flujo de trabajo es responsable de la creación física de la infraestructura del proyecto "Mis Buñuelos". Su objetivo es asegurar que la jerarquía de directorios y los archivos base cumplan estrictamente con los estándares definidos.

## 🛠️ Pasos de Ejecución (Setup Inicial)

### Paso 1: Creación de la Estructura de Directorios
* **Acción:** Generar la jerarquía de carpetas definida en el Skill `mlops_infrastructure_architect`.
* **Comando interno:** Crear de forma recursiva:
    * `data/01_raw`, `data/02_cleansed`, `data/03_features`, `data/04_processed`
    * `notebooks/`, `src/connectors/`, `tests/`
    * `experiments/phase_01_discovery/artifacts`, `experiments/phase_01_discovery/figures`
    * `experiments/phase_02_preprocessing/artifacts`, `experiments/phase_02_preprocessing/figures`
    * `experiments/phase_03_eda/figures`
    * `experiments/phase_04_features/artifacts`, `experiments/phase_04_features/figures`
    * `experiments/phase_05_backtesting/artifacts`, `experiments/phase_05_backtesting/figures`
    * `outputs/models`, `outputs/metrics`, `outputs/figures`, `outputs/forecasts`, `outputs/reports`

### Paso 2: Despliegue de Archivos Base (Scaffolding)
* **Acción:** Crear los archivos vacíos o con plantillas iniciales en `src/`.
* **Archivos a crear:**
    * `src/connectors/supabase_connector.py`
    * `src/loader.py`
    * `src/preprocessing.py`, `src/features.py`, `src/models.py`, `src/utils.py`.
    * `main.py` (Orquestador).
    * `.env.example` (Para las credenciales de Supabase).
    * `.env` (Archivo vacío para configuración local).
    * `notebooks/workbench.ipynb` (Notebook de trabajo temporal/scratchpad).

### Paso 3: Configuración y Entorno
* **Acción:** Inicializar los archivos de control del proyecto.
* **Tareas:**
    1. Crear un `config.yaml` base con las rutas de las carpetas recién creadas y parámetros globales.
    2. Generar un `requirements.txt` inicial con: `skforecast`, `pandas`, `numpy`, `supabase`, `python-dotenv`, `pyyaml`, `scikit-learn`, `matplotlib`, `seaborn`, `xgboost`, `lightgbm`.
    3. Crear un `.gitignore` estándar para Python que incluya explícitamente:
        - `.venv`
        - `.env`
        - `data/`
        - `notebooks/workbench.ipynb`

### Paso 4: Configuración del Entorno Python (Virtual Environment)
* **Acción:** Crear y configurar el entorno virtual de Python.
* **Requisitos:** Python versión **3.12.10**.
* **Comandos:**
    1. Crear entorno: `py -3.12 -m venv .venv` (Asegurar usar la versión 3.12.10).
    2. Activar entorno: `.venv\Scripts\activate`
    3. Instalación: `pip install -r requirements.txt`

### Paso 5: Validación de Estándares
* **Acción:** Verificar que toda la nomenclatura de carpetas y archivos esté en **Inglés**.
* **Skill requerida:** `mlops_infrastructure_architect` (para asegurar que el resultado coincida con el diseño).

---

## 🚦 Salida Esperada
Al finalizar, el agente debe presentar un árbol de directorios confirmado, el entorno virtual activo con librerías instaladas y confirmar que el proyecto está listo para la **Fase 1: Discovery & Audit**.
