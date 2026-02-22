import streamlit as st
import pandas as pd

st.set_page_config(page_title="BVB - Consulta Integral", layout="wide")

SHEET_ID = "1i998RGnLv8npxSLB5OyBvzNr36dQJD8RFdsKZj4UOfw"
URL_SHEET = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

@st.cache_data(ttl=60)
def cargar_datos():
    df = pd.read_csv(URL_SHEET)
    df.columns = [str(c).strip() for c in df.columns]
    return df

df = cargar_datos()

# --- VALIDACIÓN PROFESIONAL ---
st.title("🏦 Sistema de Consulta de Corresponsalía")

if "Ciudad" in df.columns:
    st.success("✅ Base Detallada Detectada")
    
    # 1. Filtros
    col1, col2 = st.columns(2)
    with col1:
        ciudad_sel = st.selectbox("Seleccione Ciudad para ver direcciones:", sorted(df['Ciudad'].unique()))
    with col2:
        esp_sel = st.selectbox("Filtrar por Especialista:", ["Todos"] + sorted(df['ESPECIALISTA'].unique().tolist()))

    # 2. Filtrado de datos
    mask = df['Ciudad'] == ciudad_sel
    if esp_sel != "Todos":
        mask = mask & (df['ESPECIALISTA'] == esp_sel)
    
    df_ver = df[mask]

    # 3. Respuesta a la Directora
    st.metric(f"Cantidad de Corresponsales en {ciudad_sel}", len(df_ver))
    
    st.subheader("📍 Direcciones y Detalles")
    # Mostramos lo que ella pidió: Dirección, Nombre/Tipo y Especialista
    columnas_finales = [c for c in ['Dirección', 'Tipo de CBs', 'ESPECIALISTA'] if c in df.columns]
    st.dataframe(df_ver[columnas_finales], use_container_width=True, hide_index=True)

else:
    st.error("⚠️ La hoja actual solo contiene un RESUMEN.")
    st.info("Por favor, asegúrate de que la primera pestaña del Google Sheet sea la BASE COMPLETA con columnas de Ciudad y Dirección.")
    st.write("Columnas detectadas actualmente:", list(df.columns))
