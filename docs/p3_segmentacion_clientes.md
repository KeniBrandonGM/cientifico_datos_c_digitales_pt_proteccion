# P3 — Segmentación de Clientes

## Pregunta
> Diseña y ejecuta una segmentación de clientes que permita a nuestro equipo de marketing distinguir claramente a los "clientes fieles" de los compradores esporádicos o en riesgo de abandono.

---

## Metodología

### Framework base: RFM
Para construir el espacio de segmentación se utilizó el framework estándar de la industria **RFM**, calculado a nivel de `customer_unique_id`

| Variable | Definición | Cálculo |
|---|---|---|
| **Recency (R)** | Días desde la última compra | Fecha referencia (2018-08-30) − fecha de última orden |
| **Frequency (F)** | Número total de órdenes | Count de `order_id` por cliente |
| **Monetary (M)** | Gasto total acumulado | Suma de `price` (sin `freight_value`) |

**Universo analizado:** 93.358 clientes únicos con al menos una orden `delivered`.

---

## Decisión de enfoque: por qué no K-Means puro sobre RFM

Antes de aplicar el algoritmo final se exploró K-Means estándar sobre las 3 variables RFM normalizadas. El análisis reveló un problema estructural del dataset:

| Métrica | Valor |
|---|---|
| Clientes con frequency = 1 | 90.557 (**97.0%**) |
| Clientes con frequency >= 2 | 2.801 (3.0%) |
| Clientes con frequency >= 3 | 228 (0.2%) |

Con el 97% de clientes en F=1, la variable **Frequency tiene varianza casi nula** — K-Means no puede usarla para separar grupos. En su lugar, el algoritmo segmentaba exclusivamente por Monetary (que sí tiene outliers grandes), produciendo clusters sin utilidad para distinguir fieles de esporádicos.

### Enfoque adoptado: segmentación híbrida en dos niveles

Se diseñó un enfoque que combina **regla de negocio + K-Means**, garantizando que la frecuencia de compra sea el discriminador principal de fidelidad:

```
Nivel 1 — Regla de negocio sobre frecuencia:
  · frequency >= 2  →  "Comprador recurrente"  (3.0%)
  · frequency = 1   →  "Comprador único"       (97.0%)

Nivel 2 — K-Means sobre R + M dentro de cada grupo:
  · Recurrentes: separar activos vs en riesgo por recency y monetary
  · Únicos: separar alto valor vs común por monetary
```

### Normalización y validación
- Normalización: **RobustScaler** (resistente a outliers de monetary)
- Variables de clustering: **Recency + Monetary** (Frequency ya actúa en el Nivel 1)
- K óptimo: determinado por **Silhouette Score** sobre rango k=2 a k=6

| Grupo | K evaluados | K óptimo | Silhouette |
|---|---|---|---|
| Recurrentes (n=2.801) | 2–5 | **2** | 0.6989 |
| Únicos (n=90.557) | 2–6 | **2** | 0.8196 |

---

## Resultados — 4 Segmentos de Clientes

| Segmento | Clientes | % | Recency media | Freq media | Gasto medio |
|---|---|---|---|---|---|
| Esporadico_Comun | 87.550 | 93.8% | 238 días | 1.0 | R$ 109 |
| Alto_Valor_Durmiente | 3.007 | 3.2% | 246 días | 1.0 | R$ 981 |
| Cliente_Fiel_En_Riesgo | 2.619 | 2.8% | 222 días | 2.1 | R$ 205 |
| Cliente_Fiel_Activo | 182 | 0.2% | 202 días | 2.5 | R$ 1.047 |

---

## Descripción de cada segmento

### Cliente_Fiel_Activo *(el segmento de oro)*
- **Perfil:** Recompran con frecuencia, son los más recientes y los de mayor gasto.
- **Características:** 2.5 órdenes en promedio, gasto medio de R$ 1.047, último contacto hace ~202 días.
- **Acción de marketing:** Programa de fidelización y beneficios exclusivos. Son el 0.2% de la base pero representan el mayor valor a largo plazo. Hay que retenerlos y premiarlos.

### Cliente_Fiel_En_Riesgo *(retención urgente)*
- **Perfil:** Han recomprado pero llevan ~222 días sin actividad.
- **Características:** 2.1 órdenes en promedio, gasto medio de R$ 205.
- **Acción de marketing:** Campaña de reactivación con incentivo (descuento, oferta personalizada). Son fieles comprobados que están enfriándose — actuar antes de perderlos definitivamente.

### Alto_Valor_Durmiente *(alto potencial de reactivación)*
- **Perfil:** Compraron una única vez pero con un ticket muy alto (R$ 981 de media vs R$ 109 del segmento común).
- **Características:** 1 sola compra, gasto 9 veces mayor que el esporádico común.
- **Acción de marketing:** Campaña de segunda compra segmentada por categoría de su primera compra. La magnitud de su gasto sugiere capacidad adquisitiva alta — el objetivo es convertirlos en recurrentes.

### Esporadico_Comun *(el grueso del negocio)*
- **Perfil:** Una sola compra a precio estándar. Representa el 93.8% de la base de clientes.
- **Características:** Gasto medio de R$ 109, recency de 238 días.
- **Acción de marketing:** Campañas de activación masiva y de bajo costo (email marketing, notificaciones). La conversión a segunda compra aunque sea pequeña en porcentaje tiene gran impacto dado el volumen.

---

## Comparativa de segmentos

```
                    RECENCY (días)    FRECUENCIA    GASTO MEDIO
                    ─────────────    ──────────    ───────────
Fiel Activo              202              2.5        R$ 1.047   ★★★★★
Fiel En Riesgo           222              2.1        R$   205   ★★★★
Alto Valor Durmiente     246              1.0        R$   981   ★★★
Esporadico Comun         238              1.0        R$   109   ★
```

---

## Limitación del dataset y escalabilidad

El dataset cubre un periodo de ~2 años (sept. 2016 – ago. 2018). La **alta concentración en frequency=1 no es un problema de datos insuficientes**, sino una característica estructural del marketplace: categorías de compra ocasional (muebles, electrónica, regalos) donde la recompra natural es baja.

Sin embargo, el modelo **gana poder predictivo con el tiempo**: a medida que el negocio madure y acumule más historia por cliente, la variable Frequency generará mayor varianza y permitirá que K-Means la use directamente como discriminador, haciendo la segmentación más granular (potencialmente 5-6 segmentos con perfiles más definidos).

---

## Supuestos asumidos

1. Se usa `customer_unique_id` en lugar de `customer_id` para identificar al cliente físico real
2. Solo se consideran órdenes con `order_status == 'delivered'`.
3. El umbral de fidelidad se define como `frequency >= 2` — al menos una recompra. Con más historia de datos este umbral podría elevarse.
4. La fecha de referencia para Recency es el día siguiente al máximo del dataset (2018-08-30), simulando el "hoy" del análisis.
5. Los ingresos se calculan como `price` sin `freight_value`, consistente con P1 y P5.
