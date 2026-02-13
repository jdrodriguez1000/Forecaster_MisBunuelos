---
description: Encapsulates expert domain knowledge on sales dynamics, seasonality, and mathematical projections specific to the Buñuelos business context.
---

# Skill: Experto en el Dominio de Pronóstico (Mis Buñuelos)

Esta habilidad dota al agente del conocimiento experto sobre las dinámicas de venta, estacionalidad cultural y proyecciones matemáticas específicas para el negocio de buñuelos.

## 1. 🏢 Contexto del Producto y Negocio
* **Producto Estrella:** Buñuelos.
* **Objetivo:** Pronosticar `total_unidades_entregadas` a 6 meses.
* **Comportamiento General:** El negocio presenta una fuerte estacionalidad marcada por festividades y ciclos de pago (quincenas/primas).

## 2. 🧠 Lógica de Proyección Macroeconómica
Para completar el dataset en el horizonte de 6 meses (donde no hay datos reales de variables exógenas), se debe implementar:
* **Algoritmo:** Promedio Móvil Recursivo de 2 meses ($PM_2$).
* **Fórmula:** $Value_{t} = (Value_{t-1} + Value_{t-2}) / 2$
* **Variables Sujetas:** `ipc_mensual`, `trm_promedio`, `tasa_desempleo`, `costo_insumos_index`, `confianza_consumidor`.

## 3. 📅 Ingeniería de Características (Business Features)

### A. Estacionalidad Mensual (Alta Temporada)
* **Meses Pico:** Junio, Julio, Diciembre y Enero.
* **Acción:** Variables binarias (dummys) para estos meses.

### B. Dinámica Promocional ("Pague 1, Lleve otro Gratis")
* **Vigencia:** Anualmente desde 2020.
* **Ciclo 1:** 1 de Abril al 31 de Mayo.
* **Ciclo 2:** 1 de Septiembre al 31 de Octubre.
* **Nota de Coexistencia:** Durante la promoción, el volumen total incluye tanto ventas promocionales como precio full.
* **Acción:** Flag binario `is_promo_season` para estos rangos de fechas.

### C. Eventos Especiales y Días Pico
* **Novenas Navideñas:** Incremento específico del **16 al 23 de Diciembre**.
* **Efecto Primas:** Días de pago aproximados en **Junio y Diciembre** (rango 15-20).
* **Efecto Quincena:** Días 15 y 30/31 de cada mes.
* **Días de la Semana:** Sábados y Domingos son los de mayor venta.
* **Festivos:** Se deben homologar estadísticamente a un **Sábado** (Trigger de alta demanda).

## 4. 📉 Comportamiento Histórico Crítico
* **Anomalía Pandemia (Outlier):** Período crítico de **Abril 2020 a Mayo 2021**.
* **Acción:** Crear feature `is_pandemic` para aislar este comportamiento atípico y evitar sesgar el pronóstico futuro.

## 5. 🧮 Configuración del Motor skforecast
* **Tipo de Forecaster:** `ForecasterDirect` (Modelos independientes).
* **Estrategia de Lags:** Experimentación inicial 1 a 12 meses.
* **Exógenas:** Todas las variables de calendario y macroeconómicas deben ser forzadas como exógenas futuras (usando la proyección $PM_2$ para las macros).
