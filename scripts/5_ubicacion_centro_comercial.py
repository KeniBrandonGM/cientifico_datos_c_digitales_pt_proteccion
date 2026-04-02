import pandas as pd
import numpy as np
import folium
from pathlib import Path

DATA_DIR    = Path(__file__).parent.parent / 'data'
OUTPUT_DIR  = Path(__file__).parent.parent / 'outputs'
OUTPUT_DIR.mkdir(exist_ok=True)

# =============================================================================
# CARGA DE DATOS
# =============================================================================
orders      = pd.read_csv(DATA_DIR / 'orders_dataset.csv')
customers   = pd.read_csv(DATA_DIR / 'customers_dataset.csv')
order_items = pd.read_csv(DATA_DIR / 'order_items_dataset.csv')
geo         = pd.read_csv(DATA_DIR / 'geolocation_dataset.csv')

print(f"orders:      {len(orders)}")
print(f"customers:   {len(customers)}")
print(f"order_items: {len(order_items)}")
print(f"geo:         {len(geo)}")

# =============================================================================
# PASO 1 — CIUDAD CON MAYORES VENTAS
# Supuesto: solo órdenes 'delivered' (mismo criterio que P1)
# Ingresos = price (sin freight_value)
# =============================================================================
print("\n" + "="*70)
print("PASO 1: CIUDAD CON MAYORES VENTAS")
print("="*70)

orders_delivered = orders[orders['order_status'] == 'delivered'].copy()

# Ingresos por orden
ingresos_orden = order_items.groupby('order_id')['price'].sum().reset_index(name='ingresos')

# Unir: orden → cliente → ingresos
df = (orders_delivered
      .merge(customers[['customer_id', 'customer_unique_id',
                         'customer_city', 'customer_state',
                         'customer_zip_code_prefix']], on='customer_id', how='inner')
      .merge(ingresos_orden, on='order_id', how='inner'))

# Agrupar por ciudad+estado (ciudad puede repetirse entre estados)
ciudad_stats = (
    df.groupby(['customer_city', 'customer_state'])
    .agg(
        ordenes=('order_id', 'count'),
        ingresos_totales=('ingresos', 'sum'),
        clientes_unicos=('customer_unique_id', 'nunique')
    )
    .reset_index()
    .sort_values('ingresos_totales', ascending=False)
)

print("\nTop 10 ciudades por ingresos totales:")
print(ciudad_stats.head(10).to_string(index=False))

print("\nTop 10 ciudades por volumen de órdenes:")
print(ciudad_stats.sort_values('ordenes', ascending=False).head(10).to_string(index=False))

# Ciudad top (por ingresos — criterio principal)
top_ciudad = ciudad_stats.iloc[0]
CIUDAD      = top_ciudad['customer_city']
ESTADO      = top_ciudad['customer_state']
print(f"\n>>> Ciudad seleccionada: {CIUDAD.upper()} ({ESTADO})")
print(f"    Ingresos: R$ {top_ciudad['ingresos_totales']:,.2f}")
print(f"    Órdenes:  {top_ciudad['ordenes']:,}")
print(f"    Clientes únicos: {top_ciudad['clientes_unicos']:,}")

# =============================================================================
# PASO 2 — COORDENADAS DE LOS CLIENTES EN ESA CIUDAD
# =============================================================================
print("\n" + "="*70)
print(f"PASO 2: COORDENADAS DE CLIENTES EN {CIUDAD.upper()}")
print("="*70)

# Clientes de la ciudad top con sus órdenes e ingresos
clientes_ciudad = df[df['customer_city'] == CIUDAD].copy()

# Geolocalización: un zip code puede tener varias entradas → promediamos
geo_avg = (
    geo.groupby('geolocation_zip_code_prefix')
    .agg(lat=('geolocation_lat', 'mean'), lng=('geolocation_lng', 'mean'))
    .reset_index()
)

# Unir clientes con coordenadas via zip code prefix
clientes_geo = clientes_ciudad.merge(
    geo_avg,
    left_on='customer_zip_code_prefix',
    right_on='geolocation_zip_code_prefix',
    how='inner'
)

print(f"Clientes con coordenadas disponibles: {len(clientes_geo)} de {len(clientes_ciudad)}")

# Validar coordenadas: eliminar outliers geográficos (Brasil: lat -34 a 5, lng -74 a -34)
clientes_geo = clientes_geo[
    clientes_geo['lat'].between(-34, 5) &
    clientes_geo['lng'].between(-74, -34)
]
print(f"Tras filtro de coordenadas válidas:   {len(clientes_geo)}")

# =============================================================================
# PASO 3 — CENTROIDE PONDERADO POR INGRESOS
# =============================================================================
print("\n" + "="*70)
print("PASO 3: CENTROIDE PONDERADO POR INGRESOS")
print("="*70)

pesos = clientes_geo['ingresos'].values
lat_opt = np.average(clientes_geo['lat'].values, weights=pesos)
lng_opt = np.average(clientes_geo['lng'].values, weights=pesos)

# Centroide simple (sin pesos) para comparar
lat_simple = clientes_geo['lat'].mean()
lng_simple  = clientes_geo['lng'].mean()

print(f"\nCentroide simple (sin ponderar):    lat={lat_simple:.6f}, lng={lng_simple:.6f}")
print(f"Centroide ponderado por ingresos:   lat={lat_opt:.6f},  lng={lng_opt:.6f}")
print(f"\n>>> PUNTO ÓPTIMO RECOMENDADO:")
print(f"    Latitud:  {lat_opt:.6f}")
print(f"    Longitud: {lng_opt:.6f}")
print(f"    (Basado en {len(clientes_geo):,} clientes con un total de R$ {pesos.sum():,.2f} en compras)")

# Estadísticas de dispersión
distancias_km = np.sqrt(
    ((clientes_geo['lat'] - lat_opt) * 111) ** 2 +
    ((clientes_geo['lng'] - lng_opt) * 111 * np.cos(np.radians(lat_opt))) ** 2
)
print(f"\n    Distancia promedio de clientes al punto: {distancias_km.mean():.2f} km")
print(f"    Distancia mediana:                        {distancias_km.median():.2f} km")
print(f"    El 80% de clientes está dentro de:        {np.percentile(distancias_km, 80):.2f} km")

# =============================================================================
# PASO 4 — MAPA INTERACTIVO CON FOLIUM
# =============================================================================
print("\n" + "="*70)
print("PASO 4: GENERANDO MAPA INTERACTIVO")
print("="*70)

mapa = folium.Map(location=[lat_opt, lng_opt], zoom_start=11, tiles='CartoDB positron')

# Heatmap de densidad de clientes (muestra hasta 3000 puntos para no sobrecargar)
muestra = clientes_geo.sample(min(3000, len(clientes_geo)), random_state=42)
from folium.plugins import HeatMap
calor_data = list(zip(muestra['lat'], muestra['lng'], muestra['ingresos']))
HeatMap(calor_data, radius=12, blur=15, min_opacity=0.4, name='Densidad de clientes').add_to(mapa)

# Punto óptimo (ponderado)
folium.Marker(
    location=[lat_opt, lng_opt],
    popup=folium.Popup(
        f"<b>PUNTO ÓPTIMO RECOMENDADO</b><br>"
        f"Centroide ponderado por ingresos<br>"
        f"Lat: {lat_opt:.6f}<br>Lng: {lng_opt:.6f}<br>"
        f"Basado en {len(clientes_geo):,} clientes",
        max_width=250
    ),
    tooltip="📍 Ubicación óptima del centro comercial",
    icon=folium.Icon(color='red', icon='star', prefix='fa')
).add_to(mapa)

# Punto centroide simple (para comparar)
folium.Marker(
    location=[lat_simple, lng_simple],
    popup=folium.Popup(
        f"<b>Centroide simple</b><br>(sin ponderar por ingresos)<br>"
        f"Lat: {lat_simple:.6f}<br>Lng: {lng_simple:.6f}",
        max_width=220
    ),
    tooltip="Centroide simple (referencia)",
    icon=folium.Icon(color='blue', icon='info-sign')
).add_to(mapa)

# Radio de cobertura: 80% de clientes
radio_80 = float(np.percentile(distancias_km, 80))
folium.Circle(
    location=[lat_opt, lng_opt],
    radius=radio_80 * 1000,
    color='red',
    fill=True,
    fill_opacity=0.05,
    popup=f"Radio de cobertura: {radio_80:.1f} km (80% de clientes)",
    tooltip=f"80% de clientes en {radio_80:.1f} km"
).add_to(mapa)

folium.LayerControl().add_to(mapa)

mapa_path = OUTPUT_DIR / 'p5_mapa_ubicacion.html'
mapa.save(str(mapa_path))
print(f"\nMapa guardado en: {mapa_path}")
print("Ábrelo en tu navegador para ver la ubicación óptima con el heatmap de clientes.")

# =============================================================================
# PASO 5 — MAPA DE CONTEXTO: TODOS LOS CLIENTES DE BRASIL
# Objetivo: mostrar graficamente que Sao Paulo concentra la mayor densidad
# de clientes y reafirmar que es la ciudad correcta para el centro comercial.
# =============================================================================
print("\n" + "="*70)
print("PASO 5: MAPA DE CONTEXTO — TODOS LOS CLIENTES DE BRASIL")
print("="*70)

# Coordenadas de todos los clientes del dataset (todas las ciudades)
clientes_todos = df.merge(
    geo_avg,
    left_on='customer_zip_code_prefix',
    right_on='geolocation_zip_code_prefix',
    how='inner'
)
clientes_todos = clientes_todos[
    clientes_todos['lat'].between(-34, 5) &
    clientes_todos['lng'].between(-74, -34)
]
print(f"Clientes con coordenadas en todo Brasil: {len(clientes_todos):,}")

# Ingresos y ordenes por ciudad para los circulos proporcionales
ciudad_geo = (
    clientes_todos.groupby(['customer_city', 'customer_state'])
    .agg(
        ingresos=('ingresos', 'sum'),
        ordenes=('order_id', 'count'),
        lat=('lat', 'mean'),
        lng=('lng', 'mean'),
    )
    .reset_index()
    .sort_values('ingresos', ascending=False)
)

# Mapa centrado en Brasil
mapa_brasil = folium.Map(
    location=[-15.0, -50.0],
    zoom_start=5,
    tiles='CartoDB positron'
)

# Heatmap de densidad de todos los clientes (muestra hasta 8000 puntos)
muestra_brasil = clientes_todos.sample(min(8000, len(clientes_todos)), random_state=42)
calor_brasil = list(zip(muestra_brasil['lat'], muestra_brasil['lng'], muestra_brasil['ingresos']))
HeatMap(
    calor_brasil,
    radius=10, blur=18, min_opacity=0.3,
    name='Densidad clientes Brasil'
).add_to(mapa_brasil)

# Circulos proporcionales: top 20 ciudades por ingresos
ingreso_max = ciudad_geo['ingresos'].max()
for _, row in ciudad_geo.head(20).iterrows():
    radio = 8000 + (row['ingresos'] / ingreso_max) * 55000   # radio en metros
    es_top = row['customer_city'] == CIUDAD

    folium.Circle(
        location=[row['lat'], row['lng']],
        radius=radio,
        color='#c0392b' if es_top else '#2980b9',
        fill=True,
        fill_opacity=0.45 if es_top else 0.25,
        weight=3 if es_top else 1,
        popup=folium.Popup(
            f"<b>{row['customer_city'].title()} ({row['customer_state']})</b><br>"
            f"Ingresos: R$ {row['ingresos']:,.0f}<br>"
            f"Ordenes: {row['ordenes']:,}",
            max_width=220
        ),
        tooltip=f"{row['customer_city'].title()} — R$ {row['ingresos']:,.0f}",
    ).add_to(mapa_brasil)

# Punto optimo dentro de Sao Paulo
folium.Marker(
    location=[lat_opt, lng_opt],
    popup=folium.Popup(
        f"<b>UBICACION OPTIMA DEL CENTRO COMERCIAL</b><br>"
        f"Ciudad: {CIUDAD.title()} ({ESTADO})<br>"
        f"Ingresos ciudad: R$ {top_ciudad['ingresos_totales']:,.0f}<br>"
        f"Lat: {lat_opt:.6f} | Lng: {lng_opt:.6f}",
        max_width=270
    ),
    tooltip="Punto optimo — centro comercial",
    icon=folium.Icon(color='red', icon='star', prefix='fa')
).add_to(mapa_brasil)

folium.LayerControl().add_to(mapa_brasil)

mapa_brasil_path = OUTPUT_DIR / 'p5_mapa_brasil.html'
mapa_brasil.save(str(mapa_brasil_path))
print(f"Mapa de contexto guardado en: {mapa_brasil_path}")
print(f"Top 3 ciudades por ingresos:")
for _, r in ciudad_geo.head(3).iterrows():
    marca = " <<< SELECCIONADA" if r['customer_city'] == CIUDAD else ""
    print(f"  {r['customer_city'].title()} ({r['customer_state']}): R$ {r['ingresos']:,.0f}{marca}")
