import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN E IDENTIDAD
st.set_page_config(page_title="BVB - Gestión Comercial", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stMetricValue"] { color: #0033a0 !important; font-weight: bold; }
    div[data-testid="stMetric"] { background-color: #ffffff; border-left: 5px solid #EBB932; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 Panel de Gestión Comercial BVB")

# 2. MOTOR DE CARGA ROBUSTO
@st.cache_data(ttl=60)
def cargar_datos_extremo():
    encoding_list = ['utf-8', 'latin-1', 'cp1252', 'utf-16']
    separator_list = [',', ';', '\t']
    
    for enc in encoding_list:
        for sep in separator_list:
            try:
                df = pd.read_csv("datos_corresponsales.csv", sep=sep, encoding=enc, engine='python', on_bad_lines='skip')
                if len(df.columns) > 3:
                    df.columns = [str(c).strip() for c in df.columns]
                    cols = pd.Series(df.columns)
                    for i, col in enumerate(cols):
                        if (cols == col).sum() > 1:
                            count = list(cols[:i]).count(col)
                            if count > 0: cols[i] = f"{col}_{count}"
                    df.columns = cols
                    
                    for col in df.columns:
                        if any(x in col.upper() for x in ["TX", "$$", "TRANSA", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC", "ENE"]):
                            df[col] = df[col].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False).str.strip()
                            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                    return df
            except:
                continue
    return None

df = cargar_datos_extremo()

if df is not None:
    # --- BUSCAR COLUMNAS ---
    col_mun = next((c for c in df.columns if "CIUDAD" in c.upper() or "MUNIC" in c.upper()), df.columns[1])
    col_esp = next((c for c in df.columns if "ESPECIALISTA" in c.upper()), df.columns[3])
    col_tx_total = next((c for c in df.columns if "TX ULTIMO SEMESTRE" in c.upper() or "TRANSA" in c.upper()), df.columns[-1])
    col_money = next((c for c in df.columns if "ENE 2026 $$" in c.upper() or "ENE 2026 $" in c.upper()), None)

    # --- FILTROS ---
    st.sidebar.header("🔍 Filtros de Búsqueda")
    
    esp_opt = ["TODOS LOS ESPECIALISTAS"] + sorted(df[col_esp].unique().astype(str).tolist())
    esp_sel = st.sidebar.selectbox("Filtrar por Especialista:", esp_opt)
    
    mun_opt = ["TODOS LOS MUNICIPIOS"] + sorted(df[col_mun].unique().astype(str).tolist())
    mun_sel = st.sidebar.selectbox("Filtrar por Municipio:", mun_opt)

    df_f = df.copy()
    if esp_sel != "TODOS LOS ESPECIALISTAS":
        df_f = df_f[df_f[col_esp] == esp_sel]
    if mun_sel != "TODOS LOS MUNICIPIOS":
        df_f = df_f[df_f[col_mun] == mun_sel]

    # --- MÉTRICAS ---
    m1, m2, m3 = st.columns(3)
    m1.metric("Corresponsales", f"{len(df_f):,}")
    m2.metric("Total TX (Semestre)", f"{df_f[col_tx_total].sum():,.0f}")
    if col_money:
        m3.metric("Monto Ene 2026 ($$)", f"$ {df_f[col_money].sum():,.0f}")

    # --- PESTAÑAS ---
    t1, t2, t3 = st.tabs(["📍 Municipios y Departamentos", "🏆 Top 50 VIP", "📅 Análisis Mensual"])

    with t1:
        st.subheader("Análisis por Ubicación")
        resumen_mun = df_f.groupby(col_mun)[col_tx_total].sum().nlargest(15).reset_index()
        fig_mun = px.bar(resumen_mun, x=col_tx_total, y=col_mun, orientation='h', 
                         title="Top 15 Municipios con más Transacciones", color_discrete_sequence=['#0033a0'])
        st.plotly_chart(fig_mun, use_container_width=True)

    with t2:
        st.subheader("🏆 Ranking Top 50 Clientes")
        top_50 = df.nlargest(50, col_tx_total)
        cols_ranking = [col_esp, col_mun, 'Dirección', col_tx_total]
        cols_ranking = [c for c in cols_ranking if c in top_50.columns]
        st.dataframe(top_50[cols_ranking], use_container_width=True, hide_index=True)

    with t3:
        st.subheader("Análisis del Último Semestre")
        meses_lista = ["JUL", "AGO", "SEP", "OCT", "NOV", "DIC", "ENE"]
        evolucion = []
        for m in meses_lista:
            c_mes = next((c for c in df.columns if m in c.upper() and "TX" in c.upper()), None)
            if c_mes:
                evolucion.append({"Mes": m, "Cantidad": df_f[c_mes].sum()})
        
        if evolucion:
            df_ev = pd.DataFrame(evolucion)
            # CORRECCIÓN DE SINTAXIS AQUÍ:
            fig_evol = px.line(df_ev, x="Mes", y="Cantidad", markers=True, title="Tendencia Mensual")
            st.plotly_chart(fig_evol, use_container_width=True)

    st.divider()
    st.subheader("📋 Base de Datos Completa")
    busqueda = st.text_input("🔍 Buscar por palabra clave:")
    if busqueda:
        df_f = df_f[df_f.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]
    st.dataframe(df_f, use_container_width=True, hide_index=True)

else:
    st.error("🚨 No se pudo leer el archivo. Revisa que se llame 'datos_corresponsales.csv'.")
