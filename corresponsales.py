import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="BVB - Gestión Comercial", layout="wide")

# Estilo para subir los números en los paneles blancos
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div[data-testid="stMetric"] { 
        background-color: #ffffff; border-left: 5px solid #EBB932; 
        border-radius: 10px; padding: 5px 15px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); height: 100px;
        display: flex; flex-direction: column; justify-content: center;
    }
    div[data-testid="stMetricLabel"] { margin-top: -10px !important; margin-bottom: -15px !important; font-size: 0.85rem !important; font-weight: bold !important; color: #666 !important; }
    div[data-testid="stMetricValue"] { color: #0033a0 !important; font-size: 2.1rem !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 Panel de Gestión Comercial BVB")

# 2. MOTOR DE CARGA CON RENOMBRADO FORZOSO
@st.cache_data(ttl=60)
def cargar_datos_seguros():
    for s in [';', ',', '\t']:
        try:
            df = pd.read_csv("datos_corresponsales.csv", sep=s, engine='python', on_bad_lines='skip', encoding_errors='ignore')
            if len(df.columns) > 2:
                # Limpiar y Renombrar para evitar duplicados
                nuevos_nombres = []
                for i, col in enumerate(df.columns):
                    nombre_limpio = str(col).upper().strip().replace('\n', ' ')
                    if nombre_limpio in nuevos_nombres or nombre_limpio == "":
                        nuevos_nombres.append(f"{nombre_limpio}_{i}")
                    else:
                        nuevos_nombres.append(nombre_limpio)
                df.columns = nuevos_nombres
                
                # Convertir números
                for c in df.columns:
                    if any(x in c for x in ["TX", "$$", "ENE", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]):
                        df[c] = df[c].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False).str.strip()
                        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
                return df
        except:
            continue
    return None

df = cargar_datos_seguros()

if df is not None:
    # --- ASIGNACIÓN DE COLUMNAS POR PRIORIDAD (Nombre o Posición) ---
    def buscar_col(keywords, default_pos):
        for k in keywords:
            for c in df.columns:
                if k in c: return c
        return df.columns[default_pos] if len(df.columns) > default_pos else df.columns[0]

    c_esp = buscar_col(["ESPEC"], 3)
    c_mun = buscar_col(["CIUD", "MUN"], 1)
    c_tx_sem = buscar_col(["TX ULTIMO SEMESTRE", "TOTAL TX", "TX"], len(df.columns)-1)
    c_money = buscar_col(["ENE 2026 $$", "ENE 2026 $", "$$"], len(df.columns)-2)
    c_estado = buscar_col(["ESTADO"], 8) # Suponiendo que está por la col 8
    c_si_no = buscar_col(["SI/NO"], 10)

    # --- FILTROS ---
    st.sidebar.header("🔍 Consultar Información")
    
    lista_esp = ["TODOS"] + sorted([str(x) for x in df[c_esp].unique() if str(x) not in ['nan', '0', 'None']])
    esp_sel = st.sidebar.selectbox("Especialista:", lista_esp)
    
    lista_mun = ["TODOS"] + sorted([str(x) for x in df[c_mun].unique() if str(x) not in ['nan', '0', 'None']])
    mun_sel = st.sidebar.selectbox("Municipio:", lista_mun)

    df_f = df.copy()
    if esp_sel != "TODOS": df_f = df_f[df_f[c_esp] == esp_sel]
    if mun_sel != "TODOS": df_f = df_f[df_f[c_mun] == mun_sel]

    # --- MÉTRICAS ---
    st.subheader("🚀 Indicadores de Gestión")
    k1, k2, k3, k4 = st.columns(4)
    
    k1.metric("Puntos Red", f"{len(df_f)}")
    k2.metric("TX Semestre", f"{df_f[c_tx_sem].sum():,.0f}")
    k3.metric("Monto Ene ($)", f"$ {df_f[c_money].sum():,.0f}")
    
    activos = len(df_f[df_f[c_si_no].astype(str).str.upper().str.contains("SI")]) if c_si_no in df_f.columns else 0
    k4.metric("Activos (Si)", activos)

    # --- TABS ---
    tab1, tab2, tab3 = st.tabs(["📊 Segmentación", "🏆 Top 50", "📋 Base de Datos"])

    with tab1:
        col_izq, col_der = st.columns(2)
        with col_izq:
            df_pie = df_f[~df_f[c_estado].astype(str).isin(['0', 'nan', '0.0'])] if c_estado in df_f.columns else pd.DataFrame()
            if not df_pie.empty:
                st.plotly_chart(px.pie(df_pie, names=c_estado, title="Nivel Master/Medio", hole=0.4), use_container_width=True)
            else:
                st.info("Sin datos de nivel para mostrar.")
        with col_der:
            top_muns = df_f.groupby(c_mun)[c_tx_sem].sum().nlargest(10).reset_index()
            st.plotly_chart(px.bar(top_muns, x=c_tx_sem, y=c_mun, orientation='h', title="Top 10 Municipios"), use_container_width=True)

    with tab2:
        st.subheader("🏆 Ranking por Transacciones")
        top_50 = df_f.nlargest(50, c_tx_sem)
        st.dataframe(top_50[[c_esp, c_mun, c_tx_sem]], use_container_width=True, hide_index=True)

    with tab3:
        st.dataframe(df_f, use_container_width=True)

else:
    st.error("🚨 El sistema no detecta el archivo 'datos_corresponsales.csv'.")
    st.info("Por favor, verifica que el archivo esté subido en la raíz de tu repositorio de GitHub.")
