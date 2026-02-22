import streamlit as st
import pandas as pd
import plotly.express as px
import io

# 1. CONFIGURACIÓN DE LA APP
st.set_page_config(page_title="BVB - Gestión Comercial", layout="wide")

# ESTILO CSS
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stMetricValue"] { color: #000000 !important; font-weight: bold; }
    [data-testid="stMetricLabel"] { color: #333333 !important; font-size: 1.1rem !important; }
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

# 2. CARGA DE DATOS ROBUSTA (Detección de separadores y duplicados)
@st.cache_data(ttl=3600)
def cargar_datos_locales():
    try:
        # Intentamos leer con detección automática de separador (sep=None)
        df = pd.read_csv("datos_corresponsales.csv", sep=None, engine='python', on_bad_lines='skip')
        
        if df.empty:
            st.error("🚨 El archivo 'datos_corresponsales.csv' parece estar vacío.")
            return None

        # --- SOLUCIÓN A COLUMNAS DUPLICADAS ---
        cols = pd.Series(df.columns)
        for i, col in enumerate(cols):
            if (cols == col).sum() > 1:
                count = list(cols[:i]).count(col)
                if count > 0:
                    cols[i] = f"{col}.{count}"
        df.columns = [str(c).strip() for c in cols]
        
        # Limpieza de datos financieros
        cols_fin = [c for c in df.columns if any(x in c for x in ["2025", "2026", "TX", "$", "Transa"])]
        for col in cols_fin:
            if df[col].dtype == 'object':
                df[col] = df[col].str.replace('$', '', regex=False).str.replace(',', '', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
        return df
    except Exception as e:
        st.error(f"Error crítico al abrir el archivo: {e}")
        st.info("Asegúrate de que el archivo CSV no esté abierto en tu computadora al subirlo a GitHub.")
        return None

df = cargar_datos_locales()

if df is not None:
    # Identificación de columnas
    cols = list(df.columns)
    col_ciudad = next((c for c in cols if "ciudad" in c.lower()), "Ciudad")
    col_esp = next((c for c in cols if "especialista" in c.lower()), "ESPECIALISTA")
    col_dir = next((c for c in cols if "dirección" in c.lower() or "direccion" in c.lower()), "Dirección")
    col_tx_total = "Tx Ultimo Semestre" if "Tx Ultimo Semestre" in cols else (next((c for c in cols if "transa" in c.lower()), cols[0]))
    col_alerta = "Transa si/no MES"

    # --- FILTROS ---
    st.sidebar.header("🔍 Criterios de Consulta")
    lista_esp = ["Todos"] + sorted(df[col_esp].dropna().unique().tolist())
    esp_sel = st.sidebar.selectbox("Especialista:", lista_esp)

    df_temp = df[df[col_esp] == esp_sel] if esp_sel != "Todos" else df
    lista_ciudades = ["Todas"] + sorted(df_temp[col_ciudad].dropna().unique().tolist())
    ciudad_sel = st.sidebar.selectbox("Municipio:", lista_ciudades)

    df_filtrado = df_temp.copy()
    if ciudad_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado[col_ciudad] == ciudad_sel]

    # --- PESTAÑAS ---
    tab1, tab2, tab3 = st.tabs(["📍 Consulta", "📈 Análisis", "🚨 Alertas"])

    with tab1:
        st.subheader(f"📍 Listado: {ciudad_sel}")
        m1, m2 = st.columns(2)
        m1.metric("Puntos", f"{len(df_filtrado):,}")
        m2.metric("TX Totales", f"{df_filtrado[col_tx_total].sum():,.0f}")
        
        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("📈 Evolución")
        meses = ["Jul 2025 TX", "Ago 2025 TX", "Sep 2025 TX", "Oct 2025 TX", "Nov 2025 TX", "Dic 2025 TX", "Ene 2026 TX"]
        cols_v = [m for m in meses if m in cols]
        if cols_v:
            df_t = df_filtrado[cols_v].sum().reset_index()
            df_t.columns = ["Mes", "Total TX"]
            st.plotly_chart(px.line(df_t, x="Mes", y="Total TX", markers=True), use_container_width=True)

    with tab3:
        st.subheader("🚨 Gestión Urgente")
        df_al = df[df[col_alerta] == "No"].copy() if col_alerta in cols else df[df[col_tx_total] == 0].copy()
        st.dataframe(df_al, use_container_width=True)

else:
    st.info("📢 Por favor, verifica que 'datos_corresponsales.csv' tenga datos y esté bien estructurado.")
