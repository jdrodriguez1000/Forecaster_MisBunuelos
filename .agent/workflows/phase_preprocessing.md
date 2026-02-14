---
description: Automatiza la creación del notebook `02_preprocessing.ipynb` mediante un script generador estandarizado.
---

# Workflow: Fase 2 - Preprocesamiento Robusto (Cleaning & Aggregation)

Este flujo de trabajo ejecuta un script de Python que genera el notebook `notebooks/02_preprocessing.ipynb` con toda la lógica de validación, limpieza, imputación y agregación definida en las reglas del proyecto.

## 🛠️ Pasos de Ejecución

### Paso 1: Generación del Notebook
Ejecuta el script generador que crea el notebook con la lógica encapsulada.

// turbo
python scripts/gen_wf_preprocessing.py

### Paso 2: Validación y Ejecución
El notebook generado en `notebooks/02_preprocessing.ipynb` debe ser ejecutado para producir los datasets limpios y el reporte.

### Paso 3: Limpieza
Eliminar archivos temporales si los hubiera.
