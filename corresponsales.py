import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. CONFIGURACIÓN E IDENTIDAD VISUAL
st.set_page_config(page_title="BVB - Gestión Estratégica", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    [data-testid="stMetricValue"] { color: #0033a0 !important; font-weight: bold; }
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border-left: 5px solid #EBB932;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# ENCABEZADO DE MARCA EN LUGAR DE TÍTULO PLANO
st.markdown("""
    <div style="text-align: left;">
        <h2 style="margin-bottom: 0px; color: #0033a0; letter-spacing: 2px; font-weight: bold;">SALAZ ANALYTICS</h2>
        <p style="font-size: 14px; color: #EBB932; margin-top: 0px; text-transform: uppercase; font-weight: bold;">Plataforma Inteligente de Gestión</p>
    </div>
""", unsafe_allow_html=True)
st.title("🏦 Gestión Integral de Corresponsalía BVB")
st.divider()

# 2. CARGA DE DATOS BLINDADA Y OPTIMIZADA (Para Corresponsales)
@st.cache_data(ttl=600)  # Volvemos al tiempo original que te funcionaba bien
def cargar_datos_corresponsales():
    try:
        if not os.path.exists("datos_corresponsales.csv"):
            return None
            
        # Volvemos a tu lógica original exacta de lectura que ya estaba blindada
        try:
            df = pd.read_csv("datos_corresponsales.csv", sep=',', engine='python', on_bad_lines='skip')
            if len(df.columns) <= 1: # Si solo detecta una columna, el separador es incorrecto
                raise ValueError
        except:
            df = pd.read_csv("datos_corresponsales.csv", sep=';', engine='python', on_bad_lines='skip')
        
        # Limpieza de nombres de columnas
        df.columns = [str(c).strip() for c in df.columns]
        
        # Lista de columnas financieras y de transacciones según tu configuración
        cols_num = [
            'Tx Ultimo Semestre', 'Jul 2025 TX', 'Ago 2025 TX', 'Sep 2025 TX', 
            'Oct 2025 TX', 'Nov 2025 TX', 'Dic 2025 TX', 'Ene 2026 TX',
            'Ene 2026 $$', 'Ago 2025 $$', 'Sep 2025 $$', 'Oct 2025 $$', 
            'Nov 2025 $$', 'Dic 2025 $$', 'Transa'
        ]
        
        for col in cols_num:
            if col in df.columns:
                # Quitamos símbolos de pesos, espacios y comas para que sean números reales
                df[col] = df[col].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False).str.strip()
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Error técnico al leer el archivo: {e}")
        return None

# 3. CARGA ULTRA RÁPIDA PARA EL NUEVO ARCHIVO DE CONVENIOS (24K+ registros)
@st.cache_data(ttl=3600)
def cargar_datos_convenios():
    """
    Carga el listado de convenios directamente desde el archivo Excel de GitHub.
    """
    archivo_excel = "listado-de-convenios-activos-corresponsales mayo 2.xlsx"
    
    if os.path.exists(archivo_excel):
        try:
            # header=1 le dice a Python que ignore la fila del título 
            # y use la fila de (ESTADO, NIT, EMPRESA...) como las columnas reales.
            df_conv = pd.read_excel(archivo_excel, sheet_name="Convenios", header=1)
            
            # Limpiamos espacios en blanco en los nombres de las columnas por seguridad
            df_conv.columns = [str(c).strip() for c in df_conv.columns]
            return df_conv
        except Exception as e:
            st.error(f"Error al procesar el archivo Excel: {e}")
            return None
            
    return None


# --- MENÚ DE NAVEGACIÓN EN LA BARRA LATERAL ---
st.sidebar.title("Navegación")
modulo_seleccionado = st.sidebar.radio("Seleccione el Módulo:", ["📊 Dashboard Corresponsales", "📄 Buscador de Convenios"])
st.sidebar.markdown("---")

# Carga en memoria en paralelo usando los cachés independientes
df = cargar_datos_corresponsales()
df_convenios = cargar_datos_convenios()


# ==========================================
# MÓDULO 1: TU DASHBOARD ORIGINAL
# ==========================================
if modulo_seleccionado == "📊 Dashboard Corresponsales":
    if df is not None:
        # --- FILTROS LATERALES (Solo se muestran en este módulo) ---
        st.sidebar.header("🔍 Filtros de Gestión")
        
        col_esp = 'ESPECIALISTA' if 'ESPECIALISTA' in df.columns else df.columns[0]
        lista_esp = ["Todos"] + sorted(df[col_esp].dropna().unique().tolist())
        esp_sel = st.sidebar.selectbox("Especialista Comercial:", lista_esp)
        
        col_mun = 'Ciudad' if 'Ciudad' in df.columns else df.columns[1]
        lista_ciu = ["Todos"] + sorted(df[col_mun].dropna().unique().tolist())
        ciu_sel = st.sidebar.selectbox("Municipio / Ciudad:", lista_ciu)
        
        # Aplicar Filtros
        df_f = df.copy()
        if esp_sel != "Todos":
            df_f = df_f[df_f[col_esp] == esp_sel]
        if ciu_sel != "Todos":
            df_f = df_f[df_f[col_mun] == ciu_sel]

        # --- MÉTRICAS DE ALTO NIVEL ---
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Corresponsales", f"{len(df_f):,}")
        
        tx_sem = 'Tx Ultimo Semestre' if 'Tx Ultimo Semestre' in df_f.columns else 'Transa'
        
        # Aseguramos que los valores sean numéricos antes de sumar
        tx_sum_val = pd.to_numeric(df_f[tx_sem], errors='coerce').fillna(0).sum()
        m2.metric("TX Total Semestre", f"{tx_sum_val:,.0f}")
        
        activos = len(df_f[df_f['Transa si/no MES'] == 'Si']) if 'Transa si/no MES' in df_f.columns else 0
        m3.metric("Puntos Activos", f"{activos:,}")
        
        # BLINDAJE DE LA MÉTRICA DE DINERO (Línea 137)
        dinero_ene = 'Ene 2026 $$' if 'Ene 2026 $$' in df_f.columns else df_f.columns[-1]
        
        # Forzamos la conversión a número, los errores se vuelven 0 para que no rompan la app
        dinero_sum_val = pd.to_numeric(df_f[dinero_ene], errors='coerce').fillna(0).sum()
        
        m4.metric("Volumen Ene ($$)", f"$ {dinero_sum_val:,.0f}")


# ==========================================
# MÓDULO 2: NUEVO ARCHIVO (CONVENIOS) OPTIMIZADO
# ==========================================
# --- CUERPO DEL DASHBOARD (VERSION LINEAL SIN TABS) ---
        st.subheader("Análisis de Transacciones por Mes (Jul 2025 - Ene 2026)")
        meses_cols = ['Jul 2025 TX', 'Ago 2025 TX', 'Sep 2025 TX', 'Oct 2025 TX', 'Nov 2025 TX', 'Dic 2025 TX', 'Ene 2026 TX']
        meses_existentes = [m for m in meses_cols if m in df_f.columns]
        
        if meses_existentes:
            data_meses = df_f[meses_existentes].sum().reset_index()
            data_meses.columns = ['Mes', 'Transacciones']
            
            c1, c2 = st.columns([2, 1])
            with c1:
                fig_line = px.line(data_meses, x='Mes', y='Transacciones', markers=True, 
                                   title="Evolución de la Red", color_discrete_sequence=['#0033a0'])
                st.plotly_chart(fig_line, use_container_width=True)
            with c2:
                mun_data = df_f.groupby(col_mun)[tx_sem].sum().nlargest(10).reset_index()
                fig_bar = px.bar(mun_data, x=tx_sem, y=col_mun, orientation='h', 
                                 title="Top 10 Municipios", color_discrete_sequence=['#EBB932'])
                st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.warning("No se encontraron las columnas mensuales de transacciones.")

        st.subheader("🏆 Top 50 Corresponsales con Mejor Desempeño")
        top_50 = df.nlargest(50, tx_sem)
        cols_ranking = [col_esp, col_mun, 'Dirección', tx_sem, 'Ene 2026 TX', 'Estado']
        cols_show = [c for c in cols_ranking if c in top_50.columns]
        st.dataframe(top_50[cols_show], use_container_width=True, hide_index=True)

        # COLLAPSIBLE / SECCIÓN DE BASE DE DATOS REPARADA
        st.subheader("📋 Base de Datos Completa")
        txt_busqueda = st.text_input("Buscar por dirección o nombre específico:")
        
        df_view = df_f.copy()
        if txt_busqueda:
            # Buscamos de manera inteligente y rápida por texto para evitar que se rompa
            busqueda_str = str(txt_busqueda).lower()
            
            # Detectamos dinámicamente las columnas de texto de tu archivo
            col_dir = 'Dirección' if 'Dirección' in df_view.columns else df_view.columns[2]
            col_nom = 'Nombre' if 'Nombre' in df_view.columns else df_view.columns[0]
            
            df_view = df_view[
                df_view[col_dir].astype(str).str.lower().str.contains(busqueda_str) |
                df_view[col_nom].astype(str).str.lower().str.contains(busqueda_str)
            ]
        
        st.write(f"Mostrando {len(df_view)} registros")
        
        # Muestra la información de manera segura
        if not df_view.empty:
            st.dataframe(df_view, use_container_width=True, hide_index=True)
        else:
            st.info("🔍 No se encontraron registros que coincidan con la búsqueda.")

elif modulo_seleccionado == "📄 Buscador de Convenios":
    st.header("📄 Consulta de Convenios Activos para Recaudo")
    
    if df_convenios is not None:
        busqueda = st.text_input("🔍 Buscar convenio en tiempo real (por Empresa, Convenio o Categoría):")
        
        df_filtrado = df_convenios.copy()
        if busqueda:
            # Optimizamos la búsqueda para que no congele la app con las 24K filas
            busqueda_str = str(busqueda).lower()
            df_filtrado = df_convenios[
                df_convenios['EMPRESA'].astype(str).str.lower().str.contains(busqueda_str) |
                df_convenios['CONVENIO'].astype(str).str.lower().str.contains(busqueda_str) |
                df_convenios['CATEGORIA'].astype(str).str.lower().str.contains(busqueda_str)
            ]
        
        # Indicadores resumidos
        c1, c2 = st.columns(2)
        c1.metric("Total Convenios Cargados", f"{len(df_convenios):,}")
        c2.metric("Resultados Encontrados", f"{len(df_filtrado):,}")
        
        # Mostrar tabla paginada e inteligente
        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
    else:
        st.error("⚠️ No se encontró el listado de convenios. Sube 'convenios_activos.csv' o el archivo Excel a tu GitHub.")

# PIE DE PÁGINA CORPORATIVO
st.markdown("---")
st.caption("SALAZ ANALYTICS | Gestión de Datos en Tiempo Real")
