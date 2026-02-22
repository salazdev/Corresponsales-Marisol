import streamlit as st
import pandas as pd

st.set_page_config(page_title="BVB - Resumen Ejecutivo", layout="wide")

st.title("🏦 Resumen Estratégico de Corresponsalía")

SHEET_ID = "1i998RGnLv8npxSLB5OyBvzNr36dQJD8RFdsKZj4UOfw"
URL_SHEET = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

@st.cache_data(ttl=60)
def cargar_resumen():
    try:
        df = pd.read_csv(URL_SHEET)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Error: {e}")
        return None

df = cargar_resumen()

if df is not None:
    # Identificar las columnas detectadas
    col_esp = "ESPECIALISTA"
    col_suma = "Suma de Cantidad puntos de atención"

    # --- MÉTRICAS ---
    st.subheader("📊 Totales por Especialista")
    
    # Calculamos totales específicos
    total_general = df[col_suma].sum()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Corresponsales", f"{total_general:,.0f}")
    
    # Buscar a Jorge
    jorge = df[df[col_esp].str.contains("JORGE ARRIETA", case=False, na=False)]
    cant_jorge = jorge[col_suma].sum() if not jorge.empty else 0
    c2.metric("Jorge Arrieta", f"{cant_jorge:,.0f}")
    
    # Buscar a Alan
    alan = df[df[col_esp].str.contains("ALAN", case=False, na=False)]
    cant_alan = alan[col_suma].sum() if not alan.empty else 0
    c3.metric("Alan Forero", f"{cant_alan:,.0f}")

    st.divider()

    # --- TABLA DE DATOS ---
    st.subheader("📑 Reporte de Especialistas")
    st.dataframe(df, use_container_width=True, hide_index=True)

else:
    st.info("Conectando con el resumen del Banco...")

