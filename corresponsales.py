import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN
st.set_page_config(page_title="BVB - Gestión Comercial", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div[data-testid="stMetric"] { 
        background-color: #ffffff; 
        border-left: 5px solid #EBB932; 
        border-radius: 10px; 
        padding: 5px 15px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        height: 110px;
    }
    div[data-testid="stMetricLabel"] {
        margin-bottom: -10px !important;
        font-size: 0.9rem !important;
        font-weight: bold !important;
    }
    div[data-testid="stMetricValue"] { 
        color: #0033a0 !important; 
        font-size: 2.1rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 Panel de Gestión Comercial BVB")

# 2. MOTOR DE CARGA "ULTRA-RESISTENTE"
@st.cache_data(ttl=60)
def cargar_datos_final():
    try:
        # Intento de lectura con parámetros de máxima tolerancia
        df = pd.read_csv(
            "datos_corresponsales.csv", 
            sep=None, 
            engine='python', 
            on_bad_lines='skip', 
            encoding_errors='ignore',
            decimal=','
        )
        
        if len(df.columns) > 1:
            # Limpieza profunda de nombres de columnas
            df.columns = [str(c).replace('\n', ' ').strip().upper() for c in df.columns]
            
            # Limpieza de datos numéricos
            for col in df.columns:
                if any(x in col for x in ["TX", "$$", "TRANSA", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC", "ENE"]):
                    df[col] = df[col].astype(str).str.replace('$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            return df
        return None
    except:
        return None

df = cargar_datos_final()

if df is not None:
    # Búsqueda dinámica de columnas
    col_esp = next((c for c in df.columns if "ESPECIALISTA" in c), df.columns[0])
    col_mun = next((c for c in df.columns if "CIUDAD" in c), df.columns[1])
    col_estado = next((c for c in df.columns if "ESTADO" in c), None)
    col_tx_total = next((c for c in df.columns if "TX ULTIMO SEMESTRE" in c or "TRANSA" in c), None)
    col_money_ene = next((c for c in df.columns if "ENE 2026 $$" in c or "ENE 2026 $" in c), None)
    col_si_no = next((c for c in df.columns if "TRANSA SI/NO MES" in c), None)

    # --- FILTROS ---
    st.sidebar.header("🔍 Consultar")
    esp_sel = st.sidebar.selectbox("Especialista:", ["TODOS"] + sorted(df[col_esp].unique().astype(str).tolist()))
    mun_sel = st.sidebar.selectbox("Municipio:", ["TODOS"] + sorted(df[col_mun].unique().astype(str).tolist()))

    df_f = df.copy()
    if esp_sel != "TODOS": df_f = df_f[df_f[col_esp] == esp_sel]
    if mun_sel != "TODOS": df_f = df_f[df_f[col_mun] == mun_sel]

    # --- MÉTRICAS ---
    st.subheader("🚀 Indicadores de Gestión")
    c1, c2, c3, c4 = st.columns(4)
    
    c1.metric("Corresponsales", f"{len(df_f)}")
    
    val_tx = df_f[col_tx_total].sum() if col_tx_total else 0
    c2.metric("TX Semestre", f"{val_tx:,.0f}")
    
    val_money = df_f[col_money_ene].sum() if col_money_ene else 0
    c3.metric("Monto Enero ($$)", f"$ {val_money:,.0f}")
        
    if col_si_no:
        con_tx = len(df_f[df_f[col_si_no].astype(str).str.upper().str.contains("SI")])
        c4.metric("Activos (Si)", con_tx)
    else:
        c4.metric("Activos", "0")

    # --- ANÁLISIS ---
    tab1, tab2, tab3 = st.tabs(["📊 Segmentación", "🏆 Ranking Top 50", "📈 Tendencia"])

    with tab1:
        st.subheader("Análisis de Segmentación")
        col_a, col_b = st.columns(2)
        with col_a:
            if col_estado:
                df_pie = df_f[~df_f[col_estado].isin(['0', 0, 'NAN'])]
                fig_pie = px.pie(df_pie, names=col_estado, hole=0.4, title="Nivel Master/Medio")
                st.plotly_chart(fig_pie, use_container_width=True)
        with col_b:
            if col_tx_total:
                top_mun = df_f.groupby(col_mun)[col_tx_total].sum().nlargest(10).reset_index()
                st.plotly_chart(px.bar(top_mun, x=col_tx_total, y=col_mun, orientation='h', title="Top Municipios"), use_container_width=True)

    with tab2:
        if col_tx_total:
            top_50 = df_f.nlargest(50, col_tx_total)
            st.dataframe(top_50[[col_esp, col_mun, col_tx_total]], use_container_width=True, hide_index=True)

    with tab3:
        meses = ["JUL", "AGO", "SEP", "OCT", "NOV", "DIC", "ENE"]
        data_ev = []
        for m in meses:
            c_tx = next((c for c in df.columns if m in c and "TX" in c), None)
            if c_tx: data_ev.append({"Mes": m, "Transacciones": df_f[c_tx].sum()})
        if data_ev:
            st.plotly_chart(px.line(pd.DataFrame(data_ev), x="Mes", y="Transacciones", markers=True), use_container_width=True)

    st.divider()
    st.subheader("📋 Datos")
    st.dataframe(df_f, use_container_width=True, hide_index=True)

else:
    st.error("🚨 Problema con 'datos_corresponsales.csv'.")
    st.info("Revisa que el archivo esté en la carpeta principal de tu GitHub.")
