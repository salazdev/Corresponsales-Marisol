import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="BVB - Gestión Comercial", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div[data-testid="stMetric"] { 
        background-color: #ffffff; border-left: 5px solid #EBB932; 
        border-radius: 10px; padding: 5px 15px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); height: 100px;
        display: flex; flex-direction: column; justify-content: center;
    }
    div[data-testid="stMetricLabel"] { margin-top: -10px !important; margin-bottom: -10px !important; font-size: 0.85rem !important; font-weight: bold !important; color: #666 !important; }
    div[data-testid="stMetricValue"] { color: #0033a0 !important; font-size: 2.2rem !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 Panel de Gestión Comercial BVB")

# 2. MOTOR DE CARGA CON DESDUPLICACIÓN DE COLUMNAS (Solución al DuplicateError)
@st.cache_data(ttl=60)
def cargar_datos_sin_duplicados():
    for s in [';', ',', '\t']:
        try:
            df = pd.read_csv("datos_corresponsales.csv", sep=s, engine='python', on_bad_lines='skip', encoding_errors='ignore')
            if len(df.columns) > 1:
                # 1. Limpiar nombres básicos
                df.columns = [str(c).upper().strip() for c in df.columns]
                
                # 2. RENOMBRAR DUPLICADOS (Evita el error de Narwhals/Plotly)
                cols = []
                count = {}
                for column in df.columns:
                    if column not in count:
                        cols.append(column)
                        count[column] = 0
                    else:
                        count[column] += 1
                        cols.append(f"{column}_{count[column]}")
                df.columns = cols
                
                # 3. Limpiar datos numéricos
                for c in df.columns:
                    if any(x in c for x in ["TX", "$$", "ENE", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]):
                        df[c] = df[c].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False).str.strip()
                        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
                return df
        except:
            continue
    return None

df = cargar_datos_sin_duplicados()

if df is not None:
    # --- IDENTIFICACIÓN DE COLUMNAS ---
    col_esp = next((c for c in df.columns if "ESPEC" in c), df.columns[0])
    col_mun = next((c for c in df.columns if "CIUD" in c or "MUN" in c), df.columns[1])
    col_tx_total = next((c for c in df.columns if "TX ULTIMO SEMESTRE" in c or "TOTAL TX" in c), None)
    col_money = next((c for c in df.columns if "ENE 2026 $$" in c or "ENE 2026 $" in c), None)
    col_estado = next((c for c in df.columns if "ESTADO" in c), None)
    col_si_no = next((c for c in df.columns if "TRANSA SI/NO" in c), None)

    # --- FILTROS ---
    st.sidebar.header("🔍 Filtros")
    esp_sel = st.sidebar.selectbox("Especialista:", ["TODOS"] + sorted([str(x) for x in df[col_esp].unique() if str(x) not in ['nan', '0']]))
    mun_sel = st.sidebar.selectbox("Ciudad:", ["TODOS"] + sorted([str(x) for x in df[col_mun].unique() if str(x) not in ['nan', '0']]))

    df_f = df.copy()
    if esp_sel != "TODOS": df_f = df_f[df_f[col_esp] == esp_sel]
    if mun_sel != "TODOS": df_f = df_f[df_f[col_mun] == mun_sel]

    # --- KPIs ---
    st.subheader("🚀 Indicadores")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Puntos Red", f"{len(df_f)}")
    k2.metric("TX Semestre", f"{df_f[col_tx_total].sum() if col_tx_total else 0:,.0f}")
    k3.metric("Monto Ene ($)", f"$ {df_f[col_money].sum() if col_money else 0:,.0f}")
    if col_si_no:
        activos = len(df_f[df_f[col_si_no].astype(str).str.upper().str.contains("SI")])
        k4.metric("Activos (Si)", activos)
    else: k4.metric("Activos", "0")

    # --- GRÁFICOS ---
    t1, t2, t3 = st.tabs(["📊 Segmentación", "🏆 Top 50", "📋 Datos"])
    
    with t1:
        c_a, c_b = st.columns(2)
        with c_a:
            if col_estado:
                # Aseguramos que df_pie no tenga nombres de columnas duplicados
                df_pie = df_f[[col_estado]].copy() 
                df_pie = df_pie[~df_pie[col_estado].astype(str).isin(['0', 'nan', 'NAN'])]
                if not df_pie.empty:
                    fig = px.pie(df_pie, names=col_estado, title="Nivel Master/Medio", hole=0.4)
                    st.plotly_chart(fig, use_container_width=True)
        with c_b:
            if col_tx_total:
                top_muns = df_f.groupby(col_mun)[col_tx_total].sum().nlargest(10).reset_index()
                st.plotly_chart(px.bar(top_muns, x=col_tx_total, y=col_mun, orientation='h', title="Top Ciudades"), use_container_width=True)

    with t2:
        if col_tx_total:
            st.dataframe(df_f.nlargest(50, col_tx_total)[[col_esp, col_mun, col_tx_total]], use_container_width=True, hide_index=True)

    with t3:
        st.dataframe(df_f, use_container_width=True)
else:
    st.error("🚨 Error leyendo el archivo. Revisa los nombres de las columnas en tu Excel.")
