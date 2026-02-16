# Auditoría de Calidad: Fase 1 - Data Discovery

## 1. Resumen de Ejecución
- **Timestamp**: 2026-02-15T17:32:31.878269
- **Status**: ✅ COMPLETO
- **Insumos**: Tablas crudas desde Supabase

## 2. Métricas de Extracción (Download Details)
| Tabla | Filas | Registro |
| :--- | :--- | :--- |
| `ventas_diarias` | 2963 | 2026-02-15 17:32 |
| `redes_sociales` | 2963 | 2026-02-15 17:32 |
| `promocion_diaria` | 2963 | 2026-02-15 17:32 |
| `macro_economia` | 98 | 2026-02-15 17:32 |

## 3. Calidad de Datos (Técnica)
- **Rango Temporal**: 2018-01-01 a 2026-02-10.
- **Detección de Nulos**: 0 nulos detectados en las columnas temporales.
- **Valores Centinela**: Se detectó el valor `999` en la columna `id` (1 ocurrencia), el cual requiere limpieza en la siguiente fase.
- **Alta Cardinalidad**: Las columnas `fecha` e `id` presentan un ratio de 1.0 (esperado para fecha).
- **Cero Varianza**: No se detectaron columnas con varianza cero.

## 4. Auditoría de Salud Financiera (Reglas de Negocio)
| Regla | Descripción | Status |
| :--- | :--- | :--- |
| `rule_2_1` | Integridad de Unidades (Normal + Promo = Total) | ✅ PASS |
| `rule_2_2` | Igualdad Promo Pagada vs Bonificada | ✅ PASS |
| `rule_2_3` | Integridad de Margen (Precio > Costo) | ✅ PASS |
| `rule_2_4` | Cálculo de Utilidad | ✅ PASS |
| `rule_2_5` | Cálculo de Ingresos | ✅ PASS |
| `rule_2_6` | Cálculo de Costo Total | ✅ PASS |
| `rule_2_7` | Valores No Negativos | ✅ PASS |

## 5. Validación de Contrato de Datos
- **Status**: ✅ PASS
- **Issues en Notebook**: `Extra columns: {'id'}`. Se recomienda remover la columna `id` en la fase de preprocesamiento ya que no añade valor predictivo.

## 6. Conclusión de Fase
La extracción es exitosa y los datos mantienen la integridad financiera requerida. La estructura es consistente con lo esperado para proceder al preprocesamiento.
