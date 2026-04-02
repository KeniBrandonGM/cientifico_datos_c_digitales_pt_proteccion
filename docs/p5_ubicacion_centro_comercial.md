# P5 — Ubicación Óptima para el Centro Comercial Insignia

## Pregunta
> La dirección de la empresa desea dar el salto al mundo físico y necesita saber cuál es el mejor punto de la ciudad con mayores ventas para ubicar un centro comercial insignia que ofrezca nuestros mejores productos.

---

## Metodología

### Supuesto analítico
**"Mejor punto"** se define como el punto geográfico que **minimiza la distancia promedio ponderada a los clientes**, dando mayor peso a aquellos con mayor gasto histórico. La lógica de negocio es que el centro comercial debe estar lo más accesible posible para los clientes de mayor valor.

### Datos utilizados
| Dataset | Uso |
|---|---|
| `orders_dataset` | Filtro de órdenes `delivered` |
| `customers_dataset` | Ciudad, estado y zip code de cada cliente |
| `order_items_dataset` | Ingresos por orden (`price`, sin flete) |
| `geolocation_dataset` | Coordenadas lat/lng por zip code prefix |

### Criterio de selección de ciudad
Se evaluaron todas las ciudades por **ingresos totales** y **volumen de órdenes** (mismos supuestos de P1: solo órdenes `delivered`, ingresos = `price`).

---

## Paso 1 — Ciudad con mayores ventas

| Ciudad | Estado | Órdenes | Ingresos totales | Clientes únicos |
|---|---|---|---|---|
| **São Paulo** | **SP** | **15.045** | **R$ 1.859.556** | **14.528** |
| Rio de Janeiro | RJ | 6.601 | R$ 955.573 | 6.361 |
| Belo Horizonte | MG | 2.697 | R$ 346.039 | 2.606 |
| Brasilia | DF | 2.071 | R$ 295.814 | 2.013 |
| Curitiba | PR | 1.489 | R$ 205.999 | 1.434 |

**São Paulo** lidera de forma contundente en ambos criterios — ingresos casi **2 veces superiores** al segundo lugar (Río de Janeiro) y más del doble de órdenes. No existe ambigüedad en la elección.

---

## Paso 2 — Punto óptimo dentro de São Paulo

### Método: Centroide ponderado por ingresos
Se obtuvieron las coordenadas de los **15.043 clientes** de São Paulo cruzando su `zip_code_prefix` con el `geolocation_dataset` (promediando coordenadas por zip code cuando había múltiples entradas). Se aplicó un filtro de coordenadas válidas dentro de los límites geográficos de Brasil.

**Fórmula:**
```
lat_óptima = Σ(lat_i × ingresos_i) / Σ(ingresos_i)
lng_óptima = Σ(lng_i × ingresos_i) / Σ(ingresos_i)
```

### Resultado

| Método | Latitud | Longitud |
|---|---|---|
| Centroide simple (sin ponderar) | -23.571916 | -46.633620 |
| **Centroide ponderado por ingresos** | **-23.571436** | **-46.633771** |

> Ambos centroides son prácticamente idénticos, lo que indica que los clientes de alto gasto están distribuidos de forma homogénea en la ciudad — no existe una zona VIP concentrada que desplace el punto óptimo.

---

## Punto óptimo recomendado

```
Latitud:   -23.571436
Longitud:  -46.633771
```

Corresponde aproximadamente a la zona **Perdizes / Pompeia** en São Paulo — área central con alta accesibilidad.

### Cobertura del punto

| Métrica | Valor |
|---|---|
| Clientes base | 15.043 |
| Ingresos totales representados | R$ 1.859.232 |
| Distancia promedio al punto | 10.36 km |
| Distancia mediana al punto | 9.78 km |
| Radio para cubrir el 80% de clientes | **15.19 km** |

El 80% de la base de clientes de São Paulo se encuentra dentro de un radio de **~15 km** del punto recomendado.

---

## Visualización

Se generó un mapa interactivo (`outputs/p5_mapa_ubicacion.html`) que incluye:
- **Heatmap** de densidad de clientes ponderado por ingresos (muestra de 3.000 puntos)
- **Marcador rojo** en el punto óptimo recomendado
- **Marcador azul** en el centroide simple (referencia comparativa)
- **Círculo rojo** con el radio de cobertura del 80% de clientes (~15.19 km)

---

## Conclusión ejecutiva

La ciudad que maximiza el potencial del centro comercial es **São Paulo**, con una ventaja indiscutible sobre el resto del país. El punto óptimo de ubicación corresponde a la zona **Perdizes / Pompeia**, desde donde se cubre al 80% de la base de clientes en un radio de 15 km.

La coincidencia entre el centroide ponderado y el simple sugiere que no existe una zona de la ciudad que concentre desproporcionadamente a los clientes de mayor valor — lo que refuerza la elección de un punto central y accesible sobre una ubicación en zonas premium como Jardins o Itaim Bibi, que serían menos representativas del conjunto de clientes.

---

## Supuestos asumidos

1. **"Mejor punto"** = centroide geográfico ponderado por ingresos del cliente. Alternativas como el algoritmo de la mediana geométrica (Weber) ofrecerían una precisión matemática mayor pero resultados prácticamente equivalentes dado el tamaño de la muestra.
2. Las coordenadas se obtienen promediando todas las entradas del `geolocation_dataset` para un mismo zip code prefix — esto introduce una leve imprecisión a nivel de barrio, aceptable para una decisión estratégica de ubicación.
3. Solo se consideran órdenes con `order_status == 'delivered'` (mismo criterio que P1).
4. Los ingresos se calculan como `price` (sin `freight_value`), consistente con P1.
