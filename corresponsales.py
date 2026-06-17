import streamlit as st
import pandas as pd
import plotly.express as px
import os

# =============================================================================
# 1. CONFIGURACIÓN DE LA PÁGINA Y ESTILOS
# =============================================================================
st.set_page_config(
    page_title="Salaz Analytics - Gestión Comercial",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados para adaptar la interfaz
st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    
    /* Fuerza el color del número (azul corporativo) */
    [data-testid="stMetricValue"] { 
        color: #0033a0 !important; 
        font-weight: bold !important; 
    }
    
    /* Fuerza el color del título del cuadro (gris oscuro visible) */
    [data-testid="stMetricLabel"] { 
        color: #222222 !important; 
        font-weight: 600 !important;
        font-size: 15px !important;
    }
    
    /* Estructura de las tarjetas de métricas */
    div[data-testid="stMetric"] {
        background-color: #ffffff !important;
        border-left: 5px solid #EBB932 !important;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1) !important;
        border-radius: 5px !important;
        padding: 10px 15px !important;
    }
    </style>
""", unsafe_allow_html=True)


# =============================================================================
# 2. CARGA SEGURA DE BASES DE DATOS (CON SOPORTE EXCEL PARA EJE CAFETERO)
# =============================================================================
@st.cache_data(ttl=600)
def cargar_datos_corresponsales():
    archivo_csv = "datos_corresponsales.csv"
    archivo_excel = "PUNTOS EJE CAFETERO.xlsx"
    df = None
    
    # 1. Intentar cargar primero el CSV si existe
    if os.path.exists(archivo_csv):
        try:
            try:
                df = pd.read_csv(archivo_csv, sep=',', engine='python', on_bad_lines='skip')
                if len(df.columns) <= 1: raise ValueError
            except:
                df = pd.read_csv(archivo_csv, sep=';', engine='python', on_bad_lines='skip')
        except:
            df = None

    # 2. Si el CSV no existe o falló, intentar cargar el Excel de PUNTOS EJE CAFETERO
    if df is None and os.path.exists(archivo_excel):
        try:
            # Lee la primera pestaña por defecto
            df = pd.read_excel(archivo_excel, engine="openpyxl")
        except:
            df = None
            
    # Si no se encuentra ningún archivo válido, retornamos None
    if df is None:
        return None
        
    try:
        # Limpieza de nombres de columnas
        df.columns = [str(c).strip() for c in df.columns]
        
        # Desduplicar columnas
        columnas_limpias = []
        conteo_columnas = {}
        for col in df.columns:
            if col in conteo_columnas:
                conteo_columnas[col] += 1
                columnas_limpias.append(f"{col}.{conteo_columnas[col]}")
            else:
                conteo_columnas[col] = 0
                columnas_limpias.append(col)
        df.columns = columnas_limpias
        
        # Estandarizar ciudades (Mapea 'Ciudad' o la segunda columna)
        col_mun = 'Ciudad' if 'Ciudad' in df.columns else df.columns[1]
        if col_mun in df.columns:
            df[col_mun] = df[col_mun].astype(str).str.strip().str.upper()
            
        return df
    except:
        return None

@st.cache_data(ttl=3600)
def cargar_datos_convenios():
    archivo_excel = "listado-de-convenios-activos-corresponsales mayo 2.xlsx"
    
    if not os.path.exists(archivo_excel):
        return None
        
    try:
        df_header = pd.read_excel(archivo_excel, sheet_name="Convenios", header=1, nrows=5, engine="openpyxl")
        df_header.columns = [str(c).strip().upper() for c in df_header.columns]
        
        col_conv = [c for c in df_header.columns if 'CONV' in c]
        col_emp = [c for c in df_header.columns if 'EMP' in c]
        col_cat = [c for c in df_header.columns if 'CAT' in c]
        col_dep = [c for c in df_header.columns if 'DEP' in c]
        col_nit = [c for c in df_header.columns if 'NIT' in c or 'IDENTI' in c]
        
        columnas_a_cargar = []
        if col_conv: columnas_a_cargar.append(col_conv[0])
        if col_emp: columnas_a_cargar.append(col_emp[0])
        if col_cat: columnas_a_cargar.append(col_cat[0])
        if col_dep: columnas_a_cargar.append(col_dep[0])
        if col_nit: columnas_a_cargar.append(col_nit[0])
        
        if columnas_a_cargar:
            df = pd.read_excel(
                archivo_excel, 
                sheet_name="Convenios", 
                header=1,
                usecols=columnas_a_cargar,
                engine="openpyxl"
            )
        else:
            df = pd.read_excel(archivo_excel, sheet_name="Convenios", header=1, engine="openpyxl")
            
        df.columns = [str(c).strip().upper() for c in df.columns]
        return df
    except Exception as e:
        try:
            df = pd.read_excel(archivo_excel, header=1, engine="openpyxl")
            df.columns = [str(c).strip().upper() for c in df.columns]
            return df
        except:
            return None

# Carga global de datos
df = cargar_datos_corresponsales()
df_convenios = cargar_datos_convenios()


# =============================================================================
# 3. LOGO CORPORATIVO E IDENTIDAD VISUAL - SALAZ ANALYTICS
# =============================================================================
if os.path.exists("logo-salazanalytics.svg"):
    st.image("logo-salazanalytics.svg", width=280)
    st.markdown("""
        <div style="margin-top: -10px; margin-bottom: 15px; padding-left: 5px;">
            <p style="margin: 0; font-size: 12px; color: #EBB932; text-transform: uppercase; font-weight: bold; letter-spacing: 0.5px;">
                SALAZ ANALYTICS Plataforma Inteligente de Gestión
            </p>
            <a href="https://salazanalytics.com/" target="_blank" style="color: #0033a0; text-decoration: underline; font-size: 14px; font-weight: 600;">
                🌐 salazanalytics.com
            </a>
        </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <div style="text-align: left; margin-bottom: 15px;">
            <h2 style="margin-bottom: 0px; color: #0033a0; letter-spacing: 1px; font-weight: bold; font-size: 28px;">SALAZ ANALYTICS</h2>
            <p style="font-size: 13px; color: #EBB932; margin-top: 0px; margin-bottom: 5px; text-transform: uppercase; font-weight: bold;">SALAZ ANALYTICS Plataforma Inteligente de Gestión</p>
            <a href="https://salazanalytics.com/" target="_blank" style="color: #0033a0; text-decoration: underline; font-size: 14px; font-weight: 600;">🌐 salazanalytics.com</a>
        </div>
    """, unsafe_allow_html=True)


# =============================================================================
# 4. MENÚ DE NAVEGACIÓN (BARRA LATERAL)
# =============================================================================
st.sidebar.title("Navegación")
modulo_seleccionado = st.sidebar.radio(
    "Seleccione el Módulo:", 
    ["📊 Dashboard Corresponsales", "📄 Buscador de Convenios"]
)
st.sidebar.markdown("---")


# =============================================================================
# MÓDULO 1: DASHBOARD DE CORRESPONSALES
# =============================================================================
if modulo_seleccionado == "📊 Dashboard Corresponsales":
    st.title("Panel de Gestión Integral de Corresponsales Bancarios")
    st.divider()
    
    if df is not None:
        st.sidebar.header("🔍 Filtros de Gestión")
        
        col_esp = 'ESPECIALISTA' if 'ESPECIALISTA' in df.columns else df.columns[0]
        lista_esp = ["Todos"] + sorted(df[col_esp].dropna().unique().tolist())
        esp_sel = st.sidebar.selectbox("Especialista Comercial:", lista_esp)
        
        col_mun = 'Ciudad' if 'Ciudad' in df.columns else df.columns[1]
        lista_ciu = ["Todos"] + sorted(df[col_mun].dropna().unique().tolist())
        ciu_sel = st.sidebar.selectbox("Municipio / Ciudad:", lista_ciu)
        
        df_f = df.copy()
        if esp_sel != "Todos":
            df_f = df_f[df_f[col_esp] == esp_sel]
        if ciu_sel != "Todos":
            df_f = df_f[df_f[col_mun] == ciu_sel]

        # --- TARJETAS DE MÉTRICAS ---
        m1, m2, m3, m4 = st.columns(4)
        m1.metric(label="👥 Total Corresponsales", value=f"{len(df_f):,}")
        
        tx_sem = 'Tx Ultimo Semestre' if 'Tx Ultimo Semestre' in df_f.columns else df_f.columns[3]
        tx_sum_val = pd.to_numeric(df_f[tx_sem], errors='coerce').fillna(0).sum()
        m2.metric(label="📊 TX Total Semestre", value=f"{tx_sum_val:,.0f}")
        
        activos = len(df_f[df_f['Transa si/no MES'] == 'Si']) if 'Transa si/no MES' in df_f.columns else 0
        m3.metric(label="✅ Puntos Activos", value=f"{activos:,}")
        
        dinero_ene = 'Ene 2026 $$' if 'Ene 2026 $$' in df_f.columns else df_f.columns[-1]
        dinero_sum_val = pd.to_numeric(df_f[dinero_ene], errors='coerce').fillna(0).sum()
        m4.metric(label="💰 Volumen Ene ($$)", value=f"$ {dinero_sum_val:,.0f}")

        # --- GRÁFICOS ---
        st.subheader("Análisis de Transacciones por Mes")
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

        st.subheader("Top 50 Corresponsales")
        
        # SOLUCIÓN: Convertimos la columna a numérica reemplazando errores por NaN de forma segura
        df_top = df.copy()
        df_top[tx_sem] = pd.to_numeric(df_top[tx_sem], errors='coerce').fillna(0)
        
        # --- TABLA DE DETALLE DINÁMICA ---
        if ciu_sel != "Todos":
            st.subheader(f"Corresponsales en {ciu_sel.title()}")
        else:
            st.subheader("Top 50 Corresponsales de la Red")
        
        # 1. Copiamos los datos ya filtrados por Especialista y Municipio
        df_top = df_f.copy()
        
        # 2. Aseguramos que la columna de transacciones sea numérica para poder ordenar
        df_top[tx_sem] = pd.to_numeric(df_top[tx_sem], errors='coerce').fillna(0)
        
        # 3. Si seleccionó un municipio específico, calculamos cuántos registros mostrar
        # (Si hay menos de 50 puntos en ese municipio, los muestra todos de una vez)
        limite_filas = min(50, len(df_top))
        
        if limite_filas > 0:
            top_dinamico = df_top.nlargest(limite_filas, tx_sem)
            st.dataframe(top_dinamico, use_container_width=True, hide_index=True)
        else:
            st.info("🔍 No hay registros disponibles para los filtros seleccionados.")


# =============================================================================
# MÓDULO 2: BUSCADOR DE CONVENIOS (CON SELECTOR DE DEPARTAMENTO INTEGRADO)
# =============================================================================
elif modulo_seleccionado == "📄 Buscador de Convenios":
    st.title("Consulta de Convenios Activos para Recaudo")
    st.divider()
    
    st.sidebar.header("🔍 Filtros de Convenios")
    
    if df_convenios is not None:
        col_dep_lista = [c for c in df_convenios.columns if 'DEP' in c]
        c_dep = col_dep_lista[0] if col_dep_lista else None
        
        if c_dep:
            lista_deps = ["Todos"] + sorted(df_convenios[c_dep].dropna().unique().tolist())
            dep_sel = st.sidebar.selectbox("Seleccione Departamento / Región:", lista_deps)
        else:
            dep_sel = "Todos"
            st.sidebar.warning("⚠️ No se detectó la columna 'DEPARTAMENTO' en el Excel.")
            
        busqueda = st.text_input("🔍 Buscar convenio en tiempo real (por Empresa, Convenio o Categoría):")
        
        df_filtrado = df_convenios.copy()
        
        if dep_sel != "Todos" and c_dep:
            df_filtrado = df_filtrado[df_filtrado[c_dep] == dep_sel]
            
        if busqueda:
            busqueda_str = str(busqueda).lower()
            col_emp = [c for c in df_filtrado.columns if 'EMP' in c]
            col_conv = [c for c in df_filtrado.columns if 'CONV' in c]
            col_cat = [c for c in df_filtrado.columns if 'CAT' in c]
            
            c_emp = col_emp[0] if col_emp else df_filtrado.columns[0]
            c_conv = col_conv[0] if col_conv else df_filtrado.columns[1]
            c_cat = col_cat[0] if col_cat else df_filtrado.columns[2]
            
            df_filtrado = df_filtrado[
                df_filtrado[c_emp].astype(str).str.lower().str.contains(busqueda_str) |
                df_filtrado[c_conv].astype(str).str.lower().str.contains(busqueda_str) |
                df_filtrado[c_cat].astype(str).str.lower().str.contains(busqueda_str)
            ]
        
        c1, c2 = st.columns(2)
        c1.metric(label="Total Convenios en este Segmento", value=f"{len(df_filtrado):,}")
        c2.metric(label="Resultados Encontrados", value=f"{len(df_filtrado) if busqueda else 0:,}")
        
        st.subheader("Detalle de Convenios")
        if not df_filtrado.empty:
            if not busqueda and dep_sel == "Todos":
                st.info("📱 Optimización móvil activa: Mostrando los primeros 100 registros. Filtra por departamento o palabra clave para desplegar más.")
                st.dataframe(df_filtrado.head(100), use_container_width=True, hide_index=True)
            else:
                st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
        else:
            st.info("🔍 No se encontraron convenios que coincidan con los filtros aplicados.")
            
    else:
        st.sidebar.selectbox("Seleccione Departamento / Región:", ["Esperando archivo Excel..."], disabled=True)
        st.error("⚠️ No se detectó el archivo en la raíz. Recuerda subir a GitHub el archivo: 'listado-de-convenios-activos-corresponsales mayo 2.xlsx'")

# PIE DE PÁGINA CORPORATIVO
st.markdown("---")
st.caption("SALAZ ANALYTICS Plataforma Inteligente de Gestión")
