import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN
st.set_page_config(page_title="BVB Dashboard", layout="wide")

st.markdown("""
    <style>
    [data-testid="stMetricValue"] { color: #0033a0 !important; font-weight: bold; }
    div[data-testid="stMetric"] { background-color: #ffffff; border-left: 5px solid #EBB932; padding: 10px; border-radius: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 Panel de Gestión Comercial BVB")

# 2. CARGA DE DATOS ULTRA-FLEXIBLE
@st.cache_data(ttl=60)
def cargar_datos_final():
    try:
        # Intento de lectura universal
        df = pd.read_csv("datos_corresponsales.csv", sep=None, engine='python', encoding_errors='ignore')
        
        # Limpiar nombres de columnas
        df.columns = [str(c).strip() for c in df.columns]
        
        # Resolver nombres duplicados (como Ciudad y Ciudad.1)
        cols = pd.Series(df.columns)
        for i, col in enumerate(cols):
            if (cols == col).sum() > 1:
                count = list(cols[:i]).count(col)
                if count > 0:
                    cols[i] = f"{col}_{count}"
        df.columns = cols

        # Convertir a número lo que sea financiero o transaccional
        for col in df.columns:
            if any(x in col.upper() for x in ["TX", "$$", "TRANSA", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC", "ENE"]):
                df[col] = df[col].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False).str.strip()
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except Exception as e:
        return None

df = cargar_datos_final()

if df is not None:
    # IDENTIFICAR COLUMNAS SEGÚN TU LISTA
    col_mun = next((c for c in df.columns if "CIUDAD" in c.upper()), df.columns[1])
    col_esp = next((c for c in df.columns if "ESPECIALISTA" in c.upper()), df.columns[3])
    col_tx_total = next((c for c in df.columns if "TX ULTIMO SEMESTRE" in c.upper()), "Tx Ultimo Semestre")
    col_ene_money = next((c for c in df.columns if "ENE 2026 $$" in c.upper()), None)

    # --- FILTROS (DESPLEGABLES COMPLETOS) ---
    st.sidebar.header("🔍 Filtros Principales")
    
    esp_list = ["TODOS"] + sorted(df[col_esp].unique().astype(str).tolist())
    esp_sel = st.sidebar.selectbox("Especialista Comercial:", esp_list)
    
    mun_list = ["TODOS"] + sorted(df[col_mun].unique().astype(str).tolist())
    mun_sel = st.sidebar.selectbox("Municipio / Ciudad:", mun_list)

    # Filtrado
    df_f = df.copy()
    if esp_sel != "TODOS": df_f = df_f[df_f[col_esp] == esp_sel]
    if mun_sel != "TODOS": df_f = df_f[df_f[col_mun] == mun_sel]

    # --- MÉTRICAS ---
    c1, c2, c3 = st.columns(3)
    c1.metric("Corresponsales", f"{len(df_f):,}")
    c2.metric("TX Totales (Semestre)", f"{df_f[col_tx_total].sum():,.0f}")
    if col_ene_money:
        c3.metric("Monto Ene 2026", f"$ {df_f[col_ene_money].sum():,.0f}")

    # --- PESTAÑAS DE ANÁLISIS ---
    tab1, tab2, tab3 = st.tabs(["📊 Análisis Geográfico", "🏆 Top 50 Clientes", "📅 Tendencia"])

    with tab1:
        st.subheader("Análisis por Municipio")
        top_muns = df_f.groupby(col_mun)[col_tx_total].sum().nlargest(15).reset_index()
        fig_mun = px.bar(top_muns, x=col_tx_total, y=col_mun, orientation='h', 
                         title="Ranking de Municipios", color_discrete_sequence=['#0033a0'])
        st.plotly_chart(fig_mun, use_container_width=True)

    with tab2:
        st.subheader("🏆 Top 50 Corresponsales que más Transan")
        top_50 = df.nlargest(50, col_tx_total)
        st.dataframe(top_50[[col_esp, col_mun, 'Dirección', col_tx_total]], use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("Evolución Mensual (Julio - Enero)")
        meses = ["JUL", "AGO", "SEP", "OCT", "NOV", "DIC", "ENE"]
        line_data = []
        for m in meses:
            col_m = next((c for c in df.columns if m in c.upper() and "TX" in c.upper()), None)
            if col_m:
                line_data.append({"Mes": m, "Transacciones": df_f[col_m].sum()})
        
        if line_data:
            df_l = pd.DataFrame(line_data)
            st.plotly_chart(px.line(df_l, x="Mes", y="Transacciones", markers=True), use_container_width=True)

    # TABLA FINAL
    st.divider()
    st.subheader("📋 Detalle de Corresponsales")
    busqueda = st.text_input("Buscar en la tabla (Nombre, Dirección, etc):")
    if busqueda:
        df_f = df_f[df_f.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]
    st.dataframe(df_f, use_container_width=True, hide_index=True)

else:
    st.error("🚨 Error de lectura. Por favor, asegúrate de que el archivo se llame 'datos_corresponsales.csv' y esté en GitHub.")
