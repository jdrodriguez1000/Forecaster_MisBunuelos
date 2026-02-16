---
description: Audits the forecasting pipeline phases, validating technical results against business goals, identifying risks, and generating executive reports in the docs/ folder.
---

# Skill: Auditor de Calidad del Pronóstico (Forecasting Quality Auditor)

Esta habilidad dota al agente de la capacidad crítica para evaluar el progreso y la calidad de las fases de ciencia de datos, asegurando que los experimentos en el laboratorio (Lab) cumplan con los estándares de ingeniería y los objetivos de negocio de "Mis Buñuelos".

## 1. 🎯 Objetivos de la Auditoría
* **Validación de Negocio**: Verificar que los hallazgos técnicos se alineen con el `Project_Charter.md` (ej. detección de estacionalidad en Diciembre).
* **Cumplimiento Normativo**: Asegurar el respeto estricto a las `projectrules.md` (ej. regla de oro anti-leakage y umbral de 36 meses).
* **Análisis de Riesgos**: Identificar anomalías en los datos o resultados mediocres (WAPE > 30%) que pongan en riesgo el éxito del proyecto.
* **Calidad de Documental**: Transformar archivos JSON técnicos en informes narrativos Markdown legibles para humanos.

## 2. 📂 Alcance y Fuentes de Información
El auditor debe leer y analizar los siguientes componentes antes de emitir un juicio:
* **Contexto Estratégico**: `Project_Charter.md` y `projectrules.md`.
* **Conocimiento Experto**: Habilidades de dominio, pipeline e infraestructura existentes.
* **Artefactos Técnicos**: 
    - Archivos `.json` en `experiments/phase_0X_name/artifacts/`.
    - Gráficas en `experiments/phase_0X_name/figures/`.

## 3. 🔍 Lógica de Evaluación por Fase

### Phase 01: Discoverer (Discovery & Audit)
* **Check Crítico**: Validar la existencia de `phase_01_discovery.json`. Si no existe, estado **CRÍTICO**.
* **Análisis de Rigor**: 
    - **Volumen**: Verificar cobertura temporal (Min 36 meses, reportar meses reales).
    - **Salud Temporal**: Validar `gaps_count`. Cero gaps es indicador de alta calidad.
    - **Integridad Financiera**: Revisar el cumplimiento de las 7 reglas de negocio (Unidades, Ingresos, Costos, Utilidad).
    - **Cardinalidad**: Identificar columnas ID y fecha mediante ratios de unicidad.
* **Análisis "Beyond the Skills"**: Identificar proactivamente columnas extra contratuales, validaciones de tipos automáticas o auditorías de algoritmos financieros integrales.
* **Identificación de Brechas (The Gaps)**: Reportar explícitamente qué no se validó (ej. outliers macro no explicados, falta de visualización de salud o ineficiencia en sincronización).

### Phase 02: Preprocessing (Cleansing)
* **Check Crítico**: Validar la existencia de `phase_02_preprocessing.json`. Si no existe, estado **CRÍTICO**.
* **Análisis de Rigor**: 
    - **Limpieza**: Validar deduplicación y corrección de centinelas (999, -1).
    - **Reindexación**: Confirmar que los huecos temporales fueron rellenados antes de agregar.
    - **Agregación**: Verificar frecuencia `MS` y consistencia de sumas/promedios.
    - **Anti-Leakage**: Certificar que se recortó el mes en curso (no debe haber datos del mes actual).
* **Análisis "Beyond the Skills"**: Identificar limpiezas personalizadas de snake_case, estandarización de tipos de datos o recálculos financieros preventivos.
* **Identificación de Brechas (The Gaps)**: Reportar si quedaron nulos residuales, si se ignoraron variables clave o si no se validaron límites físicos (ej. valores negativos).

### Phase 03: EDA (Exploratory Data Analysis)
* **Inteligencia de Archivos**: 
    - Identificar el JSON más reciente en `experiments/phase_03_eda/artifacts/`.
    - Listar archivos de imagen (`.png`, `.jpg`) en `experiments/phase_03_eda/figures/` analizados.
* **Análisis de Rigor**: 
    - **Límites**: Validar partición Train/Val/Test sin solapamiento (Leakage).
    - **Estadística**: Reportar significancia del Test de Dickey-Fuller y drift detectado entre eras.
* **Componentes Estratégicos (Mandatorios en Reporte)**:
    - **Análisis de Gráficas**: Explicar los hallazgos visuales y sus implicaciones directas en el diseño del modelo.
    - **Variables Exógenas**: Recomendar nuevas variables basadas en el EDA y el `Project_Charter.md` (ej. Binarias para Novenas/Primas/Pandemia). Justificar cada una.
    - **Grilla de Rezagos y Ventanas**: Proponer Lags (ej. 1, 2, 12) y Moving Windows (ej. 3, 6) con base en la autocorrelación observada.
    - **Transformaciones**: Decidir si se requiere Diferenciación (estacionariedad), Logaritmo o Yeo-Johnson (varianza/normalidad). Justificar.
    - **Estrategia de Rezagos y Ventanas (Lags/Windows)**: Proponer una cuadrícula (grid) de rezagos (ej. [1, 12]) y ventanas móviles (ej. [3, 6, 12]) basada en el análisis de ACF/PACF visual.
    - **Triangulación de Exógenas**: Validar recomendaciones de variables exógenas mediante la triangulación de:
        1. **Project Charter** (Contexto de negocio).
        2. **Resultados JSON** (Correlaciones y uplifts estadísticos).
        3. **Figuras/Gráficas** (Patrones visuales y heterocedasticidad).
    - **Relaciones de Impacto (Simple Terms)**: Traducir correlaciones y uplifts a lenguaje de negocio sencillo (ej. "Si X sube, Y tiende a bajar"). Explicar la sensibilidad del target ante cambios en exógenas.
    - **Función de Pesos (Eras)**: Definir al menos **3 Eras** históricas (ej. Pre-Pandemia, Pandemia, Recuperación) y proponer pesos para priorizar información reciente. Justificar el esquema.
* **Análisis "Beyond the Skills"**: Hallazgos de correlaciones inesperadas, análisis de lags de marketing profundos o identificación de shocks exógenos.
* **Identificación de Brechas (The Gaps)**: Reportar falta de visualizaciones específicas o análisis de causalidad incompleto.

### Phase 04: Featurer (Feature Engineering)
* **Check Crítico**: Validar la existencia de `phase_04_features.json`. Si no existe, estado **CRÍTICO**.
* **Análisis**: 
    - Verificar creación de variables clave: `is_promo_season`, `is_pandemic`, `novenas`, `primas`.
    - Validar proyección de exógenas mediante $MA(2)$.

## 4. 📝 Estructura de Salida (Reportes en docs/)
Cada auditoría debe generar un archivo con el siguiente formato:

### Encabezado Obligatorio
```markdown
# Reporte de Auditoría: [Nombre de la Fase]
**Utilidad:** [Descripción breve de para qué sirve este reporte]
**Fecha de Auditoría:** [Fecha actual YYYY-MM-DD HH:MM:SS]
**Archivo Fuente:** [Nombre del JSON analizado]
**Fecha de Creación Fuente:** [Fecha extraída del JSON o Metadatos]
---
```

### Cuerpo del Reporte
1. **Resumen Ejecutivo**: ¿La fase es APROBADA o RECHAZADA para producción? (Estado del pipeline).
2. **Lo Bueno (The Good)**: Fortalezas técnicas y de negocio encontradas.
3. **Lo No Tan Bueno (The Bad & Riesgos)**: Hallazgos negativos, centinelas, esparsidad o riesgos de sesgo.
4. **Auditoría Técnica Detallada**: Tablas de consumo, inventario de registros y salud de variables críticas.
5. **Valor Agregado (Beyond the Skills)**: Acciones proactivas del sistema que fortalecen la fase.
6. **Estrategia de Ingeniería de Features**: Propuesta técnica de Lags, Ventanas Móviles y transformaciones (ej. Log) basadas en la evidencia analizada.
7. **Triangulación de Exógenas**: Tabla o sección que justifique la inclusión de variables (Novenas, Primas, etc.) cruzando Charter, JSON y Gráficas.
8. **Relaciones de Impacto (Simple Terms)**: Sección dedicada a explicar en términos sencillos cómo reacciona el target ante cambios en otras variables (Marketing, Macro, Promos).
9. **Brechas y Pendientes (The Gaps)**: Lo que no se hizo, se postergó o falta validar.
10. **Recomendaciones Estratégicas**: Pasos concretos para mitigar riesgos en las siguientes fases.

## 5. 🛑 Protocolo de Errores
Si una fase no tiene su archivo JSON correspondiente, el auditor debe:
1. Detener el proceso de generación del reporte Markdown para esa fase.
2. Emitir un mensaje de sistema reportando el estado **CRÍTICO**.
3. Requerir la implementación y ejecución del notebook/proceso faltante.
