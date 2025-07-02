import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import geopandas as gpd
import json

# --- Configuración de la Página ---
st.set_page_config(
    page_title="Visualizador Orinoquia Water Futures (OWF)",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Estilos CSS Personalizados ---
st.markdown("""
<style>
    /* Estilos generales */
    .stApp {
        background-color: #f0f4f8;
    }
    /* Estilos para la barra lateral */
    .css-1d391kg {
        background-color: #ffffff;
        border-right: 1px solid #e6e6e6;
    }
    /* Estilos para los títulos */
    h1, h2, h3 {
        color: #003366; /* Azul oscuro */
    }
    /* Estilos para los botones */
    .stButton>button {
        background-color: #007bff;
        color: white;
        border-radius: 0.5rem;
        border: none;
        padding: 10px 20px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #0056b3;
        box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)


# --- MANIFIESTO DE DATOS ---
# ADVERTENCIA: Este es un manifiesto de ejemplo.
# Debes reemplazar los valores de ID con los IDs de tus propios archivos en Google Drive.
# La clave es el nombre del archivo CSV, y el valor es el ID de Google Drive.
DATA_MANIFEST = {
    "fcfs_t2_p0_d2050_c2050_l2050_results.csv": "ID_DE_TU_ARCHIVO_AQUI_1",
    "pe_t2_p0_d2050_c2050_l2050_results.csv": "ID_DE_TU_ARCHIVO_AQUI_2",
    "fcfs_t5_pn30_d2040_c2040_l2040_results.csv": "ID_DE_TU_ARCHIVO_AQUI_3",
    # Agrega aquí todas las demás combinaciones de tus escenarios
}


# --- Funciones de Lógica y Datos ---

@st.cache_data
def load_geodata(path):
    """Carga los datos geoespaciales de las cuencas desde un archivo GeoJSON."""
    try:
        gdf = gpd.read_file(path)
        gdf = gdf.to_crs("EPSG:4326")
        return gdf
    except Exception as e:
        st.error(f"Error al cargar el archivo GeoJSON de cuencas: {e}")
        return None

@st.cache_data
def load_data_from_cloud(scenario_params):
    """
    Construye la URL del archivo en la nube basado en los parámetros del escenario,
    y carga los datos en un DataFrame de pandas.
    """
    # 1. Traducir selecciones de la UI a los códigos de los nombres de archivo
    policy_code = "fcfs" if scenario_params['policy'] == "First Come First Served (FCFS)" else "pe"
    temp_code = f"t{scenario_params['tempChange']}"
    
    precip_val = scenario_params['precipChange']
    if precip_val < 0:
        precip_code = f"pn{abs(precip_val)}"
    else:
        precip_code = f"p{precip_val}"

    pop_code = f"d{scenario_params['popYear']}"
    crop_code = f"c{scenario_params['cropYear']}"
    livestock_code = f"l{scenario_params['livestockYear']}"

    # 2. Construir el nombre del archivo
    file_name = f"{policy_code}_{temp_code}_{precip_code}_{pop_code}_{crop_code}_{livestock_code}_results.csv"
    st.write(f"Buscando archivo: `{file_name}`") # Mensaje de depuración

    # 3. Buscar el ID en el manifiesto y construir la URL
    file_id = DATA_MANIFEST.get(file_name)
    
    if not file_id or file_id.startswith("ID_DE_TU_ARCHIVO"):
        st.warning(f"No se encontró un ID de archivo válido para el escenario: `{file_name}`. Se usarán datos vacíos.")
        return pd.DataFrame() # Retorna un DataFrame vacío si no se encuentra

    # URL base para descarga directa de archivos de Google Drive
    base_url = 'https://docs.google.com/uc?export=download&id='
    final_url = base_url + file_id

    # 4. Cargar los datos desde la URL
    try:
        with st.spinner(f"Descargando datos desde la nube para {file_name}..."):
            df = pd.read_csv(final_url)
            df['Date'] = pd.to_datetime(df['Date'])
            return df
    except Exception as e:
        st.error(f"Error al descargar o procesar el archivo desde la nube: {file_name}. Verifique el ID y los permisos del archivo. Error: {e}")
        return pd.DataFrame()


def calculate_stress_values(df, year=2070):
    """Calcula el índice de estrés hídrico para cada cuenca en un año específico."""
    if df.empty:
        return {}
        
    data_year = df[df['Date'].dt.year == year]
    if data_year.empty:
        return {}

    cuenca_base_names = list(set([c.split('_')[1] for c in df.columns if c.startswith('Denv_')]))
    stress_values = {}

    for base_name in cuenca_base_names:
        denv_col = f'Denv_{base_name}_cmd'
        oferta_col = f'To_downstream_from_{base_name}_cmd'
        demanda_cols = [f'Dfwr_{base_name}_cmd', f'Dfwu_{base_name}_cmd', f'Dirr_{base_name}_cmd', f'Dliv_{base_name}_cmd']
        
        # Asegurarse que las columnas existan antes de sumar
        demanda_existente = [col for col in demanda_cols if col in data_year.columns]
        if not demanda_existente or denv_col not in data_year.columns or oferta_col not in data_year.columns:
            continue

        demanda_total = data_year[demanda_existente].sum(axis=1) + data_year[denv_col]
        oferta = data_year[oferta_col]
        
        stress_index = np.divide(demanda_total, oferta, out=np.full_like(demanda_total, 10, dtype=float), where=oferta!=0)
        avg_stress = stress_index.mean()
        stress_values[base_name] = avg_stress
        
    return stress_values

# --- Componentes de la Interfaz de Usuario (UI) ---

def sidebar_ui():
    """Crea la barra lateral con los controles de los escenarios."""
    st.sidebar.image("https://www.thegef.org/sites/default/files/styles/gef_landscape_image/public/2022-04/colombia-orinoquia-river-basin.jpg", use_column_width=True)
    st.sidebar.title("Configuración de Escenarios")
    
    with st.sidebar.expander("**Escenario 1**", expanded=True):
        s1_params = scenario_controls("s1")
    
    st.sidebar.markdown("---")
    
    with st.sidebar.expander("**Escenario 2**", expanded=True):
        s2_params = scenario_controls("s2")
        
    st.sidebar.markdown("---")
    
    generate_button = st.sidebar.button("Generar Comparación y Gráficos", use_container_width=True)
    
    return s1_params, s2_params, generate_button

def scenario_controls(key_prefix):
    """Crea un conjunto de controles para un escenario."""
    params = {}
    params['policy'] = st.selectbox("Política de Asignación:", ["First Come First Served (FCFS)", "Policy Enforced (PE)"], key=f"policy_{key_prefix}")
    params['tempChange'] = st.slider("Cambio de Temperatura (°C):", 0, 5, 2, key=f"temp_{key_prefix}")
    params['precipChange'] = st.slider("Cambio de Precipitación (%):", -30, 30, 0, 10, key=f"precip_{key_prefix}")
    params['popYear'] = st.selectbox("Año Proy. Población:", [2022, 2030, 2040, 2050], index=3, key=f"pop_{key_prefix}")
    params['cropYear'] = st.selectbox("Año Proy. Cultivos:", [2022, 2030, 2040, 2050], index=3, key=f"crop_{key_prefix}")
    params['livestockYear'] = st.selectbox("Año Proy. Pecuario:", [2022, 2030, 2040, 2050], index=3, key=f"livestock_{key_prefix}")
    return params

# --- Funciones de Gráficos ---

def plot_stress_map(gdf, stress_data_s1, stress_data_s2):
    """Dibuja el mapa coroplético con el estrés hídrico."""
    if gdf is None:
        return
    
    cuenca_mapping = {
        "1": "Garagoa", "2": "Guatiquia", "3": "Guayuriba", "4": "Humea", "5": "Negro",
        "6": "Upia", "7": "Lengupa", "8": "Guanapalo", "9": "Pauto", "10": "Cusiana",
        "11": "Cravo sur", "12": "Tua", "13": "Manacacias", "14": "Metica", "15": "Guavio",
        "16": "Yucao", "17": "Melua"
    }

    gdf['stress_s1'] = gdf['NombreD'].map(lambda x: stress_data_s1.get(cuenca_mapping.get(str(x)), 0))
    gdf['stress_s2'] = gdf['NombreD'].map(lambda x: stress_data_s2.get(cuenca_mapping.get(str(x)), 0))

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Mapa de Estrés Hídrico - Escenario 1")
        fig1 = px.choropleth_mapbox(gdf, geojson=gdf.geometry, locations=gdf.index, color="stress_s1",
                                   color_continuous_scale="Reds", range_color=(0, 2),
                                   mapbox_style="carto-positron", zoom=5.5, center={"lat": 4.5, "lon": -72.5},
                                   opacity=0.6, labels={'stress_s1': 'Índice de Estrés'}, hover_name="NOMSZH")
        fig1.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig1, use_container_width=True)
        
    with col2:
        st.subheader("Mapa de Estrés Hídrico - Escenario 2")
        fig2 = px.choropleth_mapbox(gdf, geojson=gdf.geometry, locations=gdf.index, color="stress_s2",
                                   color_continuous_scale="Reds", range_color=(0, 2),
                                   mapbox_style="carto-positron", zoom=5.5, center={"lat": 4.5, "lon": -72.5},
                                   opacity=0.6, labels={'stress_s2': 'Índice de Estrés'}, hover_name="NOMSZH")
        fig2.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig2, use_container_width=True)

def plot_demand_composition(df, title):
    """Dibuja un gráfico de pie con la composición de la demanda."""
    if df is None or df.empty:
        st.warning(f"No hay datos para generar el gráfico de demanda para: {title}")
        return
        
    demand_cols = [col for col in df.columns if col.startswith(('Denv_', 'Dfwr_', 'Dfwu_', 'Dirr_', 'Dliv_'))]
    demand_totals = df[demand_cols].sum()
    
    composition = {
        "Ambiental": demand_totals[[c for c in demand_cols if 'Denv_' in c]].sum(),
        "Rural": demand_totals[[c for c in demand_cols if 'Dfwr_' in c]].sum(),
        "Urbano": demand_totals[[c for c in demand_cols if 'Dfwu_' in c]].sum(),
        "Irrigación": demand_totals[[c for c in demand_cols if 'Dirr_' in c]].sum(),
        "Pecuario": demand_totals[[c for c in demand_cols if 'Dliv_' in c]].sum(),
    }
    
    df_comp = pd.DataFrame(list(composition.items()), columns=['Componente', 'Valor'])
    
    fig = px.pie(df_comp, values='Valor', names='Componente', title=title, hole=0.3)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)

# --- Aplicación Principal ---

def main():
    """Función principal que ejecuta la aplicación Streamlit."""
    
    st.title("💧 Visualizador de Escenarios Hídricos - Orinoquia Water Futures")
    st.markdown("Esta herramienta permite comparar dinámicamente dos escenarios de recursos hídricos para la cuenca del río Meta, basados en el modelo OWF.")
    st.info("**Importante:** Esta aplicación se conecta a datos en la nube. Edite el diccionario `DATA_MANIFEST` en el código `app.py` con los IDs de sus propios archivos de Google Drive para que funcione correctamente.")

    gdf = load_geodata("soporte/cuencas/cuencas.json")
    s1_params, s2_params, generate_button = sidebar_ui()
    
    if generate_button:
        # Cargar datos desde la nube en lugar de generar datos de prueba
        df_s1 = load_data_from_cloud(s1_params)
        df_s2 = load_data_from_cloud(s2_params)
        
        # Continuar solo si se cargaron datos para ambos escenarios
        if df_s1.empty or df_s2.empty:
            st.error("No se pudieron cargar los datos para uno o ambos escenarios. Por favor, verifique la configuración y el manifiesto de datos.")
        else:
            stress_s1 = calculate_stress_values(df_s1)
            stress_s2 = calculate_stress_values(df_s2)

            st.header("Análisis de Estrés Hídrico por Cuenca (Año 2070)")
            plot_stress_map(gdf, stress_s1, stress_s2)
            
            st.markdown("---")
            
            st.header("Composición de la Demanda de Agua Anual")
            col1, col2 = st.columns(2)
            with col1:
                plot_demand_composition(df_s1, "Escenario 1")
            with col2:
                plot_demand_composition(df_s2, "Escenario 2")
    else:
        st.info("Configure los escenarios en la barra lateral y presione 'Generar Comparación' para ver los resultados.")

if __name__ == "__main__":
    main()
