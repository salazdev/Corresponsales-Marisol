import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="BVB - Gestión Comercial", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .kpi-label { color: #555; font-size: 0.85rem; font-weight: bold; margin-bottom: -10px; }
    [data-testid="stMetricValue"] { color: #0033a0 !important; font-weight: bold; font-size: 1.8rem; }
    div[data-testid="stMetric"] { 
        background-color: #ffffff; border-left: 5px solid #EBB932; 
        border-radius: 10px; padding: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 Panel de Gestión Comercial BVB")

# 2. MOTOR DE CARGA ULTRA-FLEXIBLE
@st.cache_data(ttl=60)
def cargar_datos_seguro():
    # Probamos múltiples combinaciones de separadores y codificaciones
    for enc in ['utf-8', 'latin-1', 'cp1252', 'utf-8-sig']:
        for sep in [';', ',', '\t']:
            try:
                df = pd.read_csv("datos_corresponsales.csv", sep=sep, encoding=enc, engine='python', on_bad_lines='skip')
                if len(df.columns) > 5:
                    # Limpiamos nombres de columnas: mayúsculas, sin espacios, sin saltos de línea
                    df.columns = [str(c).replace('\n', ' ').strip().upper() for c in df.columns]
                    
                    # Manejo de columnas duplicadas (Ciudad, Ciudad_1)
                    cols = pd.Series(df.columns)
                    for i, col in enumerate(cols):
                        if (cols == col).sum() > 1:
                            count = list(cols[:i]).count(col)
                            if count > 0: cols[i] = f"{col}_{count}"
                    df.columns = cols

                    # Limpiamos los números de símbolos como $ y ,
                    for col in df.columns:
                        if any(x in col for x in ["TX", "$$", "TRANSA", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC", "ENE"]):
                            df[col] = df[col].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False).str.strip()
                            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                    return df
            except:
                continue
    return None

df = cargar_datos_seguro()

if df is not None:
    # Búsqueda inteligente de columnas clave
    col_esp = next((c for c in df.columns if "ESPECIALISTA" in c), df.columns[0])
    col_mun = next((c for c in df.columns if "CIUDAD" in c), df.columns[1])
    col_estado = next((c for c in df.columns if "ESTADO" in c), None)
    col_tx_total = next((c for c in df.columns if "TX ULTIMO SEMESTRE" in c or "TRANSA" in c), None)
    col_money_ene = next((c for c in df.columns if "ENE 2026 $$" in c or "ENE 2026 $" in c), None)
    col_si_no = next((c for c in df.columns if "TRANSA SI/NO MES" in c), None)

    # --- FILTROS LATERALES ---
    st.sidebar.header("🔍 Consultar Información")
    esp_sel = st.sidebar.selectbox("Especialista:", ["TODOS"] + sorted(df[col_esp].unique().astype(str).tolist()))
    mun_sel = st.sidebar.selectbox("Municipio:", ["TODOS"] + sorted(df[col_mun].unique().astype(str).tolist()))

    df_f = df.copy()
    if esp_sel != "TODOS": df_f = df_f[df_f[col_esp] == esp_sel]
    if mun_sel != "TODOS": df_f = df_f[df_f[col_mun] == mun_sel]

    # --- MÉTRICAS (KPIs) ---
    st.subheader("🚀 Indicadores de Gestión")
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.markdown('<p class="kpi-label">Corresponsales Seleccionados</p>', unsafe_allow_html=True)
        st.metric("Puntos", f"{len(df_f)}")
    
    with c2:
        st.markdown('<p class="kpi-label">Volumen Semestral (Cantidades)</p>', unsafe_allow_html=True)
        val_tx = df_f[col_tx_total].sum() if col_tx_total else 0
        st.metric("TX Total", f"{val_tx:,.0f}")
    
    with c3:
        st.markdown('<p class="kpi-label">Dinero Movilizado Ene 2026</p>', unsafe_allow_html=True)
        val_money = df_f[col_money_ene].sum() if col_money_ene else 0
        st.metric("Monto Total", f"$ {val_money:,.0f}")
        
    with c4:
        st.markdown('<p class="kpi-label">Puntos con Transacción (Activos)</p>', unsafe_allow_html=True)
        if col_si_no:
            con_tx = len(df_f[df_f[col_si_no].astype(str).str.upper().str.contains("SI")])
            st.metric("Activos (Si)", con_tx)
        else:
            st.metric("Sin Datos", "0")

    # --- TABS DE ANÁLISIS ---
    tab1, tab2, tab3 = st.tabs(["📊 Niveles y Municipios", "🏆 Top 50 Clientes", "📈 Evolución Mensual"])

    with tab1:
        st.subheader("Análisis de Segmentación y Ubicación")
        col_a, col_b = st.columns(2)
        with col_a:
            if col_estado:
                # Filtrar valores vacíos o '0' para que el gráfico sea útil
                df_pie = df_f[~df_f[col_estado].isin(['0', 0, 'nan', 'NAN'])]
                if not df_pie.empty:
                    fig_pie = px.pie(df_pie, names=col_estado, title="Nivel (Master/Medio/Intermedio)", 
                                     hole=0.4, color_discrete_sequence=px.colors.qualitative.Bold)
                    st.plotly_chart(fig_pie, use_container_width=True)
                else: st.info("No hay datos de 'Estado' para esta selección.")
        with col_b:
            if col_tx_total:
                top_mun = df_f.groupby(col_mun)[col_tx_total].sum().nlargest(10).reset_index()
                fig_bar = px.bar(top_mun, x=col_tx_total, y=col_mun, orientation='h', 
                                 title="Top Municipios por Transacciones", color_discrete_sequence=['#0033a0'])
                st.plotly_chart(fig_bar, use_container_width=True)

    with tab2:
        st.subheader("🏆 Top 50 Corresponsales con Mayor Volumen")
        if col_tx_total:
            top_50 = df_f.nlargest(50, col_tx_total)
            st.dataframe(top_50[[col_esp, col_mun, 'DIRECCIÓN', col_tx_total]], use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("Evolución de Transacciones (Cantidad)")
        meses = ["JUL", "AGO", "SEP", "OCT", "NOV", "DIC", "ENE"]
        data_ev = []
        for m in meses:
            c_tx = next((c for c in df.columns if m in c and "TX" in c), None)
            if c_tx:
                data_ev.append({"Mes": m, "Transacciones": df_f[c_tx].sum()})
        
        if data_ev:
            fig_ev = px.line(pd.DataFrame(data_ev), x="Mes", y="Transacciones", markers=True, 
                             title="Tendencia Semestral", color_discrete_sequence=['#EBB932'])
            st.plotly_chart(fig_ev, use_container_width=True)
        else:
            st.warning("No se encontraron columnas de meses para el gráfico.")

    st.divider()
    st.subheader("📋 Detalle de la Operación")
    st.dataframe(df_f, use_container_width=True, hide_index=True)

else:
    st.error("🚨 El archivo 'datos_corresponsales.csv' no tiene el formato correcto o no se encuentra.")
    st.info("Asegúrate de que el archivo en GitHub sea un CSV (delimitado por comas o punto y coma).")
