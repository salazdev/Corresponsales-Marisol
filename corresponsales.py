import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. CONFIGURACIÓN VISUAL Y DE PÁGINA
st.set_page_config(page_title="BVB - Gestión Comercial", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    
    /* Panel blanco de las métricas */
    div[data-testid="stMetric"] { 
        background-color: #ffffff !important; 
        border-left: 5px solid #EBB932 !important; 
        border-radius: 10px !important; 
        padding: 15px 20px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important; 
        height: 130px !important;
    }
    
    /* TÍTULOS EN NEGRO ABSOLUTO */
    div[data-testid="stMetricLabel"] p { 
        color: #000000 !important; 
        font-size: 1.1rem !important; 
        font-weight: 800 !important;
        opacity: 1 !important;
    }
    
    /* NÚMEROS EN AZUL */
    div[data-testid="stMetricValue"] div { 
        color: #0033a0 !important; 
        font-size: 2.3rem !important; 
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 Panel de Gestión Comercial BVB")

# 2. MOTOR DE CARGA CON DIAGNÓSTICO
@st.cache_data(ttl=10)
def cargar_datos_extremo():
    # Listar todos los archivos para saber qué ve el servidor
    todos_los_archivos = os.listdir('.')
    csv_disponibles = [f for f in todos_los_archivos if f.lower().endswith('.csv')]
    
    if not csv_disponibles:
        return None, todos_los_archivos

    # Intentar cargar el primero que encuentre
    archivo_a_cargar = csv_disponibles[0]
    
    for s in [';', ',', '\t']:
        try:
            df = pd.read_csv(archivo_a_cargar, sep=s, engine='python', on_bad_lines='skip', encoding_errors='ignore')
            if len(df.columns) > 1:
                # Limpiar nombres de columnas
                nuevos_nombres = []
                for i, col in enumerate(df.columns):
                    nombre = str(col).upper().strip().replace('\n', ' ')
                    if nombre in nuevos_nombres or nombre == "":
                        nuevos_nombres.append(f"{nombre}_{i}")
                    else:
                        nuevos_nombres.append(nombre)
                df.columns = nuevos_nombres
                
                # Limpiar números
                for c in df.columns:
                    if any(x in c for x in ["TX", "$$", "ENE", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]):
                        df[c] = df[c].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False).str.strip()
                        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
                return df, archivo_a_cargar
        except:
            continue
    return None, todos_los_archivos

df, info_archivo = cargar_datos_extremo()

if df is not None:
    # --- ASIGNACIÓN DE COLUMNAS ---
    def buscar_columna(keys, pos_backup):
        for k in keys:
            for c in df.columns:
                if k in c: return c
        return df.columns[pos_backup]

    c_esp = buscar_columna(["ESPEC"], 3)
    c_mun = buscar_columna(["CIUD", "MUN"], 1)
    c_tx_total = buscar_columna(["TX ULTIMO SEMESTRE", "TOTAL TX"], len(df.columns)-2)
    c_money = buscar_columna(["ENE 2026 $$", "ENE 2026 $"], len(df.columns)-3)
    c_estado = buscar_columna(["ESTADO"], 8)
    c_si_no = buscar_columna(["SI/NO"], 10)

    # --- FILTROS ---
    st.sidebar.header("🔍 Filtros")
    esp_sel = st.sidebar.selectbox("Especialista:", ["TODOS"] + sorted([str(x) for x in df[c_esp].unique() if str(x) not in ['nan', '0']]))
    mun_sel = st.sidebar.selectbox("Municipio:", ["TODOS"] + sorted([str(x) for x in df[c_mun].unique() if str(x) not in ['nan', '0']]))

    df_f = df.copy()
    if esp_sel != "TODOS": df_f = df_f[df_f[c_esp] == esp_sel]
    if mun_sel != "TODOS": df_f = df_f[df_f[c_mun] == mun_sel]

    # --- INDICADORES ---
    st.subheader("🚀 Indicadores Clave")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Puntos Red", f"{len(df_f)}")
    k2.metric("TX Semestre", f"{df_f[c_tx_total].sum():,.0f}")
    k3.metric("Monto Ene ($)", f"$ {df_f[c_money].sum():,.0f}")
    
    activos = 0
    if c_si_no in df_f.columns:
        activos = len(df_f[df_f[c_si_no].astype(str).str.upper().str.contains("SI")])
    k4.metric("Activos (Si)", activos)

    # --- PESTAÑAS ---
    tab1, tab2, tab3 = st.tabs(["📊 Análisis", "🏆 Top 50", "📋 Base de Datos"])

    with tab1:
        izq, der = st.columns(2)
        with izq:
            if c_estado in df_f.columns:
                df_pie = df_f[~df_f[c_estado].astype(str).isin(['0', 'nan', 'NAN', '0.0'])]
                if not df_pie.empty:
                    st.plotly_chart(px.pie(df_pie, names=c_estado, title="Distribución por Nivel", hole=0.4), use_container_width=True)
        with der:
            top_muns = df_f.groupby(c_mun)[c_tx_total].sum().nlargest(10).reset_index()
            st.plotly_chart(px.bar(top_muns, x=c_tx_total, y=c_mun, orientation='h', title="Top 10 Municipios"), use_container_width=True)

    with tab2:
        st.subheader("🏆 Mejores 50 Corresponsales")
        ranking = df_f.sort_values(by=c_tx_total, ascending=False).head(50)
        st.dataframe(ranking[[c_esp, c_mun, c_tx_total, c_money]], use_container_width=True, hide_index=True)

    with tab3:
        st.dataframe(df_f, use_container_width=True)
else:
    st.error("🚨 No se encontró ningún archivo CSV válido.")
    st.warning(f"Archivos detectados en el repositorio: {info_archivo}")
    st.info("Asegúrate de que tu archivo termine en .csv y no esté dentro de una carpeta.")
