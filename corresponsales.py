import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="BVB - Gestión Comercial", layout="wide")

# Diseño visual (Azul y Dorado BVB)
st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    [data-testid="stMetricValue"] { color: #0033a0 !important; font-weight: bold; }
    div[data-testid="stMetric"] { 
        background-color: #ffffff; 
        border-left: 5px solid #EBB932; 
        border-radius: 10px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 Panel de Gestión Comercial BVB")

# 2. MOTOR DE CARGA "TODO TERRENO"
@st.cache_data(ttl=60)
def cargar_datos_extremo():
    try:
        # Intentamos leer el archivo ignorando errores de codificación
        df = pd.read_csv("datos_corresponsales.csv", sep=None, engine='python', encoding_errors='ignore')
        
        # Limpieza profunda de nombres de columnas
        # Esto quita los saltos de línea que mete Excel dentro de las celdas
        df.columns = [str(c).replace('\n', ' ').replace('\r', ' ').strip() for c in df.columns]
        
        # Manejo de nombres DUPLICADOS (como "Ciudad" y "Ciudad")
        cols = pd.Series(df.columns)
        for i, col in enumerate(cols):
            if (cols == col).sum() > 1:
                count = list(cols[:i]).count(col)
                if count > 0:
                    cols[i] = f"{col}_{count}"
        df.columns = cols

        # Limpieza de datos (quitar $ y comas para poder SUMAR)
        for col in df.columns:
            if any(x in col.upper() for x in ["TX", "$$", "TRANSA", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC", "ENE"]):
                df[col] = df[col].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False).str.strip()
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Error en la estructura del archivo: {e}")
        return None

df = cargar_datos_extremo()

if df is not None:
    # Identificación de columnas clave según tu descripción
    # Buscamos columnas aunque tengan nombres ligeramente diferentes
    col_esp = next((c for c in df.columns if "ESPECIALISTA" in c.upper()), df.columns[0])
    col_mun = next((c for c in df.columns if "CIUDAD" in c.upper()), df.columns[1])
    col_estado = next((c for c in df.columns if "ESTADO" in c.upper()), None)
    col_rango = next((c for c in df.columns if "RANGOS" in c.upper()), None)
    col_tx_total = next((c for c in df.columns if "TX ULTIMO SEMESTRE" in c.upper()), None)
    col_si_no = next((c for c in df.columns if "TRANSA SI/NO MES" in c.upper()), None)

    # --- BARRA LATERAL CON DESPLEGABLES ---
    st.sidebar.header("🔍 Filtros de Consulta")
    
    lista_esp = ["TODOS"] + sorted(df[col_esp].unique().astype(str).tolist())
    esp_sel = st.sidebar.selectbox("Especialista:", lista_esp)
    
    lista_mun = ["TODOS"] + sorted(df[col_mun].unique().astype(str).tolist())
    mun_sel = st.sidebar.selectbox("Municipio:", lista_mun)

    df_f = df.copy()
    if esp_sel != "TODOS": df_f = df_f[df_f[col_esp] == esp_sel]
    if mun_sel != "TODOS": df_f = df_f[df_f[col_mun] == mun_sel]

    # --- KPI'S (Métricas) ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Puntos", f"{len(df_f)}")
    
    if col_tx_total:
        c2.metric("TX Semestre", f"{df_f[col_tx_total].sum():,.0f}")
    
    col_ene_tx = next((c for c in df.columns if "ENE 2026 TX" in c.upper()), None)
    if col_ene_tx:
        c3.metric("TX Enero 2026", f"{df_f[col_ene_tx].sum():,.0f}")
        
    if col_si_no:
        con_tx = len(df_f[df_f[col_si_no].astype(str).str.upper().str.contains("SI")])
        c4.metric("Activos (Si)", con_tx)

    # --- PESTAÑAS ---
    tab1, tab2, tab3 = st.tabs(["📊 Análisis por Estado", "🏆 Top 50 VIP", "📈 Comparativo TX vs $$"])

    with tab1:
        st.subheader("Distribución de la Red")
        col_a, col_b = st.columns(2)
        with col_a:
            if col_estado:
                fig_estado = px.pie(df_f, names=col_estado, title="Niveles (Master/Medio/Intermedio)", hole=0.4)
                st.plotly_chart(fig_estado, use_container_width=True)
        with col_b:
            if col_rango:
                fig_rango = px.bar(df_f[col_rango].value_counts().reset_index(), x='index', y=col_rango, title="Distribución por Rangos")
                st.plotly_chart(fig_rango, use_container_width=True)

    with tab2:
        st.subheader("Ranking Top 50")
        if col_tx_total:
            top_50 = df_f.nlargest(50, col_tx_total)
            st.dataframe(top_50[[col_esp, col_mun, 'Dirección', col_tx_total]], use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("Histórico Semestral (Cantidades vs Dinero)")
        meses = ["JUL", "AGO", "SEP", "OCT", "NOV", "DIC", "ENE"]
        data_ev = []
        for m in meses:
            c_tx = next((c for c in df.columns if m in c.upper() and "TX" in c.upper()), None)
            c_money = next((c for c in df.columns if m in c.upper() and "$$" in c.upper()), None)
            if c_tx: data_ev.append({"Mes": m, "Tipo": "Cantidades (TX)", "Valor": df_f[c_tx].sum()})
            if c_money: data_ev.append({"Mes": m, "Tipo": "Dinero ($$)", "Valor": df_f[c_money].sum()})
        
        if data_ev:
            df_ev = pd.DataFrame(data_ev)
            fig_ev = px.line(df_ev, x="Mes", y="Valor", color="Tipo", markers=True)
            st.plotly_chart(fig_ev, use_container_width=True)

    st.divider()
    st.subheader("📋 Base de Datos Completa")
    st.dataframe(df_f, use_container_width=True, hide_index=True)

else:
    st.error("🚨 Sigue habiendo un problema con el archivo 'datos_corresponsales.csv'.")
    st.info("Asegúrate de que el archivo en GitHub sea un CSV real y no un Excel (.xlsx) renombrado a .csv.")
