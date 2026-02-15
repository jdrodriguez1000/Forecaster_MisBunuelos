---
description: Automatiza la creación del notebook `03_eda.ipynb` mediante un script generador estandarizado (Modo Turbo).
---

# Workflow: Fase 3 - Análisis Exploratorio de Datos (Anti-Data Leakage)

Este flujo de trabajo ejecuta el script generador que crea el notebook de EDA aplicando estrictamente las reglas de **Anti-Data Leakage** ("Only Eyes on the Past") y partición temporal automática.

## 🛠️ Pasos de Ejecución

### Paso 1: Generación del Notebook (Turbo)
Se ejecuta el script `scripts/gen_eda.py` que:
1.  Lee `config.yaml` para parámetros y fechas.
2.  Genera las celdas de visualización con estilo "Rich Aesthetics".
3.  Crea la lógica de partición Train/Val/Test.

// turbo
python scripts/gen_eda.py

### Paso 2: Validación Visual
El usuario debe abrir `notebooks/03_eda.ipynb`, ejecutar las celdas y registrar las conclusiones de negocio al final del mismo.

### Paso 3: Limpieza
(Opcional) Eliminar archivos temporales tras la confirmación de hallazgos.
