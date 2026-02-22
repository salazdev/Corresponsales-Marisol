import streamlit as st
import pandas as pd
import plotly.express as px

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

# 2. CARGA DE DATOS ROBUSTA
@st.cache_data(ttl=3600)
def cargar_datos_locales():
    try:
        # Leer archivo con detección de separador
        df = pd.read_csv("datos_corresponsales.csv", sep=None, engine='python', on_bad_lines='skip')
        
        if df.empty:
            return None

        # Limpiar nombres de columnas y quitar duplicados
        cols = pd.Series(df.columns).str.strip()
        for i, col in enumerate(cols):
            if (cols == col).sum() > 1:
                count = list(cols[:i]).count(col)
                if count > 0:
                    cols[i] = f"{col}.{count}"
        df.columns = cols

        # LIMPIEZA DE COLUMNAS NUMÉRICAS
        for col in df.columns:
            if any(x in col.upper() for x in ["TX", "2025", "2026", "TRANSA", "$"]):
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False).str.strip()
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
        return df
    except Exception as e:
        st.error(f"Error al cargar el archivo: {e}")
        return None

df = cargar_datos_locales()

if df is not None:
    # Identificación de columnas
    cols = list(df.columns)
    col_ciudad = next((c for c in cols if "ciudad" in c.lower()), "Ciudad")
    col_esp = next((c for c in cols if "especialista" in c.lower()), "ESPECIALISTA")
    col_dir = next((c for c in cols if "dirección" in c.lower() or "direccion" in c.lower()), "Dirección")
    
    # Buscamos la columna de transacciones totales
    posibles_tx = [c for c in cols if "TX ULTIMO SEMESTRE" in c.upper() or "TOTAL" in c.upper()]
    col_tx_total = posibles_tx[0] if posibles_tx else (next((c for c in cols if "TX" in c.upper() or "TRANSA" in c.upper()), cols[-1]))

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
        
        # Corregido: Cierre de paréntesis y formato
        m1.metric("Puntos Encontrados", f"{len(df_filtrado):,}")
        
        suma_tx = float(df_filtrado[col_tx_total].sum())
        m2.metric("TX Totales", f"{suma_tx:,.0f}")
        
        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("📈 Evolución de Transacciones")
        meses = [c for c in cols if any(m in c.upper() for m in ["JUL", "AGO", "SEP", "OCT", "NOV", "DIC", "ENE"])]
        if meses:
            df_t = df_filtrado[meses].sum().reset_index()
            df_t.columns = ["Mes", "Total TX"]
            fig = px.line(df_t, x="Mes", y="Total TX", markers=True, color_discrete_sequence=["#0033a0"])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No se encontraron columnas de meses para la tendencia.")

    with tab3:
        st.subheader("🚨 Alertas de Gestión")
        df_al = df_filtrado[df_filtrado[col_tx_total] == 0].copy()
        if not df_al.empty:
            st.warning(f"Hay {len(df_al)} puntos con 0 transacciones.")
            st.dataframe(df_al[[col_esp, col_ciudad, col_dir, col_tx_total]], use_container_width=True)
        else:
            st.success("✅ No se detectan puntos inactivos en esta selección.")

else:
    st.info("📢 Sube el archivo 'datos_corresponsales.csv' para comenzar.")
