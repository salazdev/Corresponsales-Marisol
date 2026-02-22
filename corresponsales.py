import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="BVB - Gestión Estratégica", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    [data-testid="stMetricValue"] { color: #0033a0 !important; font-weight: bold; }
    div[data-testid="stMetric"] { background-color: #ffffff; border-radius: 10px; border-left: 5px solid #EBB932; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 Panel de Gestión Comercial BVB")

# 2. MOTOR DE CARGA ULTRA-ROBUSTO
@st.cache_data(ttl=300)
def cargar_datos_seguro():
    rutas_y_formatos = [
        {'encoding': 'utf-8', 'sep': ','},
        {'encoding': 'latin-1', 'sep': ';'},
        {'encoding': 'utf-16', 'sep': '\t'},
        {'encoding': 'cp1252', 'sep': ','}
    ]
    
    df = None
    for formato in rutas_y_formatos:
        try:
            df = pd.read_csv(
                "datos_corresponsales.csv", 
                encoding=formato['encoding'], 
                sep=formato['sep'],
                engine='python',
                on_bad_lines='skip'
            )
            if len(df.columns) > 1: # Si detectó más de una columna, funcionó
                break
        except:
            continue

    if df is None or df.empty:
        return None

    # --- LIMPIEZA DE COLUMNAS REPETIDAS (Evita el ValueError) ---
    cols_limpias = []
    seen = {}
    for c in df.columns:
        nombre = str(c).strip()
        if nombre in seen:
            seen[nombre] += 1
            cols_limpias.append(f"{nombre}_{seen[nombre]}")
        else:
            seen[nombre] = 0
            cols_limpias.append(nombre)
    df.columns = cols_limpias

    # --- LIMPIEZA DE NÚMEROS ($ y TX) ---
    for col in df.columns:
        if any(x in col.upper() for x in ["TX", "$$", "TRANSA", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC", "ENE"]):
            df[col] = df[col].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False).str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    return df

df = cargar_datos_seguro()

if df is not None:
    # 3. IDENTIFICACIÓN DE COLUMNAS PARA LOS DESPLEGABLES
    col_mun = next((c for c in df.columns if "CIUDAD" in c.upper()), "Ciudad")
    col_esp = next((c for c in df.columns if "ESPECIALISTA" in c.upper()), "ESPECIALISTA")
    col_tx_total = next((c for c in df.columns if "TX ULTIMO SEMESTRE" in c.upper()), "Tx Ultimo Semestre")
    col_money = next((c for c in df.columns if "ENE 2026 $$" in c.upper()), None)

    # --- DESPLEGABLES COMPLETOS EN LA BARRA LATERAL ---
    st.sidebar.header("🔍 Consultar Información")
    
    # Filtro Especialista
    opciones_esp = ["TODOS LOS ESPECIALISTAS"] + sorted([str(x) for x in df[col_esp].unique() if pd.notna(x)])
    esp_sel = st.sidebar.selectbox("Especialista Comercial:", opciones_esp)
    
    # Filtro Municipio
    opciones_mun = ["TODOS LOS MUNICIPIOS"] + sorted([str(x) for x in df[col_mun].unique() if pd.notna(x)])
    mun_sel = st.sidebar.selectbox("Municipio / Ciudad:", opciones_mun)
    
    # Filtro Estado
    col_estado = next((c for c in df.columns if "ESTADO" in c.upper()), None)
    if col_estado:
        opciones_est = ["TODOS LOS ESTADOS"] + sorted([str(x) for x in df[col_estado].unique() if pd.notna(x)])
        est_sel = st.sidebar.selectbox("Estado del Corresponsal:", opciones_est)

    # Aplicar Filtros
    df_f = df.copy()
    if esp_sel != "TODOS LOS ESPECIALISTAS":
        df_f = df_f[df_f[col_esp] == esp_sel]
    if mun_sel != "TODOS LOS MUNICIPIOS":
        df_f = df_f[df_f[col_mun] == mun_sel]
    if col_estado and est_sel != "TODOS LOS ESTADOS":
        df_f = df_f[df_f[col_estado] == est_sel]

    # --- MÉTRICAS ---
    m1, m2, m3 = st.columns(3)
    m1.metric("Número de Corresponsales", f"{len(df_f):,}")
    m2.metric("Total Transacciones (Semestre)", f"{df_f[col_tx_total].sum():,.0f}")
    if col_money:
        m3.metric("Monto Dinero Enero 2026", f"$ {df_f[col_money].sum():,.0f}")

    # --- PESTAÑAS DE ANÁLISIS ---
    t1, t2, t3 = st.tabs(["📊 Análisis por Municipio", "🏆 Top 50 Clientes", "📅 Histórico Mensual"])

    with t1:
        st.subheader("Desempeño por Ubicación Geográfica")
        mun_data = df_f.groupby(col_mun)[col_tx_total].sum().nlargest(15).reset_index()
        fig_mun = px.bar(mun_data, x=col_tx_total, y=col_mun, orientation='h', 
                         title="Top Municipios con más Transacciones", color_discrete_sequence=['#0033a0'])
        st.plotly_chart(fig_mun, use_container_width=True)

    with t2:
        st.subheader("🏆 Ranking Top 50 Nacional")
        top_50 = df.nlargest(50, col_tx_total)
        columnas_ver = [col_esp, col_mun, 'Dirección', col_tx_total]
        columnas_ver = [c for c in columnas_ver if c in top_50.columns]
        st.dataframe(top_50[columnas_ver], use_container_width=True, hide_index=True)

    with t3:
        st.subheader("Análisis del Último Semestre (Jul 2025 - Ene 2026)")
        # Buscar columnas de meses dinámicamente
        meses = ["JUL", "AGO", "SEP", "OCT", "NOV", "DIC", "ENE"]
        datos_linea = []
        for m in meses:
            col_m = next((c for c in df.columns if m in c.upper() and "TX" in c.upper()), None)
            if col_m:
                datos_linea.append({"Mes": m, "TX": df_f[col_m
