import streamlit as st
import pandas as pd

# 1. CONFIGURACIÓN DE LA APP
st.set_page_config(page_title="BVB - Consulta Integral", layout="wide")

# ESTILO CSS PARA FORZAR TEXTO NEGRO EN MÉTRICAS Y MEJORAR CONTRASTE
st.markdown("""
    <style>
    /* Fondo de la app */
    .main { background-color: #f8f9fa; }
    
    /* Forzar texto negro en las métricas */
    [data-testid="stMetricValue"] {
        color: #000000 !important;
        font-weight: bold;
    }
    [data-testid="stMetricLabel"] {
        color: #333333 !important;
        font-size: 1.1rem !important;
    }
    
    /* Contenedor de métricas con borde azul Banco de Bogotá */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-left: 8px solid #0033a0;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 Panel de Control: Corresponsalía Bancaria")
st.info("Consulta detallada de Especialistas, Ciudades y Direcciones.")

# 2. CARGA DE DATOS
@st.cache_data(ttl=3600)
def cargar_datos_locales():
    try:
        df = pd.read_csv("datos_corresponsales.csv", on_bad_lines='skip', engine='python')
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        return None

df = cargar_datos_locales()

if df is not None:
    # Identificación de columnas
    cols = df.columns.tolist()
    col_ciudad = next((c for c in cols if "ciudad" in c.lower()), None)
    col_esp = next((c for c in cols if "especialista" in c.lower()), None)
    col_dir = next((c for c in cols if "dirección" in c.lower() or "direccion" in c.lower()), None)
    col_tipo = next((c for c in cols if "tipo" in c.lower()), None)

    # --- FILTROS ---
    st.sidebar.header("🔍 Criterios de Consulta")
    
    # Especialista
    lista_esp = ["Todos"] + sorted(df[col_esp].dropna().unique().tolist()) if col_esp else ["Todos"]
    esp_sel = st.sidebar.selectbox("Filtrar por Especialista:", lista_esp)

    # Ciudad (Dinámica)
    df_temp = df.copy()
    if esp_sel != "Todos":
        df_temp = df_temp[df_temp[col_esp] == esp_sel]
    
    lista_ciudades = ["Todas"] + sorted(df_temp[col_ciudad].dropna().unique().tolist()) if col_ciudad else ["Todas"]
    ciudad_sel = st.sidebar.selectbox("Filtrar por Ciudad:", lista_ciudades)

    # Aplicar filtros
    df_final = df.copy()
    if esp_sel != "Todos":
        df_final = df_final[df_final[col_esp] == esp_sel]
    if ciudad_sel != "Todas":
        df_final = df_final[df_final[col_ciudad] == ciudad_sel]

    # --- MÉTRICAS (Ahora con texto negro garantizado) ---
    st.subheader("📊 Resumen de la Selección")
    m1, m2, m3 = st.columns(3)
    
    with m1:
        st.metric("Puntos Encontrados", f"{len(df_final):,}")
    with m2:
        st.metric("Especialista", esp_sel if esp_sel != "Todos" else "Nacional")
    with m3:
        st.metric("Ubicación", ciudad_sel if ciudad_sel != "Todas" else "Colombia")

    st.divider()

    # --- TABLA DE DETALLES ---
    st.subheader(f"📍 Detalle: {ciudad_sel}")
    
    busqueda = st.text_input("🔍 Búsqueda rápida (escriba cualquier dato):")
    if busqueda:
        df_final = df_final[df_final.astype(str).apply(lambda x: x.str.contains(busqueda, case=False, na=False)).any(axis=1)]

    # Mostrar tabla
    columnas_vista = [c for c in [col_esp, col_ciudad, col_dir, col_tipo] if c is not None]
    st.dataframe(df_final[columnas_vista], use_container_width=True, hide_index=True)

    # Botón de descarga
    csv = df_final.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Descargar Excel de esta consulta", csv, "consulta_bvb.csv", "text/csv")

else:
    st.warning("Cargando base de datos...")
