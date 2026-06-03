import streamlit as pd  # Si usas st para streamlit
import streamlit as st
import pandas as pd
import os

# =============================================================================
# CONFIGURACIÓN DE LA PÁGINA Y ESTILOS
# =============================================================================
st.set_page_config(
    page_title="Salaz Analytics - Gestión Comercial",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados para adaptar la interfaz al modo oscuro/claro
st.markdown("""
    <style>
        .block-container { padding-top: 2rem; padding-bottom: 2rem; }
        h1 { font-weight: 800; color: #f8f9fa; }
        .stMetric { background-color: #1e222b; padding: 15px; border-radius: 10px; border-left: 5px solid #0033a0; }
    </style>
""", unsafe_allow_html=True)


# =============================================================================
# CARGA SEGURA DE BASES DE DATOS (CON CONTROL DE ERRORES)
# =============================================================================
@st.cache_data
def cargar_datos_seguro(ruta_archivo):
    if os.path.exists(ruta_archivo):
        try:
            df = pd.read_csv(ruta_archivo)
            if df.empty:
                st.sidebar.warning(f"⚠️ El archivo '{ruta_archivo}' está vacío.")
                return None
            return df
        except pd.errors.EmptyDataError:
            st.sidebar.error(f"❌ Error: '{ruta_archivo}' no tiene columnas válidas.")
            return None
        except Exception as e:
            st.sidebar.error(f"❌ Error inesperado en '{ruta_archivo}': {e}")
            return None
    return None

# Ejecutamos la lectura de los archivos en la raíz del repositorio
df_corresponsales = cargar_datos_seguro("corresponsales_bvb.csv")
df_convenios = cargar_datos_seguro("convenios_activos.csv")


# =============================================================================
# LOGO CORPORATIVO E IDENTIDAD VISUAL - SALAZ ANALYTICS
# =============================================================================
if os.path.exists("logo-salazanalytics.svg"):
    st.image("logo-salazanalytics.svg", width=280)
    st.markdown("""
        <div style="margin-top: -10px; margin-bottom: 15px; padding-left: 5px;">
            <p style="margin: 0; font-size: 12px; color: #EBB932; text-transform: uppercase; font-weight: bold; letter-spacing: 0.5px;">
                Plataforma Inteligente de Gestión
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
            <p style="font-size: 13px; color: #EBB932; margin-top: 0px; margin-bottom: 5px; text-transform: uppercase; font-weight: bold;">Plataforma Inteligente de Gestión</p>
            <a href="https://salazanalytics.com/" target="_blank" style="color: #0033a0; text-decoration: underline; font-size: 14px; font-weight: 600;">🌐 salazanalytics.com</a>
        </div>
    """, unsafe_allow_html=True)


# =============================================================================
# MENÚ DE NAVEGACIÓN (BARRA LATERAL)
# =============================================================================
st.sidebar.title("📌 Navegación")
modulo_seleccionado = st.sidebar.radio(
    "Seleccione el módulo que desea consultar:",
    ["📊 Dashboard General", "📄 Buscador de Convenios"]
)


# =============================================================================
# MÓDULO 1: DASHBOARD GENERAL
# =============================================================================
if modulo_seleccionado == "📊 Dashboard General":
    st.title("🏦 Panel de Gestión Comercial Corresponsalía BVB")
    st.divider()
    
    if df_corresponsales is not None:
        # Métricas principales de la corresponsalía
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(label="Total Corresponsales", value=f"{len(df_corresponsales):,}")
        with col2:
            col_tx = [c for c in df_corresponsales.columns if 'TX' in c or 'TRANS' in c]
            val_tx = f"{df_corresponsales[col_tx[0]].sum():,}" if col_tx else "N/A"
            st.metric(label="Transacciones Totales", value=val_tx)
        with col3:
            col_monto = [c for c in df_corresponsales.columns if 'MONTO' in c or 'VALOR' in c]
            val_monto = f"${df_corresponsales[col_monto[0]].sum():,}" if col_monto else "N/A"
            st.metric(label="Monto Total Movilizado", value=val_monto)
            
        st.subheader("📋 Vista General de Datos")
        st.dataframe(df_corresponsales.head(200), use_container_width=True, hide_index=True)
    else:
        st.info("⏳ Por favor sube el archivo 'corresponsales_bvb.csv' para activar las métricas del Dashboard.")


# =============================================================================
# MÓDULO 2: BUSCADOR DE CONVENIOS (CON FILTRO POR DEPARTAMENTO Y OPTIMIZADO PARA MÓVIL)
# =============================================================================
elif modulo_seleccionado == "📄 Buscador de Convenios":
    st.title("📄 Consulta de Convenios Activos para Recaudo")
    st.divider()
    
    if df_convenios is not None:
        st.sidebar.subheader("🔍 Filtros de Región")
        
        # Mapeo dinámico de la columna de departamento
        col_dep_lista = [c for c in df_convenios.columns if 'DEP' in c]
        c_dep = col_dep_lista[0] if col_dep_lista else None
        
        if c_dep:
            lista_deps = ["Todos"] + sorted(df_convenios[c_dep].dropna().unique().tolist())
            dep_sel = st.sidebar.selectbox("Seleccione Departamento:", lista_deps)
        else:
            dep_sel = "Todos"
            st.sidebar.warning("⚠️ No se encontró una columna de departamento clara.")
            
        # Cuadro de texto para búsquedas específicas
        busqueda = st.text_input("🔍 Buscar convenio en tiempo real (por Empresa, Convenio o Categoría):")
        
        # Copia de trabajo para aplicar los filtros
        df_filtrado = df_convenios.copy()
        
        # 1. Aplicación del filtro por departamento
        if dep_sel != "Todos" and c_dep:
            df_filtrado = df_filtrado[df_filtrado[c_dep] == dep_sel]
            
        # 2. Aplicación del motor de búsqueda en tiempo real
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
        
        # Tarjetas dinámicas de conteo rápido
        c1, c2 = st.columns(2)
        c1.metric(label="Total Convenios en este Segmento", value=f"{len(df_filtrado):,}")
        c2.metric(label="Resultados Encontrados", value=f"{len(df_filtrado) if busqueda else 0:,}")
        
        # Visualización inteligente adaptada para cargas móviles rápidas
        st.subheader("📋 Detalle de Convenios")
        if not df_filtrado.empty:
            if not busqueda and dep_sel == "Todos":
                st.info("📱 Modo Móvil Activo: Mostrando los primeros 100 convenios. Filtra por departamento o palabra clave para ver más.")
                st.dataframe(df_filtrado.head(100), use_container_width=True, hide_index=True)
            else:
                st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
        else:
            st.info("🔍 No se encontraron convenios que coincidan con los criterios seleccionados.")
            
    else:
        st.info("⏳ Por favor sube el archivo 'convenios_activos.csv' en tu repositorio para activar este módulo.")


# =============================================================================
# PIE DE PÁGINA CORPORATIVO
# =============================================================================
st.markdown("---")
st.caption("SALAZ ANALYTICS | Plataforma Inteligente de Gestión")
