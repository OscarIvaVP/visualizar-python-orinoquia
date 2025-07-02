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


# --- Funciones de Lógica y Datos ---

@st.cache_data
def load_geodata(path):
    """Carga los datos geoespaciales de las cuencas desde un archivo GeoJSON."""
    try:
        gdf = gpd.read_file(path)
        # Asegurarse de que el CRS sea el correcto para Plotly
        gdf = gdf.to_crs("EPSG:4326")
        return gdf
    except Exception as e:
        st.error(f"Error al cargar el archivo GeoJSON de cuencas: {e}")
        return None

@st.cache_data
def generate_mock_data(scenario_params, start_year=2020, end_year=2070):
    """
    Genera datos simulados (mock data) para un escenario dado.
    En una implementación real, esta función se conectaría al modelo Pywr
    o a una base de datos con los resultados de la simulación.
    """
    np.random.seed(sum(ord(c) for c in json.dumps(scenario_params)))
    
    dates = pd.to_datetime(pd.date_range(start=f'{start_year}-01-01', end=f'{end_year}-12-31', freq='MS'))
    num_records = len(dates)
    
    # Nombres base de las cuencas (extraídos del código original)
    cuenca_base_names = [
        "Cravo_sur", "Pauto", "Tua", "Cusiana", "Upia", "Guanapalo", "Lengupa", 
        "Guatiquia", "Guayuriba", "Metica", "Humea", "Guavio", "Negro", "Garagoa",
        "Manacacias", "Melua", "Yucao"
    ]
    
    data = {"Date": dates.strftime('%Y-%m-%d')}
    
    # Generar columnas de datos aleatorios pero plausibles
    for cuenca in cuenca_base_names:
        # Oferta de agua (To_downstream)
        oferta_base = np.random.uniform(50, 500)
        data[f'To_downstream_from_{cuenca}_cmd'] = np.random.normal(oferta_base, oferta_base * 0.4, num_records).clip(0)
        
        # Demandas
        data[f'Denv_{cuenca}_cmd'] = np.random.normal(oferta_base * 0.1, oferta_base * 0.05, num_records).clip(0)
        data[f'Dfwr_{cuenca}_cmd'] = np.random.normal(oferta_base * 0.05, oferta_base * 0.02, num_records).clip(0)
        data[f'Dfwu_{cuenca}_cmd'] = np.random.normal(oferta_base * 0.08, oferta_base * 0.03, num_records).clip(0)
        data[f'Dirr_{cuenca}_cmd'] = np.random.normal(oferta_base * 0.15, oferta_base * 0.08, num_records).clip(0)
        data[f'Dliv_{cuenca}_cmd'] = np.random.normal(oferta_base * 0.03, oferta_base * 0.01, num_records).clip(0)

    df = pd.DataFrame(data)
    df['Date'] = pd.to_datetime(df['Date'])
    return df

def calculate_stress_values(df, year=2070):
    """Calcula el índice de estrés hídrico para cada cuenca en un año específico."""
    data_year = df[df['Date'].dt.year == year]
    if data_year.empty:
        return {}

    cuenca_base_names = list(set([c.split('_')[1] for c in df.columns if c.startswith('Denv_')]))
    stress_values = {}

    for base_name in cuenca_base_names:
        denv_col = f'Denv_{base_name}_cmd'
        oferta_col = f'To_downstream_from_{base_name}_cmd'
        demanda_cols = [f'Dfwr_{base_name}_cmd', f'Dfwu_{base_name}_cmd', f'Dirr_{base_name}_cmd', f'Dliv_{base_name}_cmd']
        
        demanda_total = data_year[demanda_cols].sum(axis=1) + data_year[denv_col]
        oferta = data_year[oferta_col]
        
        # Evitar división por cero
        stress_index = np.divide(demanda_total, oferta, out=np.full_like(demanda_total, 10), where=oferta!=0)
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
    
    # Mapear nombres de cuencas del GeoJSON a los datos de estrés
    # Esto es una suposición y podría necesitar ajustes con los datos reales
    cuenca_mapping = {
        "1": "Garagoa", "2": "Guatiquia", "3": "Guayuriba", "4": "Humea", "5": "Negro",
        "6": "Upia", "7": "Lengupa", "8": "Guanapalo", "9": "Pauto", "10": "Cusiana",
        "11": "Cravo sur", "12": "Tua", "13": "Manacacias", "14": "Metica", "15": "Guavio",
        "16": "Yucao", "17": "Melua"
    }

    gdf['stress_s1'] = gdf['NombreD'].map(lambda x: stress_data_s1.get(cuenca_mapping.get(x), 0))
    gdf['stress_s2'] = gdf['NombreD'].map(lambda x: stress_data_s2.get(cuenca_mapping.get(x), 0))

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Mapa de Estrés Hídrico - Escenario 1")
        fig1 = px.choropleth_mapbox(
            gdf,
            geojson=gdf.geometry,
            locations=gdf.index,
            color="stress_s1",
            color_continuous_scale="Reds",
            range_color=(0, 2),
            mapbox_style="carto-positron",
            zoom=5.5,
            center={"lat": 4.5, "lon": -72.5},
            opacity=0.6,
            labels={'stress_s1': 'Índice de Estrés'},
            hover_name="NOMSZH"
        )
        fig1.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig1, use_container_width=True)
        
    with col2:
        st.subheader("Mapa de Estrés Hídrico - Escenario 2")
        fig2 = px.choropleth_mapbox(
            gdf,
            geojson=gdf.geometry,
            locations=gdf.index,
            color="stress_s2",
            color_continuous_scale="Reds",
            range_color=(0, 2),
            mapbox_style="carto-positron",
            zoom=5.5,
            center={"lat": 4.5, "lon": -72.5},
            opacity=0.6,
            labels={'stress_s2': 'Índice de Estrés'},
            hover_name="NOMSZH"
        )
        fig2.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig2, use_container_width=True)

def plot_demand_composition(df, title):
    """Dibuja un gráfico de pie con la composición de la demanda."""
    if df is None:
        st.warning(f"No hay datos para generar el gráfico: {title}")
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

    # Cargar datos geoespaciales
    gdf = load_geodata("soporte/cuencas/cuencas.json")

    # Controles de la barra lateral
    s1_params, s2_params, generate_button = sidebar_ui()
    
    if generate_button:
        with st.spinner("Generando datos y gráficos para los escenarios... Por favor espere."):
            # Generar datos para ambos escenarios
            df_s1 = generate_mock_data(s1_params)
            df_s2 = generate_mock_data(s2_params)
            
            # Calcular estrés hídrico para los mapas
            stress_s1 = calculate_stress_values(df_s1)
            stress_s2 = calculate_stress_values(df_s2)

            # Mostrar mapas
            st.header("Análisis de Estrés Hídrico por Cuenca (Año 2070)")
            plot_stress_map(gdf, stress_s1, stress_s2)
            
            st.markdown("---")
            
            # Mostrar composición de la demanda
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
