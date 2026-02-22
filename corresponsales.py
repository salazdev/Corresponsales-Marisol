import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN E IDENTIDAD
st.set_page_config(page_title="BVB - Gestión Comercial", layout="wide")

# Estilo para etiquetas y paneles
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .kpi-label { color: #555; font-size: 0.9rem; font-weight: bold; margin-bottom: 5px; }
    [data-testid="stMetricValue"] { color: #0033a0 !important; font-weight: bold; font-size: 2rem; }
    div[data-testid="stMetric"] { 
        background-color: #ffffff; border-left: 5px solid #EBB932; 
        border-radius: 10px; padding: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 Panel de Gestión Comercial BVB")

# 2. CARGA DE DATOS CON LIMPIEZA EXTREMA
@st.cache_data(ttl=60)
def cargar_datos_limpios():
    for sep in [';', ',', '\t']:
        try:
            df = pd.read_csv("datos_corresponsales.csv", sep=sep, engine='python', on_bad_lines='skip', encoding_errors='ignore')
            if len(df.columns) > 5:
                # LIMPIEZA CLAVE: Quitar espacios locos y saltos de línea de los nombres de columnas
                df.columns = [str(c).replace('\n', ' ').strip().upper() for c in df.columns]
                
                # Manejo de nombres duplicados
                cols = pd.Series(df.columns)
                for i, col in enumerate(cols):
                    if (cols == col).sum() > 1:
                        count = list(cols[:i]).count(col)
                        if count > 0: cols[i] = f"{col}_{count}"
                df.columns = cols

                # Limpiar valores monetarios y cantidades
                for col in df.columns:
                    if any(x in col for x in ["TX", "$$", "TRANSA", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC", "ENE"]):
                        df[col] = df[col].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False).str.strip()
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                return df
        except:
            continue
    return None

df = cargar_datos_limpios()

if df is not None:
    # Identificar columnas por contenido (Flexible)
    col_esp = next((c for c in df.columns if "ESPECIALISTA" in c), df.columns[0])
    col_mun = next((c for c in df.columns if "CIUDAD" in c), df.columns[1])
    col_estado = next((c for c in df.columns if "ESTADO" in c), None)
    col_tx_total = next((c for c in df.columns if "TX ULTIMO SEMESTRE" in c or "TRANSA" in c), None)
    col_money_ene = next((c for c in df.columns if "ENE 2026 $$" in c or "ENE 2026 $" in c), None)
    col_si_no = next((c for c in df.columns if "TRANSA SI/NO MES" in c), None)

    # --- FILTROS ---
    st.sidebar.header("🔍 Consultar Información")
    esp_sel = st.sidebar.selectbox("Especialista:", ["TODOS"] + sorted(df[col_esp].unique().astype(str).tolist()))
    mun_sel = st.sidebar.selectbox("Municipio:", ["TODOS"] + sorted(df[col_mun].unique().astype(str).tolist()))

    df_f = df.copy()
    if esp_sel != "TODOS": df_f = df_f[df_f[col_esp] == esp_sel]
    if mun_sel != "TODOS": df_f = df_f[df_f[col_mun] == mun_sel]

    # --- MÉTRICAS (KPIs) CON NOMBRES CLAROS ---
    st.subheader("🚀 Indicadores de Gestión")
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.markdown('<p class="kpi-label">Corresponsales en la Zona</p>', unsafe_allow_html=True)
        st.metric("Total Puntos", f"{len(df_f)}")
    
    with c2:
        st.markdown('<p class="kpi-label">Volumen Transaccional (Cant)</p>', unsafe_allow_html=True)
        val_tx = df_f[col_tx_total].sum() if col_tx_total else 0
        st.metric("TX Semestre", f"{val_tx:,.0f}")
    
    with c3:
        st.markdown('<p class="kpi-label">Dinero Movilizado Ene 2026</p>', unsafe_allow_html=True)
        val_money = df_f[col_money_ene].sum() if col_money_ene else 0
        st.metric("Monto Total", f"$ {val_money:,.0f}")
        
    with c4:
        st.markdown('<p class="kpi-label">Puntos que Transaron</p>', unsafe_allow_html=True)
        if col_si_no:
            con_tx = len(df_f[df_f[col_si_no].astype(str).str.upper().str.contains("SI")])
            st.metric("Activos (Si)", con_tx)
        else:
            st.metric("Sin Datos", "0")

    # --- TABS DE ANÁLISIS ---
    t1, t2, t3 = st.tabs(["📊 Análisis por Estado", "🏆 Top 50 Clientes", "📈 Evolución Mensual"])

    with t1:
        st.subheader("Análisis de Segmentación")
        col_a, col_b = st.columns(2)
        with col_a:
            # Si el gráfico no se mueve es porque el filtro deja pocos datos o la columna está vacía
            if col_estado and not df_f[col_estado].empty:
                # Filtramos valores 0 o vacíos para que el gráfico sea real
                data_pie = df_f[df_f[col_estado] != "0"]
                fig_pie = px.pie(data_pie, names=col_estado, title="Nivel: Master / Medio / Intermedio", 
                                 hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.warning("No hay datos de 'Estado' para esta selección.")
        with col_b:
            if col_tx_total:
                top_mun = df_f.groupby(col_mun)[col_tx_total].sum().nlargest(10).reset_index()
                fig_bar = px.bar(top_mun, x=col_tx_total, y=col_mun, orientation='h', 
                                 title="Top Municipios Seleccionados", color_discrete_sequence=['#0033a0'])
                st.plotly_chart(fig_bar, use_container_width=True)

    with t2:
        st.subheader("🏆 Top 50 Corresponsales")
        if col_tx_total:
            top_50 = df_f.nlargest(50, col_tx_total)
            st.dataframe(top_50[[col_esp, col_mun, 'DIRECCIÓN', col_tx_total]], use_container_width=True, hide_index=True)

    with t3:
        st.subheader("Comparativo Histórico")
        meses = ["JUL", "AGO", "SEP", "OCT", "NOV", "DIC", "ENE"]
        data_ev = []
        for m in meses:
            # Buscar columnas que digan el MES y TX
            c_tx = next((c for c in df.columns if m in c and "TX" in c), None)
            if c_tx:
                data_ev.append({"Mes": m, "Valor": df_f[c_tx].sum()})
        
        if data_ev:
            fig_ev = px.line(pd.DataFrame(data_ev), x="Mes", y="Valor", markers=True, 
                             title="Tendencia de Transacciones (Cantidad)", color_discrete_sequence=['#EBB932'])
            st.plotly_chart(fig_ev, use_container_width=True)

    st.divider()
    st.subheader("📋 Detalle de la Operación")
    st.dataframe(df_f, use_container_width=True, hide_index=True)

else:
    st.error("🚨 Error al procesar el archivo. Revisa que sea un CSV válido.")
