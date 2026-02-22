import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. CONFIGURACIÓN VISUAL
st.set_page_config(page_title="BVB - Gestión Comercial", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div[data-testid="stMetric"] { 
        background-color: #ffffff; border-left: 5px solid #EBB932; 
        border-radius: 10px; padding: 5px 15px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); height: 110px;
        display: flex; flex-direction: column; justify-content: center;
    }
    div[data-testid="stMetricLabel"] { margin-bottom: -10px !important; font-size: 0.9rem !important; font-weight: bold !important; color: #555 !important; }
    div[data-testid="stMetricValue"] { color: #0033a0 !important; font-size: 2.2rem !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 Panel de Gestión Comercial BVB")

# 2. MOTOR DE BÚSQUEDA DE ARCHIVO Y CARGA
@st.cache_data(ttl=60)
def cargar_datos_extremo():
    # Buscamos cualquier archivo que termine en .csv en la carpeta
    archivos = [f for f in os.listdir('.') if f.endswith('.csv')]
    nombre_archivo = "datos_corresponsales.csv" if "datos_corresponsales.csv" in archivos else (archivos[0] if archivos else None)
    
    if not nombre_archivo:
        return None

    for s in [';', ',', '\t']:
        try:
            df = pd.read_csv(nombre_archivo, sep=s, engine='python', on_bad_lines='skip', encoding_errors='ignore')
            if len(df.columns) > 2:
                # Renombrar duplicados
                nuevos_nombres = []
                for i, col in enumerate(df.columns):
                    nombre = str(col).upper().strip().replace('\n', ' ')
                    if nombre in nuevos_nombres or nombre == "":
                        nuevos_nombres.append(f"{nombre}_{i}")
                    else:
                        nuevos_nombres.append(nombre)
                df.columns = nuevos_nombres
                
                # Limpiar números
                for c in df.columns:
                    if any(x in c for x in ["TX", "$$", "ENE", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]):
                        df[c] = df[c].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False).str.strip()
                        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
                return df
        except:
            continue
    return None

df = cargar_datos_extremo()

if df is not None:
    # Identificar columnas
    def encontrar_col(keywords, pos):
        for k in keywords:
            for c in df.columns:
                if k in c: return c
        return df.columns[pos]

    c_esp = encontrar_col(["ESPEC"], 3)
    c_mun = encontrar_col(["CIUD", "MUN"], 1)
    c_tx_total = encontrar_col(["TX ULTIMO SEMESTRE", "TOTAL TX", "TX"], len(df.columns)-2)
    c_money = encontrar_col(["ENE 2026 $$", "ENE 2026 $", "$$"], len(df.columns)-3)
    c_estado = encontrar_col(["ESTADO"], 8)
    c_si_no = encontrar_col(["SI/NO"], 10)

    # --- FILTROS ---
    st.sidebar.header("🔍 Filtros")
    esp_sel = st.sidebar.selectbox("Especialista:", ["TODOS"] + sorted([str(x) for x in df[c_esp].unique() if str(x) not in ['nan', '0']]))
    mun_sel = st.sidebar.selectbox("Municipio:", ["TODOS"] + sorted([str(x) for x in df[c_mun].unique() if str(x) not in ['nan', '0']]))

    df_f = df.copy()
    if esp_sel != "TODOS": df_f = df_f[df_f[c_esp] == esp_sel]
    if mun_sel != "TODOS": df_f = df_f[df_f[c_mun] == mun_sel]

    # --- KPIs ---
    st.subheader("🚀 Indicadores Clave")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Puntos Red", f"{len(df_f)}")
    c2.metric("TX Semestre", f"{df_f[c_tx_total].sum():,.0f}")
    c3.metric("Monto Ene ($)", f"$ {df_f[c_money].sum():,.0f}")
    activos = len(df_f[df_f[c_si_no].astype(str).str.upper().str.contains("SI")]) if c_si_no in df_f.columns else 0
    c4.metric("Activos (Si)", activos)

    # --- PESTAÑAS ---
    tab1, tab2, tab3 = st.tabs(["📊 Análisis", "🏆 Top 50", "📋 Base de Datos"])

    with tab1:
        izq, der = st.columns(2)
        with izq:
            if c_estado in df_f.columns:
                df_pie = df_f[~df_f[c_estado].astype(str).isin(['0', 'nan', '0.0'])]
                if not df_pie.empty:
                    st.plotly_chart(px.pie(df_pie, names=c_estado, title="Distribución de Niveles", hole=0.4), use_container_width=True)
        with der:
            top_muns = df_f.groupby(c_mun)[c_tx_total].sum().nlargest(10).reset_index()
            st.plotly_chart(px.bar(top_muns, x=c_tx_total, y=c_mun, orientation='h', title="Top 10 Municipios"), use_container_width=True)

    with tab2:
        st.subheader("🏆 Ranking Top 50 Corresponsales")
        top_50 = df_f.sort_values(by=c_tx_total, ascending=False).head(50)
        st.dataframe(top_50[[c_esp, c_mun, c_tx_total, c_money]], use_container_width=True, hide_index=True)

    with tab3:
        st.dataframe(df_f, use_container_width=True)

else:
    st.error("🚨 No se encontró el archivo CSV.")
    st.info(f"Archivos detectados en el servidor: {os.listdir('.')}")
