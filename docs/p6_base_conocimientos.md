# Pregunta 6 — Base de Conocimientos Simulada

## Objetivo
Construir una base de conocimientos en formato JSON con 3 productos de los más vendidos (P1),
incluyendo descripciones atractivas y precios reales promedio del dataset.

## Productos seleccionados

| # | Categoría | Nombre comercial | Precio promedio | Unidades vendidas |
|---|-----------|-------------------|-----------------|-------------------|
| 1 | health_beauty | Kit de Belleza y Cuidado Personal Premium | R$ 130.28 | 9465 |
| 2 | bed_bath_table | Colección Hogar: Cama, Baño y Mesa | R$ 93.44 | 10953 |
| 3 | watches_gifts | Relojes y Regalos Exclusivos | R$ 199.04 | 5859 |

## Criterio de selección

Se eligieron 3 categorías que destacan en los rankings de P1:

- **health_beauty**: #1 en ingresos totales, #2 en volumen → producto estrella por rentabilidad.
- **bed_bath_table**: #1 en volumen, #3 en ingresos → producto estrella por demanda masiva.
- **watches_gifts**: #2 en ingresos pero NO está en el top 5 de volumen → alto ticket promedio,
  segmento premium/aspiracional, interesante para personalización del agente IA.

## Supuestos

- **Precios:** Se usó el precio promedio (`price`) de todas las unidades vendidas en órdenes
  con status `delivered`. No se incluye `freight_value` ya que es costo logístico, no precio del producto.
- **Descripciones:** Redactadas en español, orientadas a un agente conversacional de ventas.
  Son simuladas pero basadas en la naturaleza real de cada categoría.
- **Estructura JSON:** Incluye metadatos (id, tags, rango de precios, flag de destacado)
  pensados para que el agente de IA pueda filtrar y recomendar dinámicamente.

## Archivo generado

- `outputs/p6_base_conocimientos.json`
