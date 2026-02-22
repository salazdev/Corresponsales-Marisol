import streamlit as st
import pandas as pd
import plotly.express as px
import io

# 1. CONFIGURACIÓN
st.set_page_config(page_title="BVB - Gestión Comercial", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    [data-testid="stMetricValue"] { color: #0033a0 !important; font-weight: bold; }
    div[data-testid="stMetric"] { 
        background-color: #ffffff; border-left: 5px solid #EBB932; 
        border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 Panel de Gestión Comercial BVB")

# 2. MOTOR DE CARGA "ANTIBALAS" (on_bad_lines='skip')
@st.cache_data(ttl=60)
def cargar_datos_seguro():
    try:
        # Cargamos el archivo ignorando filas que tengan más columnas de las permitidas
        df = pd.read_csv(
            "datos_corresponsales.csv", 
            sep=None, 
            engine='python', 
            on_bad_lines='skip', 
            encoding_errors='ignore'
        )
        
        # Limpieza de nombres de columnas (quitar saltos de línea de Excel)
        df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
        
        # Resolver duplicados (Ciudad, Ciudad_1)
        cols = pd.Series(df.columns)
        for i, col in enumerate(cols):
            if (cols == col).sum() > 1:
                count = list(cols[:i]).count(col)
                if count > 0: cols[i] = f"{col}_{count}"
        df.columns = cols

        # Convertir datos a números (TX y $$)
        for col in df.columns:
            if any(x in col.upper() for x in ["TX", "$$", "TRANSA", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC", "ENE"]):
                df[col] = df[col].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False).str.strip()
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Error técnico: {e}")
        return None

df = cargar_datos_seguro()

if df is not None:
    # Identificación de columnas dinámicas
    col_esp = next((c for c in df.columns if "ESPECIALISTA" in c.upper()), df.columns[0])
    col_mun = next((c for c in df.columns if "CIUDAD" in c.upper()), df.columns[1])
    col_estado = next((c for c in df.columns if "ESTADO" in c.upper()), None)
    col_tx_total = next((c for c in df.columns if "TX ULTIMO SEMESTRE" in c.upper()), None)
    col_si_no = next((c for c in df.columns if "TRANSA SI/NO MES" in c.upper()), None)

    # --- FILTROS ---
    st.sidebar.header("🔍 Filtros")
    esp_sel = st.sidebar.selectbox("Especialista:", ["TODOS"] + sorted(df[col_esp].unique().astype(str).tolist()))
    mun_sel = st.sidebar.selectbox("Municipio:", ["TODOS"] + sorted(df[col_mun].unique().astype(str).tolist()))

    df_f = df.copy()
    if esp_sel != "TODOS": df_f = df_f[df_f[col_esp] == esp_sel]
    if mun_sel != "TODOS": df_f = df_f[df_f[col_mun] == mun_sel]

    # --- MÉTRICAS ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Puntos", f"{len(df_f)}")
    if col_tx_total:
        c2.metric("TX Semestre", f"{df_f[col_tx_total].sum():,.0f}")
    
    col_ene_tx = next((c for c in df.columns if "ENE 2026 TX" in c.upper()), None)
    if col_ene_tx:
        c3.metric("TX Ene 2026", f"{df_f[col_ene_tx].sum():,.0f}")
        
    if col_si_no:
        con_tx = len(df_f[df_f[col_si_no].astype(str).str.upper().str.contains("SI")])
        c4.metric("Activos (Si)", con_tx)

    # --- TABS ---
    t1, t2, t3 = st.tabs(["📊 Niveles y Estados", "🏆 Top 50", "📈 Tendencia Semestre"])

    with t1:
        if col_estado:
            st.plotly_chart(px.pie(df_f, names=col_estado, title="Proporción por Estado", hole=0.4), use_container_width=True)
        else:
            st.info("No se encontró la columna 'Estado'")

    with t2:
        if col_tx_total:
            top_50 = df_f.nlargest(50, col_tx_total)
            st.dataframe(top_50[[col_esp, col_mun, 'Dirección', col_tx_total]], use_container_width=True, hide_index=True)

    with t3:
        meses = ["JUL", "AGO", "SEP", "OCT", "NOV", "DIC", "ENE"]
        data_ev = []
        for m in meses:
            c_tx = next((c for c in df.columns if m in c.upper() and "TX" in c.upper()), None)
            c_money = next((c for c in df.columns if m in c.upper() and "$$" in c.upper()), None)
            if c_tx: data_ev.append({"Mes": m, "Tipo": "TX (Cant)", "Valor": df_f[c_tx].sum()})
            if c_money: data_ev.append({"Mes": m, "Tipo": "$$ (Valor)", "Valor": df_f[c_money].sum()})
        
        if data_ev:
            st.plotly_chart(px.line(pd.DataFrame(data_ev), x="Mes", y="Valor", color="Tipo", markers=True), use_container_width=True)

    st.divider()
    st.subheader("📋 Datos Detallados")
    st.dataframe(df_f, use_container_width=True, hide_index=True)

else:
    st.info("📢 Cargando... Verifica el archivo en GitHub.")
