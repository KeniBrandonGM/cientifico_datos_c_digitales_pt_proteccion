import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import RobustScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

DATA_DIR   = Path(__file__).parent.parent / 'data'
OUTPUT_DIR = Path(__file__).parent.parent / 'data'

# =============================================================================
# CARGA Y CONSTRUCCION RFM
# =============================================================================
orders      = pd.read_csv(DATA_DIR / 'orders_dataset.csv')
order_items = pd.read_csv(DATA_DIR / 'order_items_dataset.csv')
customers   = pd.read_csv(DATA_DIR / 'customers_dataset.csv')

orders = orders[orders['order_status'] == 'delivered'].copy()
orders['order_purchase_timestamp'] = pd.to_datetime(orders['order_purchase_timestamp'])

ingresos = order_items.groupby('order_id')['price'].sum().reset_index(name='monetary')
df = orders.merge(ingresos, on='order_id', how='inner')
df = df.merge(customers[['customer_id', 'customer_unique_id']], on='customer_id', how='inner')

fecha_ref = orders['order_purchase_timestamp'].max() + pd.Timedelta(days=1)

rfm = (
    df.groupby('customer_unique_id')
    .agg(
        recency  =('order_purchase_timestamp', lambda x: (fecha_ref - x.max()).days),
        frequency=('order_id', 'count'),
        monetary =('monetary', 'sum')
    )
    .reset_index()
)

print(f"Clientes totales en RFM: {len(rfm)}")
print(f"Fecha referencia recency: {fecha_ref.date()}")

# =============================================================================
# NIVEL 1 — SPLIT POR REGLA DE NEGOCIO (frecuencia)
# =============================================================================
print("\n" + "="*70)
print("NIVEL 1: SPLIT POR FRECUENCIA DE COMPRA")
print("="*70)

recurrentes = rfm[rfm['frequency'] >= 2].copy()
unicos      = rfm[rfm['frequency'] == 1].copy()

print(f"Compradores unicos   (freq=1):  {len(unicos):>6} ({len(unicos)/len(rfm)*100:.1f}%)")
print(f"Compradores recurrentes (freq>=2): {len(recurrentes):>6} ({len(recurrentes)/len(rfm)*100:.1f}%)")

# =============================================================================
# NIVEL 2A — K-Means sobre RECURRENTES (variables: R + M)
# Pregunta: dentro de los que recompran, ¿quienes siguen activos vs en riesgo?
# =============================================================================
print("\n" + "="*70)
print("NIVEL 2A: K-MEANS SOBRE RECURRENTES (R + M)")
print("="*70)

scaler_rec = RobustScaler()
rec_scaled = scaler_rec.fit_transform(recurrentes[['recency', 'monetary']])

print("\nBuscando k optimo para recurrentes:")
sil_rec = {}
for k in range(2, 6):
    km  = KMeans(n_clusters=k, random_state=42, n_init=10)
    lbl = km.fit_predict(rec_scaled)
    sil = silhouette_score(rec_scaled, lbl, random_state=42)
    sil_rec[k] = sil
    print(f"  k={k} | silhouette={sil:.4f}")

k_rec = max(sil_rec, key=sil_rec.get)
print(f"\n>>> K optimo recurrentes: {k_rec}")

km_rec = KMeans(n_clusters=k_rec, random_state=42, n_init=10)
recurrentes['sub_cluster'] = km_rec.fit_predict(rec_scaled)

print("\nEstadisticas por sub-cluster (recurrentes):")
stats_rec = recurrentes.groupby('sub_cluster')[['recency', 'frequency', 'monetary']].mean().round(1)
stats_rec['n'] = recurrentes.groupby('sub_cluster').size()
print(stats_rec.to_string())

# =============================================================================
# NIVEL 2B — K-Means sobre UNICOS (variables: R + M)
# Pregunta: dentro de los que compraron una vez, ¿quienes valen la pena reactivar?
# =============================================================================
print("\n" + "="*70)
print("NIVEL 2B: K-MEANS SOBRE UNICOS (R + M)")
print("="*70)

scaler_uni = RobustScaler()
uni_scaled  = scaler_uni.fit_transform(unicos[['recency', 'monetary']])

print("\nBuscando k optimo para unicos (silhouette con muestra de 15k):")
sil_uni = {}
for k in range(2, 7):
    km  = KMeans(n_clusters=k, random_state=42, n_init=10)
    lbl = km.fit_predict(uni_scaled)
    sil = silhouette_score(uni_scaled, lbl, sample_size=15000, random_state=42)
    sil_uni[k] = sil
    print(f"  k={k} | silhouette={sil:.4f}")

k_uni = max(sil_uni, key=sil_uni.get)
print(f"\n>>> K optimo unicos: {k_uni}")

km_uni = KMeans(n_clusters=k_uni, random_state=42, n_init=10)
unicos['sub_cluster'] = km_uni.fit_predict(uni_scaled)

print("\nEstadisticas por sub-cluster (unicos):")
stats_uni = unicos.groupby('sub_cluster')[['recency', 'monetary']].mean().round(1)
stats_uni['n'] = unicos.groupby('sub_cluster').size()
print(stats_uni.to_string())

# =============================================================================
# ETIQUETADO DE SEGMENTOS
# Lógica: recurrentes → por recency | unicos → por recency + monetary
# =============================================================================
print("\n" + "="*70)
print("ETIQUETADO DE SEGMENTOS DE NEGOCIO")
print("="*70)

# --- Recurrentes: el sub-cluster con menor recency = activo, mayor = en riesgo ---
medias_rec = recurrentes.groupby('sub_cluster')['recency'].mean()

if k_rec == 2:
    cluster_activo   = medias_rec.idxmin()
    cluster_riesgo   = medias_rec.idxmax()
    etiquetas_rec = {
        cluster_activo: 'Cliente_Fiel_Activo',
        cluster_riesgo: 'Cliente_Fiel_En_Riesgo',
    }
else:
    # Si k=3+, ordenamos por recency y etiquetamos
    orden = medias_rec.sort_values().index.tolist()
    nombres = ['Cliente_Fiel_Activo', 'Cliente_Fiel_Intermedio', 'Cliente_Fiel_En_Riesgo']
    etiquetas_rec = {c: nombres[i] for i, c in enumerate(orden[:3])}

recurrentes['segmento'] = recurrentes['sub_cluster'].map(etiquetas_rec)

# --- Unicos: etiquetamos comparando clusters entre sí (ranking relativo) ---
# k=2 separa principalmente por monetary: cluster alto M vs cluster bajo M
medias_uni = unicos.groupby('sub_cluster')[['recency', 'monetary']].mean()
print(f"\nMedias unicos por sub-cluster:\n{medias_uni.round(1).to_string()}")

cluster_alto_valor = medias_uni['monetary'].idxmax()
cluster_comun      = medias_uni['monetary'].idxmin()

etiquetas_uni = {
    cluster_alto_valor: 'Alto_Valor_Durmiente',   # 1 compra, gasto alto — vale la pena reactivar
    cluster_comun:      'Esporadico_Comun',        # 1 compra, gasto promedio/bajo
}
unicos['segmento'] = unicos['sub_cluster'].map(etiquetas_uni)

# =============================================================================
# RESULTADO FINAL
# =============================================================================
print("\n" + "="*70)
print("RESULTADO FINAL — SEGMENTOS DE CLIENTES")
print("="*70)

final = pd.concat([recurrentes, unicos], ignore_index=True)

resumen = (
    final.groupby('segmento')
    .agg(
        clientes   =('customer_unique_id', 'count'),
        recency_med=('recency', 'mean'),
        freq_media =('frequency', 'mean'),
        monetary_med=('monetary', 'mean'),
    )
    .round(1)
    .sort_values('clientes', ascending=False)
)
resumen['pct'] = (resumen['clientes'] / len(final) * 100).round(1)
print(resumen.to_string())

# Guardar para uso en P6/P7
final[['customer_unique_id', 'recency', 'frequency', 'monetary', 'segmento']].to_csv(
    OUTPUT_DIR / 'clientes_segmentados.csv', index=False
)
print(f"\nGuardado: data/clientes_segmentados.csv")
