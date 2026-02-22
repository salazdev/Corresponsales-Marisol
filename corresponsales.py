import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN E IDENTIDAD
st.set_page_config(page_title="BVB - Dashboard Estratégico", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    [data-testid="stMetricValue"] { color: #0033a0 !important; font-weight: bold; }
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border-left: 5px solid #EBB932;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 Gestión Integral de Corresponsalía BVB")

# 2. CARGA Y LIMPIEZA DE DATOS (Basado en tus columnas reales)
@st.cache_data(ttl=600)
def cargar_datos():
    try:
        df = pd.read_csv("datos_corresponsales.csv", sep=None, engine='python')
        
        # Limpiar nombres de columnas duplicadas o con espacios
        df.columns = [str(c).strip() for c in df.columns]
        
        # Forzar a números las columnas de transacciones y dinero
        cols_numericas = [
            'Tx Ultimo Semestre', 'Jul 2025 TX', 'Ago 2025 TX', 'Sep 2025 TX', 
            'Oct 2025 TX', 'Nov 2025 TX', 'Dic 2025 TX', 'Ene 2026 TX',
            'Ene 2026 $$', 'Ago 2025 $$', 'Sep 2025 $$', 'Oct 2025 $$', 
            'Nov 2025 $$', 'Dic 2025 $$'
        ]
        
        for col in cols_numericas:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
        return None

df = cargar_datos()

if df is not None:
    # --- BARRA LATERAL (FILTROS SOLICITADOS) ---
    st.sidebar.header("🔍 Panel de Búsqueda")
    
    # Filtro por Especialista
    lista_esp = ["Todos"] + sorted(df['ESPECIALISTA'].unique().tolist())
    esp_sel = st.sidebar.selectbox("Seleccione Especialista:", lista_esp)
    
    # Filtro por Municipio (Columna Ciudad)
    lista_ciu = ["Todas"] + sorted(df['Ciudad'].unique().tolist())
    ciu_sel = st.sidebar.selectbox("Seleccione Municipio:", lista_ciu)
    
    # Aplicar Filtros
    df_f = df.copy()
    if esp_sel != "Todos":
        df_f = df_f[df_f['ESPECIALISTA'] == esp_sel]
    if ciu_sel != "Todas":
        df_f = df_f[df_f['Ciudad'] == ciu_sel]

    # --- CUADRO DE MÉTRICAS PRINCIPALES ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Corresponsales", f"{len(df_f):,}")
    m2.metric("TX Totales Semestre", f"{df_f['Tx Ultimo Semestre'].sum():,.0f}")
    m3.metric("Puntos Activos", f"{len(df_f[df_f['Transa si/no MES'] == 'Si']):,}")
    m4.metric("Ene 2026 (Dinero)", f"$ {df_f['Ene 2026 $$'].sum():,.0f}")

    # --- PESTAÑAS DE ANÁLISIS ---
    tab1, tab2, tab3 = st.tabs(["📊 Análisis Semestral", "🏆 Ranking Top 50", "📋 Listado Detallado"])

    with tab1:
        st.subheader("Análisis de Tendencia (Julio 2025 - Enero 2026)")
        
        # Preparar datos para el gráfico de línea
        meses_tx = {
            'Jul': df_f['Jul 2025 TX'].sum(),
            'Ago': df_f['Ago 2025 TX'].sum(),
            'Sep': df_f['Sep 2025 TX'].sum(),
            'Oct': df_f['Oct 2025 TX'].sum(),
            'Nov': df_f['Nov 2025 TX'].sum(),
            'Dic': df_f['Dic 2025 TX'].sum(),
            'Ene': df_f['Ene 2026 TX'].sum()
        }
        df_evolucion = pd.DataFrame(list(meses_tx.items()), columns=['Mes', 'Cantidad TX'])
        
        c1, c2 = st.columns(2)
        with c1:
            fig_linea = px.line(df_evolucion, x='Mes', y='Cantidad TX', title="Tendencia de Transacciones por Mes", markers=True)
            st.plotly_chart(fig_linea, use_container_width=True)
            
        with c2:
            # Gráfico de barras por Municipio
            top_mun = df_f.groupby('Ciudad')['Tx Ultimo Semestre'].sum().nlargest(10).reset_index()
            fig_bar = px.bar(top_mun, x='Tx Ultimo Semestre', y='Ciudad', orientation='h', 
                             title="Top 10 Municipios por Actividad", color_discrete_sequence=['#0033a0'])
            st.plotly_chart(fig_bar, use_container_width=True)

    with tab2:
        st.subheader("🏆 Top 50 Corresponsales VIP")
        st.write("Ranking basado en transacciones acumuladas del último semestre.")
        
        # Creamos el Top 50
        top_50 = df.nlargest(50, 'Tx Ultimo Semestre')
        
        # Mapa de calor o tabla resaltada
        st.dataframe(top_50[['ESPECIALISTA', 'Ciudad', 'Dirección', 'Tx Ultimo Semestre', 'Ene 2026 TX', 'Estado']], 
                     use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("🔍 Consultar Corresponsales")
        busqueda = st.text_input("Escriba Dirección o Municipio para buscar rápido:")
        
        df_final = df_f.copy()
        if busqueda:
            df_final = df_f[df_f.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]
            
        st.dataframe(df_final, use_container_width=True, hide_index=True)

else:
    st.info("📢 Esperando conexión con 'datos_corresponsales.csv'. Asegúrate de que el archivo esté en la raíz de tu GitHub.")
