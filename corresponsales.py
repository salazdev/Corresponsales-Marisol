import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DE LA APP
st.set_page_config(page_title="BVB - Gestión Comercial", layout="wide")

# ESTILO CSS PARA IDENTIDAD VISUAL
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

# 2. CARGA DE DATOS CON SOLUCIÓN PARA COLUMNAS DUPLICADAS
@st.cache_data(ttl=3600)
def cargar_datos_locales():
    try:
        # Carga inicial
        df = pd.read_csv("datos_corresponsales.csv", on_bad_lines='skip', engine='python')
        
        # --- SOLUCIÓN AL ERROR DE DUPLICADOS ---
        # Este bloque renombra columnas repetidas (ej: 'Ciudad' -> 'Ciudad', 'Ciudad.1')
        cols = pd.Series(df.columns)
        for i, col in enumerate(cols):
            if (cols == col).sum() > 1:
                count = list(cols[:i]).count(col)
                if count > 0:
                    cols[i] = f"{col}.{count}"
        df.columns = [str(c).strip() for c in cols]
        
        # Limpieza de datos financieros (quitar $ y comas)
        cols_fin = [c for c in df.columns if any(x in c for x in ["2025", "2026", "TX", "$", "Transa"])]
        for col in cols_fin:
            if df[col].dtype == 'object':
                df[col] = df[col].str.replace('$', '', regex=False).str.replace(',', '', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
        return df
    except Exception as e:
        st.error(f"Error al cargar el archivo: {e}")
        return None

df = cargar_datos_locales()

if df is not None:
    # Identificación dinámica de columnas
    cols = list(df.columns)
    col_ciudad = next((c for c in cols if "ciudad" in c.lower()), "Ciudad")
    col_esp = next((c for c in cols if "especialista" in c.lower()), "ESPECIALISTA")
    col_dir = next((c for c in cols if "dirección" in c.lower() or "direccion" in c.lower()), "Dirección")
    col_tx_total = "Tx Ultimo Semestre" if "Tx Ultimo Semestre" in cols else (next((c for c in cols if "transa" in c.lower()), cols[0]))
    col_alerta = "Transa si/no MES"

    # --- FILTROS ---
    st.sidebar.header("🔍 Criterios de Consulta")
    lista_esp = ["Todos"] + sorted(df[col_esp].dropna().unique().tolist())
    esp_sel = st.sidebar.selectbox("Seleccione Especialista:", lista_esp)

    df_temp = df[df[col_esp] == esp_sel] if esp_sel != "Todos" else df
    lista_ciudades = ["Todas"] + sorted(df_temp[col_ciudad].dropna().unique().tolist())
    ciudad_sel = st.sidebar.selectbox("Seleccione Municipio:", lista_ciudades)

    # Filtrado final
    df_filtrado = df_temp.copy()
    if ciudad_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado[col_ciudad] == ciudad_sel]

    # --- PESTAÑAS ---
    tab1, tab2, tab3, tab4 = st.tabs(["📍 Consulta", "📈 Análisis Semestral", "🏆 Top 50 VIP", "🚨 Alertas"])

    with tab1:
        st.subheader("📊 Resumen de Selección")
        m1, m2, m3 = st.columns(3)
        m1.metric("Puntos Encontrados", f"{len(df_filtrado):,}")
        m2.metric("Especialista Comercial", esp_sel if esp_sel != "Todos" else "Nivel Nacional")
        m3.metric("Transacciones Totales", f"{df_filtrado[col_tx_total].sum():,.0f}")

        st.divider()
        busqueda = st.text_input("🔍 Buscar por dirección o nombre:")
        if busqueda:
            df_filtrado = df_filtrado[df_filtrado.astype(str).apply(lambda x: x.str.contains(busqueda, case=False, na=False)).any(axis=1)]

        # Visualización de la tabla
        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
        
        csv = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Reporte CSV", csv, "reporte_bvb.csv", "text/csv")

    with tab2:
        st.subheader("📈 Evolución Transaccional (Jul 2025 - Ene 2026)")
        meses = ["Jul 2025 TX", "Ago 2025 TX", "Sep 2025 TX", "Oct 2025 TX", "Nov 2025 TX", "Dic 2025 TX", "Ene 2026 TX"]
        cols_v = [m for m in meses if m in cols]
        if cols_v:
            df_t = df_filtrado[cols_v].sum().reset_index()
            df_t.columns = ["Mes", "Total TX"]
            fig = px.line(df_t, x="Mes", y="Total TX", markers=True, color_discrete_sequence=["#0033a0"])
            st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.subheader("🏆 Ranking Top 50 Nacional")
        top_50 = df.nlargest(50, col_tx_total)
        st.dataframe(top_50[[col_esp, col_ciudad, col_dir, col_tx_total]], use_container_width=True, hide_index=True)

    with tab4:
        st.subheader("🚨 Gestión de Puntos Inactivos")
        df_al = df[df[col_alerta] == "No"].copy() if col_alerta in cols else df[df[col_tx_total] == 0].copy()
        
        if not df_al.empty:
            st.error(f"Se identificaron {len(df_al)} puntos con baja actividad.")
            esp_lista = st.selectbox("Filtrar Alertas por Especialista:", ["Todos"] + sorted(df_al[col_esp].unique().tolist()))
            if esp_lista != "Todos":
                df_al = df_al[df_al[col_esp] == esp_lista]
            st.dataframe(df_al[[col_esp, col_ciudad, col_dir, col_tx_total]], use_container_width=True, hide_index=True)
        else:
            st.success("✅ Red activa al 100%.")

else:
    st.warning("⚠️ Cargando datos localmente...")
