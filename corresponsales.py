import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DE LA APP
st.set_page_config(page_title="BVB - Gestión Comercial", layout="wide")

# ESTILO CSS (Texto negro en métricas y bordes azules Banco de Bogotá)
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
    .stTabs [aria-selected="true"] { font-weight: bold; border-bottom: 2px solid #0033a0; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 Sistema de Gestión de Corresponsalía (Versión Alta Velocidad)")

# 2. CARGA DESDE GITHUB (Súper rápido y estable)
@st.cache_data(ttl=3600)
def cargar_datos_locales():
    try:
        # Lee el archivo directamente desde la misma carpeta del repositorio
        df = pd.read_csv("datos_corresponsales.csv", on_bad_lines='skip', engine='python')
        # Limpieza de nombres de columnas
        df.columns = [str(c).strip() for c in df.columns]
        
        # Limpieza de datos financieros para gráficos (quitar $ y comas)
        cols_fin = [c for c in df.columns if any(x in c for x in ["2025", "2026", "TX", "$", "Transa"])]
        for col in cols_fin:
            if df[col].dtype == 'object':
                df[col] = df[col].str.replace('$', '', regex=False).str.replace(',', '', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
        return df
    except FileNotFoundError:
        st.error("🚨 ¡Archivo no encontrado! Sube 'datos_corresponsales.csv' a tu GitHub.")
        return None
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        return None

df = cargar_datos_locales()

if df is not None:
    # Identificación automática de columnas clave
    cols = list(df.columns)
    col_ciudad = next((c for c in cols if "ciudad" in c.lower()), "Ciudad")
    col_esp = next((c for c in cols if "especialista" in c.lower()), "ESPECIALISTA")
    col_dir = next((c for c in cols if "dirección" in c.lower() or "direccion" in c.lower()), "Dirección")
    
    # Intentar identificar columna de transacciones totales o usar la primera numérica
    col_tx_total = "Tx Ultimo Semestre" if "Tx Ultimo Semestre" in cols else (next((c for c in cols if "transa" in c.lower()), cols[0]))
    col_alerta = "Transa si/no MES"

    # --- FILTROS EN SIDEBAR ---
    st.sidebar.header("🔍 Criterios de Consulta")
    
    lista_esp = ["Todos"] + sorted(df[col_esp].dropna().unique().tolist())
    esp_sel = st.sidebar.selectbox("Filtrar por Especialista:", lista_esp)

    df_temp = df[df[col_esp] == esp_sel] if esp_sel != "Todos" else df
    
    lista_ciudades = ["Todas"] + sorted(df_temp[col_ciudad].dropna().unique().tolist())
    ciudad_sel = st.sidebar.selectbox("Seleccione Municipio:", lista_ciudades)

    # DataFrame Filtrado Final
    df_filtrado = df_temp.copy()
    if ciudad_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado[col_ciudad] == ciudad_sel]

    # --- PESTAÑAS DE NAVEGACIÓN ---
    tab1, tab2, tab3, tab4 = st.tabs(["📍 Consulta", "📈 Tendencia Semestral", "🏆 Top 50", "🚨 Alertas"])

    with tab1:
        st.subheader("📊 Resumen de la Selección")
        m1, m2, m3 = st.columns(3)
        m1.metric("Puntos Encontrados", f"{len(df_filtrado):,}")
        m2.metric("Especialista", esp_sel if esp_sel != "Todos" else "Nacional")
        m3.metric("Transacciones Totales", f"{df_filtrado[col_tx_total].sum():,.0f}")

        st.divider()
        busqueda = st.text_input("🔍 Búsqueda rápida (Dirección, nombre, etc.):")
        if busqueda:
            df_filtrado = df_filtrado[df_filtrado.astype(str).apply(lambda x: x.str.contains(busqueda, case=False, na=False)).any(axis=1)]

        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
        
        csv = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Reporte CSV", csv, "consulta_bvb.csv", "text/csv")

    with tab2:
        st.subheader("📈 Evolución de Transacciones (Julio 2025 - Enero 2026)")
        meses = ["Jul 2025 TX", "Ago 2025 TX", "Sep 2025 TX", "Oct 2025 TX", "Nov 2025 TX", "Dic 2025 TX", "Ene 2026 TX"]
        cols_v = [m for m in meses if m in cols]
        if cols_v:
            df_t = df_filtrado[cols_v].sum().reset_index()
            df_t.columns = ["Mes", "Total TX"]
            fig = px.line(df_t, x="Mes", y="Total TX", markers=True, color_discrete_sequence=["#0033a0"])
            st.plotly_chart(fig, use_container_width=True)
        
        top_mun = df_filtrado.groupby(col_ciudad)[col_tx_total].sum().nlargest(10).reset_index()
        fig_bar = px.bar(top_mun, x=col_tx_total, y=col_ciudad, orientation='h', title="Top 10 Municipios por Volumen")
        st.plotly_chart(fig_bar, use_container_width=True)

    with tab3:
        st.subheader("🏆 Ranking Top 50 Corresponsales VIP")
        top_50 = df.nlargest(50, col_tx_total)
        st.dataframe(top_50[[col_esp, col_ciudad, col_dir, col_tx_total]], use_container_width=True, hide_index=True)

    with tab4:
        st.subheader("🚨 Gestión de Puntos Inactivos")
        # Identificar los que marcan "No" en transaccionalidad o tienen 0
        df_al = df[df[col_alerta] == "No"].copy() if col_alerta in cols else df[df[col_tx_total] == 0].copy()
        
        if not df_al.empty:
            st.warning(f"Se identificaron {len(df_al)} puntos que requieren gestión urgente.")
            esp_lista = st.selectbox("Filtrar Alertas por Especialista Comercial:", ["Todos"] + sorted(df_al[col_esp].unique().tolist()))
            if esp_lista != "Todos":
                df_al = df_al[df_al[col_esp] == esp_lista]
            st.dataframe(df_al[[col_esp, col_ciudad, col_dir, col_tx_total]], use_container_width=True, hide_index=True)
        else:
            st.success("✅ ¡Felicidades! Todos los puntos están transando activamente.")

else:
    st.warning("⚠️ Esperando carga de datos...")
