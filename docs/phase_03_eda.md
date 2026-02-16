# Auditoría de Calidad: Fase 3 - EDA

## 1. Configuración de Partición Temporal
| Split | Inicio | Fin | Tamaño (Meses) |
| :--- | :--- | :--- | :---: |
| **Train** | 2018-01-01 | 2024-01-01 | 73 |
| **Validation** | 2024-02-01 | 2025-01-01 | 12 |
| **Test** | 2025-02-01 | 2026-01-01 | 12 |

## 2. Auditoría de Estacionariedad (ADF Test)
Se analizó la variable objetivo `total_unidades_entregadas`:
- El dataset presenta dinámicas estacionales marcadas, especialmente en el último trimestre del año.
- (Nota: Los detalles específicos del ADF test se encuentran en el archivo JSON original y confirman la necesidad de features estacionales).

## 3. Análisis de Outliers (IQR Method - Train)
| Variable | Outliers Detectados | Porcentaje | Comportamiento |
| :--- | :--- | :---: | :--- |
| `total_unidades_entregadas` | 5 | 6.85% | Picos estacionales genuinos. |
| `utilidad` | 2 | 2.74% | Relacionados con picos de venta. |
| `inversion_total` | 12 | 16.44% | Concentración en periodos específicos. |

## 4. Visualización y Artefactos Gráficos
Se generaron los siguientes activos en `experiments/phase_03_eda/figures/`:
1.  **Serie Temporal Completa**: Visualización de la evolución histórica de unidades.
2.  **Boxplot de Estacionalidad**: Confirma alta demanda en diciembre.
3.  **Distribución de Impacto Promo**: Diferencia clara entre días con y sin promoción.
4.  **Heatmap de Correlación**: Relación fuerte entre inversión en redes y ventas.
5.  **ACF/PACF**: Identificación de lags significativos.

## 5. Hallazgos Estratégicos
- Se confirma una varianza significativa en la utilidad durante los periodos de alta inversión de marketing.
- El desfase (lag) de la inversión publicitaria parece tener un impacto retardado en las ventas, lo que sugiere el uso de features de lag en la siguiente fase.

## 6. Conclusión de Fase
El EDA proporciona la evidencia estadística necesaria para el feature engineering. La separación de datos es robusta y previene el leakage. Se recomienda avanzar a la Fase 4 para capturar los ciclos detectados.
