import streamlit as st
import pandas as pd
import plotly.express as px

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

# 2. CARGADOR DE FUERZA BRUTA (Prueba ; , y \t)
@st.cache_data(ttl=60)
def cargar_datos_fuerza_bruta():
    for separador in [';', ',', '\t']:
        try:
            df = pd.read_csv(
                "datos_corresponsales.csv", 
                sep=separador, 
                engine='python', 
                on_bad_lines='skip', 
                encoding_errors='ignore'
            )
            # Si logró leer más de 5 columnas, asumimos que este es el separador correcto
            if len(df.columns) > 5:
                # Limpieza de nombres de columnas
                df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
                
                # Manejo de duplicados (Ciudad, Ciudad_1)
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
        except:
            continue
    return None

df = cargar_datos_fuerza_bruta()

if df is not None:
    # Identificación de columnas (Búsqueda por palabras clave)
    col_esp = next((c for c in df.columns if "ESPECIALISTA" in c.upper()), df.columns[0])
    col_mun = next((c for c in df.columns if "CIUDAD" in c.upper()), df.columns[1])
    col_estado = next((c for c in df.columns if "ESTADO" in c.upper()), None)
    col_tx_total = next((c for c in df.columns if "TX ULTIMO SEMESTRE" in c.upper()), None)
    col_si_no = next((c for c in df.columns if "TRANSA SI/NO MES" in c.upper()), None)
    col_money_ene = next((c for c in df.columns if "ENE 2026 $$" in c.upper()), None)

    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("🔍 Consultar Información")
    esp_sel = st.sidebar.selectbox("Especialista:", ["TODOS"] + sorted(df[col_esp].unique().astype(str).tolist()))
    mun_sel = st.sidebar.selectbox("Municipio:", ["TODOS"] + sorted(df[col_mun].unique().astype(str).tolist()))

    df_f = df.copy()
    if esp_sel != "TODOS": df_f = df_f[df_f[col_esp] == esp_sel]
    if mun_sel != "TODOS": df_f = df_f[df_f[col_mun] == mun_sel]

    # --- MÉTRICAS (KPIs) ---
    st.subheader("🚀 Indicadores de Gestión")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Corresponsales", f"{len(df_f)}")
    
    if col_tx_total:
        c2.metric("TX Total Semestre", f"{df_f[col_tx_total].sum():,.0f}")
    
    if col_money_ene:
        c3.metric("Monto Ene 2026 ($$)", f"$ {df_f[col_money_ene].sum():,.0f}")
        
    if col_si_no:
        con_tx = len(df_f[df_f[col_si_no].astype(str).str.upper().str.contains("SI")])
        c4.metric("Puntos Activos (Si)", con_tx)

    # --- TABS DE ANÁLISIS ---
    t1, t2, t3 = st.tabs(["📊 Análisis por Estado", "🏆 Top 50 Clientes", "📈 Evolución TX vs $$"])

    with t1:
        st.subheader("Análisis por Departamento y Nivel")
        col_a, col_b = st.columns(2)
        with col_a:
            if col_estado:
                fig_pie = px.pie(df_f, names=col_estado, title="Proporción: Master / Medio / Intermedio", hole=0.4)
                st.plotly_chart(fig_pie, use_container_width=True)
        with col_b:
            # Gráfico por municipio
            top_mun = df_f.groupby(col_mun)[col_tx_total].sum().nlargest(10).reset_index() if col_tx_total else pd.DataFrame()
            if not top_mun.empty:
                fig_bar = px.bar(top_mun, x=col_tx_total, y=col_mun, orientation='h', title="Top 10 Municipios")
                st.plotly_chart(fig_bar, use_container_width=True)

    with t2:
        st.subheader("🏆 Top 50 Corresponsales con Mayor Actividad")
        if col_tx_total:
            top_50 = df_f.nlargest(50, col_tx_total)
            st.dataframe(top_50[[col_esp, col_mun, 'Dirección', col_tx_total]], use_container_width=True, hide_index=True)

    with t3:
        st.subheader("Comparativo Mensual: Cantidades vs Valores")
        meses = ["JUL", "AGO", "SEP", "OCT", "NOV", "DIC", "ENE"]
        data_ev = []
        for m in meses:
            c_tx = next((c for c in df.columns if m in c.upper() and "TX" in c.upper()), None)
            c_money = next((c for c in df.columns if m in c.upper() and "$$" in c.upper()), None)
            if c_tx: data_ev.append({"Mes": m, "Tipo": "TX (Cantidades)", "Valor": df_f[c_tx].sum()})
            if c_money: data_ev.append({"Mes": m, "Tipo": "$$ (Valores)", "Valor": df_f[c_money].sum()})
        
        if data_ev:
            st.plotly_chart(px.line(pd.DataFrame(data_ev), x="Mes", y="Valor", color="Tipo", markers=True), use_container_width=True)

    st.divider()
    st.subheader("📋 Base de Datos Completa")
    st.dataframe(df_f, use_container_width=True, hide_index=True)

else:
    st.error("🚨 No se pudo detectar el formato del archivo.")
    st.info("Recomendación: Abre tu Excel, dale 'Guardar como' -> 'CSV (delimitado por comas)' y súbelo de nuevo a GitHub.")
