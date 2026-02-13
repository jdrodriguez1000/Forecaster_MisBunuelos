# Project Charter: Forecaster Mis Buñuelos

**Fecha:** 13 de Febrero de 2026  
**Cliente:** Mis Buñuelos  
**Proyecto:** Sistema de Pronóstico de Ventas (6 meses)

---

## 1. Resumen Ejecutivo
Mis Buñuelos, empresa líder en su sector, enfrenta desafíos significativos en la planificación de su demanda. Actualmente, los pronósticos de ventas son realizados manualmente por un comité de expertos, proceso que ha demostrado ser subjetivo, políticamente influenciable y propenso a errores (desviaciones de hasta el 25% en baja temporada y quiebres de stock en alta).

El objetivo principal es desarrollar un modelo de forecasting basado en datos, objetivo y automatizado, que sirva como herramienta de soporte a la toma de decisiones, reduciendo la incertidumbre y optimizando el inventario.

---

## 2. Objetivos del Negocio
1.  **Reducir el Error de Pronóstico:** Minimizar la brecha entre ventas reales y proyectadas (actualmente hasta 25% en meses bajos).
2.  **Eliminar Subjetividad:** Proveer "anclas" objetivas basadas en datos históricos para las discusiones del comité de expertos.
3.  **Optimizar Inventario:** Evitar quiebres de stock en temporada alta (Diciembre, Enero, Junio, Julio) y sobre-stock en temporada baja.

---

## 3. Alcance del Proyecto

### 3.1. Entregables
- Modelo de Machine Learning capaz de predecir las ventas mensuales de "Buñuelos" (unidades) para los próximos 6 meses.
- Pipeline de datos automatizado conectado a Supabase.
- Evaluación de modelos comparada contra un Baseline (Seasonal Naive).

### 3.2. Restricciones y Reglas de Negocio (Críticas)
- **Horizonte de Pronóstico:** 6 meses (Mes $t$ a $t+5$).
- **Lag de Información:** Al predecir el mes actual ($t$), **NO** se puede utilizar información de ventas del mes en curso, ya que estos datos son parciales. El modelo debe usar datos cerrados hasta el mes $t-1$.
- **Producto:** Foco exclusivo en el producto estrella "Buñuelos".

### 3.3. Comportamiento Histórico y Estacionalidad
- **Pandemia:** Caída significativa de ventas (Abril 2020 - Mayo 2021).
- **Promociones ("Pague 1, Lleve otro Gratis"):**
    - Ciclos anuales desde 2020: Abril-Mayo y Septiembre-Octubre.
    - Objetivo: Impulsar ventas en valles estacionales.
- **Picos de Demanda:**
    - **Meses:** Diciembre, Enero, Junio, Julio.
    - **Días:** Sábados, Domingos y Festivos.
    - **Fechas Especiales:** Quincenas (15 y 30), Primas (Jun/Dic), Novenas (16-23 Dic).

---

## 4. Estrategia de Datos

### 4.1. Fuentes de Información
El modelo se alimentará de 4 fuentes principales cargadas en Supabase:

| Archivo | Tabla Supabase | Granularidad | Contenido |
| :--- | :--- | :--- | :--- |
| `ventas_diarias.csv` | `ventasdiarias` | Diaria | Histórico de ventas (2018-2026), precios, costos. |
| `inversion_RRSS.csv` | `redessociales` | Diaria | Inversión en Facebook e Instagram. |
| `promocion.csv` | `promociondia` | Diaria | Flag de promoción (0/1). |
| `macro_colombia.csv` | `macroeconomia` | Mensual | IPC, TRM, Desempleo, etc. |

### 4.2. Ingeniería de Características
- Agregación mensual de variables diarias (suma de ventas, conteo de días promo).
- Generación de lags y ventanas móviles.
- Variables *dummy* para eventos especiales (Pandemia, Novenas, Primas).

---

## 5. Arquitectura Técnica

### 5.1. Stack Tecnológico
- **Lenguaje:** Python y Notebooks (.ipynb)
- **Librería de Forecasting:** `skforecast`
- **Estrategia:** `ForecasterDirect` (Modelos independientes por paso del horizonte).

### 5.2. Modelos Evaluados
Se competirá contra un **Baseline (Seasonal Naive)**. Los candidatos son:
1.  Ridge Regression
2.  Random Forest Regressor
3.  LGBMRegressor
4.  XGBRegressor
5.  GradientBoostingRegressor
6.  HistGradientBoostingRegressor

---

## 6. Criterios de Éxito
El proyecto se considerará exitoso si:
1.  El modelo seleccionado supera consistentemente al Baseline (Seasonal Naive) en métricas de error (RMSE/MAE) en el set de prueba.
2.  La herramienta es adoptada por el comité de expertos como insumo principal para sus proyecciones.
