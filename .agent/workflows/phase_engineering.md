---
description: Automatiza la creación del notebook `04_feature_engineering.ipynb` mediante un script generador estandarizado (Modo Turbo).
---

# Workflow: Fase 4 - Feature Engineering (Signals & Context)

Este flujo de trabajo ejecuta un script de Python que genera el notebook `notebooks/04_feature_engineering.ipynb` con la lógica de variables cíclicas, banderas de negocio y efectos retardados de marketing.

## 🛠️ Pasos de Ejecución

### Paso 1: Generación del Notebook
Ejecuta el script generador que crea el notebook de laboratorio.

// turbo
python scripts/gen_engineering.py

### Paso 2: Validación y Ejecución
El usuario debe abrir y ejecutar el notebook generado en `notebooks/04_feature_engineering.ipynb`. 
Este notebook producirá:
1.  **Dataset**: `data/03_features/master_features.parquet`.
2.  **Reporte**: `experiments/phase_04_feature_engineering/artifacts/phase_04_feature_engineering.json`.
3.  **Visuales**: Gráficas de validación en `experiments/phase_04_feature_engineering/figures/`.

### Paso 4: Limpieza de Archivos Temporales
* **Acción:** Eliminar cualquier archivo temporal generado durante la ejecución (`.py`, `.txt`, `.log`) que no forme parte del repositorio.
* **Comando Sugerido:** `Remove-Item -Path "notebooks/run_*.py", "notebooks/*.log", "notebooks/*.txt" -ErrorAction SilentlyContinue`
* **Motivo:** Mantener el entorno de notebooks limpio y evitar commits de scripts de ejecución temporal.
