import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN
st.set_page_config(page_title="BVB - Dashboard Estratégico", layout="wide")

# Estilo para que las métricas se vean claras
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { color: #0033a0 !important; font-weight: bold; font-size: 1.8rem; }
    div[data-testid="stMetric"] { background-color: #ffffff; border-left: 5px solid #EBB932; padding: 10px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 Panel de Gestión Comercial BVB")

# 2. CARGA Y LIMPIEZA PROFUNDA
@st.cache_data(ttl=600)
def cargar_y_limpiar():
    try:
        # Leer archivo probando separadores comunes
        try:
            df = pd.read_csv("datos_corresponsales.csv", sep=None, engine='python', on_bad_lines='skip')
        except:
            df = pd.read_csv("datos_corresponsales.csv", sep=';', encoding='latin-1', on_bad_lines='skip')

        # --- SOLUCIÓN AL ERROR DE DUPLICADOS (ValueError) ---
        new_cols = []
        counts = {}
        for col in df.columns:
            c_clean = str(col).strip()
            if c_clean in counts:
                counts[c_clean] += 1
                new_cols.append(f"{c_clean}_{counts[c_clean]}")
            else:
                counts[c_clean] = 0
                new_cols.append(c_clean)
        df.columns = new_cols

        # Limpiar datos numéricos (Quitar $, comas y espacios)
        for col in df.columns:
            if any(x in col.upper() for x in ["TX", "$$", "TRANSA", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC", "ENE"]):
                df[col] = df[col].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False).str.strip()
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Error cargando el archivo: {e}")
        return None

df = cargar_y_limpiar()

if df is not None:
    # Identificar columnas clave (por si cambian de nombre)
    col_mun = next((c for c in df.columns if "CIUDAD" in c.upper()), df.columns[1])
    col_esp = next((c for c in df.columns if "ESPECIALISTA" in c.upper()), df.columns[3])
    col_tx_total = next((c for c in df.columns if "TX ULTIMO SEMESTRE" in c.upper()), "Transa")
    
    # --- FILTROS ---
    st.sidebar.header("🔍 Filtros de Consulta")
    esp_sel = st.sidebar.selectbox("Especialista:", ["Todos"] + sorted(df[col_esp].unique().tolist()))
    mun_sel = st.sidebar.selectbox("Municipio:", ["Todos"] + sorted(df[col_mun].unique().tolist()))

    # Aplicar filtros
    df_f = df.copy()
    if esp_sel != "Todos": df_f = df_f[df_f[col_esp] == esp_sel]
    if mun_sel != "Todos": df_f = df_f[df_f[col_mun] == mun_sel]

    # --- MÉTRICAS ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Puntos Red", f"{len(df_f):,}")
    m2.metric("TX Semestre", f"{df_f[col_tx_total].sum():,.0f}")
    
    col_money = next((c for c in df.columns if "ENE 2026 $$" in c.upper()), df.columns[-1])
    m3.metric("Monto Ene ($$)", f"$ {df_f[col_money].sum():,.0f}")
    
    col_act = next((c for c in df.columns if "TRANSA SI/NO MES" in c.upper()), None)
    if col_act:
        activos = len(df_f[df_f[col_act].astype(str).str.contains("Si", case=False)])
        m4.metric("Activos", activos)

    # --- PESTAÑAS ---
    tab1, tab2, tab3 = st.tabs(["📉 Análisis de Tiempo", "🏆 Top 50 Clientes", "📋 Base de Datos"])

    with tab1:
        st.subheader("Análisis Semestral por Mes")
        # Buscar columnas de meses de forma flexible
        meses_dict = {
            "Jul": [c for c in df.columns if "JUL" in c.upper() and "TX" in c.upper()],
            "Ago": [c for c in df.columns if "AGO" in c.upper() and "TX" in c.upper()],
            "Sep": [c for c in df.columns if "SEP" in c.upper() and "TX" in c.upper()],
            "Oct": [c for c in df.columns if "OCT" in c.upper() and "TX" in c.upper()],
            "Nov": [c for c in df.columns if "NOV" in c.upper() and "TX" in c.upper()],
            "Dic": [c for c in df.columns if "DIC" in c.upper() and "TX" in c.upper()],
            "Ene": [c for c in df.columns if "ENE" in c.upper() and "TX" in c.upper()]
        }
        
        datos_grafico = []
        for mes, cols in meses_dict.items():
            if cols:
                valor = df_f[cols[0]].sum()
                datos_grafico.append({"Mes": mes, "Transacciones": valor})
        
        if datos_grafico:
            df_g = pd.DataFrame(datos_grafico)
            fig = px.line(df_g, x="Mes", y="Transacciones", markers=True, title="Evolución de Transacciones (Cantidad)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No se detectaron las columnas de meses (Jul-Ene). Revisa los nombres en el Excel.")

        # Gráfico por Municipio
        top_mun = df_f.groupby(col_mun)[col_tx_total].sum().nlargest(10).reset_index()
        fig_bar = px.bar(top_mun, x=col_tx_total, y=col_mun, orientation='h', title="Top 10 Municipios que más Transan")
        st.plotly_chart(fig_bar, use_container_width=True)

    with tab2:
        st.subheader("🏆 Ranking Top 50 Corresponsales")
        # Mostrar donde están ubicados los mejores
        top_50 = df.nlargest(50, col_tx_total)
        st.dataframe(top_50[[col_esp, col_mun, "Dirección", col_tx_total]], use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("📋 Detalle General")
        search = st.text_input("Buscar por palabra clave:")
        if search:
            df_f = df_f[df_f.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
        st.dataframe(df_f, use_container_width=True, hide_index=True)

else:
    st.info("📢 Cargando datos... Asegúrate de que 'datos_corresponsales.csv' esté en GitHub.")
