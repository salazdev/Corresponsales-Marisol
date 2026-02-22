import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN E IDENTIDAD
st.set_page_config(page_title="BVB - Gestión Comercial", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    [data-testid="stMetricValue"] { color: #0033a0 !important; font-weight: bold; font-size: 2rem; }
    div[data-testid="stMetric"] { 
        background-color: #ffffff; 
        border-left: 5px solid #EBB932; 
        border-radius: 10px; 
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        padding: 10px 20px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 Panel de Gestión Comercial BVB")

# 2. MOTOR DE CARGA MEJORADO
@st.cache_data(ttl=60)
def cargar_datos():
    encodings = ['utf-8', 'latin-1', 'cp1252']
    for enc in encodings:
        try:
            df = pd.read_csv("datos_corresponsales.csv", sep=None, engine='python', encoding=enc)
            if len(df.columns) > 2:
                # Limpiar nombres de columnas (quitar saltos de línea y espacios)
                df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
                
                # Manejar duplicados de "Ciudad"
                cols = pd.Series(df.columns)
                for i, col in enumerate(cols):
                    if (cols == col).sum() > 1:
                        count = list(cols[:i]).count(col)
                        if count > 0: cols[i] = f"{col}_{count}"
                df.columns = cols

                # Convertir columnas de TX y $$ a números
                for col in df.columns:
                    if any(x in col.upper() for x in ["TX", "$$", "TRANSA", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC", "ENE"]):
                        df[col] = df[col].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False).str.strip()
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                return df
        except:
            continue
    return None

df = cargar_datos()

if df is not None:
    # --- FILTROS LATERALES ---
    st.sidebar.header("🔍 Filtros de Búsqueda")
    
    col_esp = next((c for c in df.columns if "ESPECIALISTA" in c.upper()), df.columns[0])
    col_mun = next((c for c in df.columns if "CIUDAD" in c.upper()), df.columns[1])
    col_estado = next((c for c in df.columns if "ESTADO" in c.upper()), None)
    col_rango = next((c for c in df.columns if "RANGOS" in c.upper()), None)

    esp_sel = st.sidebar.selectbox("Filtrar por Especialista:", ["TODOS"] + sorted(df[col_esp].unique().astype(str).tolist()))
    mun_sel = st.sidebar.selectbox("Filtrar por Municipio:", ["TODOS"] + sorted(df[col_mun].unique().astype(str).tolist()))
    
    if col_estado:
        est_sel = st.sidebar.multiselect("Nivel/Estado:", sorted(df[col_estado].unique().astype(str).tolist()), default=None)
    
    # Aplicar Filtros
    df_f = df.copy()
    if esp_sel != "TODOS": df_f = df_f[df_f[col_esp] == esp_sel]
    if mun_sel != "TODOS": df_f = df_f[df_f[col_mun] == mun_sel]
    if col_estado and est_sel: df_f = df_f[df_f[col_estado].isin(est_sel)]

    # --- KPI'S PRINCIPALES ---
    st.subheader("🚀 Indicadores Clave (Semestre Actual)")
    k1, k2, k3, k4 = st.columns(4)
    
    k1.metric("Puntos Seleccionados", f"{len(df_f)}")
    
    col_tx_total = next((c for c in df.columns if "TX ULTIMO SEMESTRE" in c.upper()), "Tx Ultimo Semestre")
    k2.metric("Total TX Semestre", f"{df_f[col_tx_total].sum():,.0f}")
    
    col_money_ene = next((c for c in df.columns if "ENE 2026 $$" in c.upper()), None)
    if col_money_ene:
        k3.metric("Monto Ene 2026 ($$)", f"$ {df_f[col_money_ene].sum():,.0f}")
    
    col_si_no = next((c for c in df.columns if "TRANSA SI/NO MES" in c.upper()), None)
    if col_si_no:
        activos = len(df_f[df_f[col_si_no].astype(str).str.upper().str.contains("SI")])
        k4.metric("Puntos con Transacción", activos)

    # --- CUERPO DEL PANEL ---
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Análisis Comparativo", "🏆 Top 50 VIP", "📈 Tendencia TX vs $$", "📋 Detalle Completo"])

    with tab1:
        st.subheader("Distribución por Nivel y Municipio")
        c1, c2 = st.columns(2)
        with c1:
            if col_estado:
                fig_pie = px.pie(df_f, names=col_estado, title="Proporción por Estado (Master/Medio/Intermedio)", 
                                 hole=0.4, color_discrete_sequence=px.colors.qualitative.Prism)
                st.plotly_chart(fig_pie, use_container_width=True)
        with c2:
            top_mun = df_f.groupby(col_mun)[col_tx_total].sum().nlargest(10).reset_index()
            fig_bar = px.bar(top_mun, x=col_tx_total, y=col_mun, orientation='h', title="Top 10 Municipios por TX",
                             color_discrete_sequence=['#0033a0'])
            st.plotly_chart(fig_bar, use_container_width=True)

    with tab2:
        st.subheader("🏆 Top 50 Corresponsales con Mayor Volumen")
        top_50 = df_f.nlargest(50, col_tx_total)
        # Columnas dinámicas para la tabla
        cols_mostrar = [col_esp, col_mun, 'Dirección', col_estado, col_tx_total]
        if col_money_ene: cols_mostrar.append(col_money_ene)
        st.dataframe(top_50[[c for c in cols_mostrar if c in df_f.columns]], use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("Comparativo Mensual: Cantidades (TX) vs Valores ($$)")
        meses = ["JUL", "AGO", "SEP", "OCT", "NOV", "DIC", "ENE"]
        data_meses = []
        for m in meses:
            c_tx = next((c for c in df.columns if m in c.upper() and "TX" in c.upper()), None)
            c_money = next((c for c in df.columns if m in c.upper() and "$$" in c.upper()), None)
            if c_tx:
                data_meses.append({
                    "Mes": m, 
                    "Tipo": "Cantidades (TX)", 
                    "Valor": df_f[c_tx].sum()
                })
            if c_money:
                # Nota: Dividimos por un factor para que el gráfico sea legible si el dinero es muy alto
                data_meses.append({
                    "Mes": m, 
                    "Tipo": "Valores ($$)", 
                    "Valor": df_f[c_money].sum()
                })
        
        if data_meses:
            df_meses = pd.DataFrame(data_meses)
            fig_compare = px.line(df_meses, x="Mes", y="Valor", color="Tipo", markers=True, 
                                  title="Evolución Semestral TX vs $$")
            st.plotly_chart(fig_compare, use_container_width=True)

    with tab4:
        st.subheader("📋 Base de Datos Filtrada")
        st.dataframe(df_f, use_container_width=True, hide_index=True)

else:
    st.error("🚨 Error: No se puede leer el archivo. Verifica el nombre 'datos_corresponsales.csv' en GitHub.")
