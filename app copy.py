import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json

# --- Configuración de la Página ---
st.set_page_config(
    page_title="Visualizador Comparativo OWF",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Estilos CSS Personalizados ---
st.markdown("""
<style>
    .stApp { background-color: #f0f4f8; }
    .css-1d391kg { background-color: #ffffff; border-right: 1px solid #e6e6e6; }
    h1, h2, h3 { color: #003366; }
    .stButton>button {
        background-color: #007bff; color: white; border-radius: 0.5rem; border: none;
        padding: 10px 20px; transition: all 0.3s ease;
    }
    .stButton>button:hover { background-color: #0056b3; box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2); }
</style>
""", unsafe_allow_html=True)

# --- DEFINICIÓN DE COLUMNAS (Extraído de visualizer.html) ---
OFERTA_AGUA_COLS = ["To_downstream_from_Casanare_cmd", "To_downstream_from_CravoSur_cmd", "To_downstream_from_Cumaral_cmd", "To_downstream_from_Cusiana_cmd", "To_downstream_from_Dir_btw_ca_or_cmd", "To_downstream_from_Dir_btw_cu_ca_cmd", "To_downstream_from_Dir_btw_cu_cs_cmd", "To_downstream_from_Dir_btw_gb_yu_cmd", "To_downstream_from_Dir_btw_hu_up_cmd", "To_downstream_from_Dir_btw_p_ca_cmd", "To_downstream_from_Garagoa_cmd", "To_downstream_from_Guacavia_cmd", "To_downstream_from_Guanapalo_cmd", "To_downstream_from_Guatiquia_cmd", "To_downstream_from_Guavio_cmd", "To_downstream_from_Guayuriba_cmd", "To_downstream_from_Humea_cmd", "To_downstream_from_Lago_de_tota_cmd", "To_downstream_from_Lengupa_cmd", "To_downstream_from_Manacacias_cmd", "To_downstream_from_Melua_cmd", "To_downstream_from_Metica_cmd", "To_downstream_from_Negro_cmd", "To_downstream_from_Pauto_cmd", "To_downstream_from_Tua_cmd", "To_downstream_from_Upia_cmd", "To_downstream_from_Yucao_cmd"]
DEMANDA_AGUA_COLS = ["Denv_Casanare_cmd", "Denv_CravoSur_cmd", "Denv_Cumaral_cmd", "Denv_Cusiana_cmd", "Denv_Dir_btw_ca_or_cmd", "Denv_Dir_btw_cu_ca_cmd", "Denv_Dir_btw_cu_cs_cmd", "Denv_Dir_btw_gb_yu_cmd", "Denv_Dir_btw_hu_up_cmd", "Denv_Dir_btw_p_ca_cmd", "Denv_Garagoa_cmd", "Denv_Guacavia_cmd", "Denv_Guanapalo_cmd", "Denv_Guatiquia_cmd", "Denv_Guavio_cmd", "Denv_Guayuriba_cmd", "Denv_Humea_cmd", "Denv_Lago_de_tota_cmd", "Denv_Lengupa_cmd", "Denv_Manacacias_cmd", "Denv_Melua_cmd", "Denv_Metica_cmd", "Denv_Negro_cmd", "Denv_Pauto_cmd", "Denv_Tua_cmd", "Denv_Upia_cmd", "Denv_Yucao_cmd","Dfwr_Casanare_cmd", "Dfwr_CravoSur_cmd", "Dfwr_Cumaral_cmd", "Dfwr_Cusiana_cmd", "Dfwr_Dir_btw_ca_or_cmd", "Dfwr_Dir_btw_cu_ca_cmd", "Dfwr_Dir_btw_cu_cs_cmd", "Dfwr_Dir_btw_gb_yu_cmd", "Dfwr_Dir_btw_hu_up_cmd", "Dfwr_Dir_btw_p_ca_cmd", "Dfwr_Garagoa_cmd", "Dfwr_Guacavia_cmd", "Dfwr_Guanapalo_cmd", "Dfwr_Guatiquia_cmd", "Dfwr_Guavio_cmd", "Dfwr_Guayuriba_cmd", "Dfwr_Humea_cmd", "Dfwr_Lago_de_tota_cmd", "Dfwr_Lengupa_cmd", "Dfwr_Manacacias_cmd", "Dfwr_Melua_cmd", "Dfwr_Metica_cmd", "Dfwr_Negro_cmd", "Dfwr_Pauto_cmd", "Dfwr_Tua_cmd", "Dfwr_Upia_cmd", "Dfwr_Yucao_cmd", "Dfwu_Casanare_cmd", "Dfwu_CravoSur_cmd", "Dfwu_Cumaral_cmd", "Dfwu_Cusiana_cmd", "Dfwu_Dir_btw_ca_or_cmd", "Dfwu_Dir_btw_cu_ca_cmd", "Dfwu_Dir_btw_cu_cs_cmd", "Dfwu_Dir_btw_gb_yu_cmd", "Dfwu_Dir_btw_hu_up_cmd", "Dfwu_Dir_btw_p_ca_cmd", "Dfwu_Garagoa_cmd", "Dfwu_Guacavia_cmd", "Dfwu_Guanapalo_cmd", "Dfwu_Guatiquia_cmd", "Dfwu_Guavio_cmd", "Dfwu_Guayuriba_cmd", "Dfwu_Humea_cmd", "Dfwu_Lago_de_tota_cmd", "Dfwu_Lengupa_cmd", "Dfwu_Manacacias_cmd", "Dfwu_Melua_cmd", "Dfwu_Metica_cmd", "Dfwu_Negro_cmd", "Dfwu_Pauto_cmd", "Dfwu_Tua_cmd", "Dfwu_Upia_cmd", "Dfwu_Yucao_cmd", "Dirr_Casanare_cmd", "Dirr_CravoSur_cmd", "Dirr_Cumaral_cmd", "Dirr_Cusiana_cmd", "Dirr_Dir_btw_ca_or_cmd", "Dirr_Dir_btw_cu_ca_cmd", "Dirr_Dir_btw_cu_cs_cmd", "Dirr_Dir_btw_gb_yu_cmd", "Dirr_Dir_btw_hu_up_cmd", "Dirr_Dir_btw_p_ca_cmd", "Dirr_Garagoa_cmd", "Dirr_Guacavia_cmd", "Dirr_Guanapalo_cmd", "Dirr_Guatiquia_cmd", "Dirr_Guavio_cmd", "Dirr_Guayuriba_cmd", "Dirr_Humea_cmd", "Dirr_Lago_de_tota_cmd", "Dirr_Lengupa_cmd", "Dirr_Manacacias_cmd", "Dirr_Melua_cmd", "Dirr_Metica_cmd", "Dirr_Negro_cmd", "Dirr_Pauto_cmd", "Dirr_Tua_cmd", "Dirr_Upia_cmd", "Dirr_Yucao_cmd", "Dliv_Casanare_cmd", "Dliv_CravoSur_cmd", "Dliv_Cumaral_cmd", "Dliv_Cusiana_cmd", "Dliv_Dir_btw_ca_or_cmd", "Dliv_Dir_btw_cu_ca_cmd", "Dliv_Dir_btw_cu_cs_cmd", "Dliv_Dir_btw_gb_yu_cmd", "Dliv_Dir_btw_hu_up_cmd", "Dliv_Dir_btw_p_ca_cmd", "Dliv_Garagoa_cmd", "Dliv_Guacavia_cmd", "Dliv_Guanapalo_cmd", "Dliv_Guatiquia_cmd", "Dliv_Guavio_cmd", "Dliv_Guayuriba_cmd", "Dliv_Humea_cmd", "Dliv_Lago_de_tota_cmd", "Dliv_Lengupa_cmd", "Dliv_Manacacias_cmd", "Dliv_Melua_cmd", "Dliv_Metica_cmd", "Dliv_Negro_cmd", "Dliv_Pauto_cmd", "Dliv_Tua_cmd", "Dliv_Upia_cmd", "Dliv_Yucao_cmd"]
DEMAND_COMPONENTS = {
    'Ambiental': [c for c in DEMANDA_AGUA_COLS if c.startswith('Denv_')],
    'Rural': [c for c in DEMANDA_AGUA_COLS if c.startswith('Dfwr_')],
    'Urbano': [c for c in DEMANDA_AGUA_COLS if c.startswith('Dfwu_')],
    'Irrigación': [c for c in DEMANDA_AGUA_COLS if c.startswith('Dirr_')],
    'Pecuario': [c for c in DEMANDA_AGUA_COLS if c.startswith('Dliv_')]
}

# --- Funciones de Lógica y Datos ---

@st.cache_data
def load_manifest(path="soporte/manifest.json"):
    """Carga el manifiesto de datos desde un archivo JSON."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        st.error(f"Error al cargar '{path}': {e}")
        return None

@st.cache_data
def load_data_from_cloud(scenario_params, data_manifest):
    """Construye la URL y carga los datos del escenario."""
    policy_code = "FCFS" if scenario_params['policy'] == "First Come First Served (FCFS)" else "PE"
    file_name = f"OWF_{policy_code}_{scenario_params['run']}_DT{scenario_params['tempChange']}_DP{100 + scenario_params['precipChange']}_FW{scenario_params['popYear']}_Irr{scenario_params['cropYear']}_Liv{scenario_params['livestockYear']}.csv"
    st.write(f"Buscando en manifiesto: `{file_name}`")

    file_id = data_manifest.get(file_name)
    if not file_id:
        st.warning(f"ID no encontrado para: `{file_name}`.")
        return pd.DataFrame()

    final_url = f'https://docs.google.com/uc?export=download&id={file_id}'
    try:
        with st.spinner(f"Descargando {file_name}..."):
            df = pd.read_csv(final_url)
            df = df.rename(columns={df.columns[0]: 'Date'})
            df['Date'] = pd.to_datetime(df['Date'])
            return df
    except Exception as e:
        st.error(f"Error al descargar/procesar {file_name}: {e}")
        return pd.DataFrame()

# --- Funciones de Procesamiento para Gráficos ---

def get_annual_totals(df, columns):
    """Calcula los totales anuales para un conjunto de columnas."""
    if df.empty: return pd.Series(dtype=float)
    valid_cols = [col for col in columns if col in df.columns]
    df['Total'] = df[valid_cols].sum(axis=1)
    annual_totals = df.set_index('Date').resample('A')['Total'].sum()
    return annual_totals

def prepare_monthly_data(df, columns, scenario_name):
    """Prepara los datos para los gráficos de cajas mensuales."""
    if df.empty: return pd.DataFrame()
    valid_cols = [col for col in columns if col in df.columns]
    df['Total'] = df[valid_cols].sum(axis=1)
    df_monthly = df[['Date', 'Total']].copy()
    df_monthly['Month'] = df_monthly['Date'].dt.strftime('%b')
    df_monthly['Scenario'] = scenario_name
    return df_monthly

def get_annual_composition(df):
    """Calcula la composición porcentual anual de la demanda."""
    if df.empty: return pd.DataFrame()
    totals = {name: df[cols].sum().sum() for name, cols in DEMAND_COMPONENTS.items() if all(c in df.columns for c in cols)}
    total_demand = sum(totals.values())
    if total_demand == 0: return pd.DataFrame()
    percentages = {name: (val / total_demand) * 100 for name, val in totals.items()}
    return pd.DataFrame(list(percentages.items()), columns=['Componente', 'Porcentaje'])

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
    
    generate_button = st.sidebar.button("Generar Comparación", use_container_width=True)
    return s1_params, s2_params, generate_button

def scenario_controls(key_prefix):
    """Crea un conjunto de controles para un escenario."""
    params = {}
    params['policy'] = st.selectbox("Política:", ["First Come First Served (FCFS)", "Policy Enforced (PE)"], key=f"policy_{key_prefix}")
    params['run'] = st.selectbox("Réplica:", ["R1", "R2", "R3", "R4", "R5"], key=f"run_{key_prefix}")
    params['tempChange'] = st.slider("Temp. (°C):", 0, 5, 2, key=f"temp_{key_prefix}")
    params['precipChange'] = st.slider("Precip. (%):", -30, 30, 0, 10, key=f"precip_{key_prefix}")
    params['popYear'] = st.selectbox("Año Pob.:", [2022, 2030, 2040, 2050], index=1, key=f"pop_{key_prefix}")
    params['cropYear'] = st.selectbox("Año Cult.:", [2022, 2030, 2040, 2050], index=0, key=f"crop_{key_prefix}")
    params['livestockYear'] = st.selectbox("Año Pec.:", [2022, 2030, 2040, 2050], index=1, key=f"livestock_{key_prefix}")
    return params

# --- Funciones de Gráficos ---

def plot_line_comparison(s1_data, s2_data, title, yaxis_title):
    """Dibuja un gráfico de líneas comparativo."""
    fig = go.Figure()
    if not s1_data.empty:
        fig.add_trace(go.Scatter(x=s1_data.index.year, y=s1_data.values, mode='lines+markers', name='Escenario 1'))
    if not s2_data.empty:
        fig.add_trace(go.Scatter(x=s2_data.index.year, y=s2_data.values, mode='lines+markers', name='Escenario 2'))
    fig.update_layout(title=title, yaxis_title=yaxis_title, legend_orientation="h", legend_y=1.15)
    st.plotly_chart(fig, use_container_width=True)

def plot_boxplot_comparison(s1_data, s2_data, title, yaxis_title):
    """Dibuja un gráfico de cajas comparativo."""
    combined_df = pd.concat([s1_data, s2_data])
    if combined_df.empty:
        st.warning(f"No hay datos para el gráfico: {title}")
        return
    month_order = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    combined_df['Month'] = pd.Categorical(combined_df['Month'], categories=month_order, ordered=True)
    fig = px.box(combined_df, x='Month', y='Total', color='Scenario', title=title, labels={'Total': yaxis_title})
    fig.update_layout(legend_orientation="h", legend_y=1.15)
    st.plotly_chart(fig, use_container_width=True)

def plot_composition_comparison(s1_data, s2_data):
    """Dibuja un gráfico de barras apiladas para la composición de la demanda."""
    if s1_data.empty and s2_data.empty:
        st.warning("No hay datos para el gráfico de composición de demanda.")
        return
    s1_data['Escenario'] = 'Escenario 1'
    s2_data['Escenario'] = 'Escenario 2'
    combined_df = pd.concat([s1_data, s2_data])
    fig = px.bar(combined_df, x='Escenario', y='Porcentaje', color='Componente', title='Composición Anual Promedio de la Demanda', barmode='stack')
    fig.update_layout(yaxis_title='Porcentaje (%)', xaxis_title=None, legend_title='Componente')
    st.plotly_chart(fig, use_container_width=True)

# --- Aplicación Principal ---

def main():
    st.title("📊 Visualizador Comparativo de Escenarios Hídricos OWF")
    st.markdown("Esta herramienta permite explorar y comparar dos escenarios de recursos hídricos para la cuenca del río Meta.")
    
    data_manifest = load_manifest()
    s1_params, s2_params, generate_button = sidebar_ui()
    
    if generate_button:
        if data_manifest:
            df_s1 = load_data_from_cloud(s1_params, data_manifest)
            df_s2 = load_data_from_cloud(s2_params, data_manifest)
            
            if df_s1.empty or df_s2.empty:
                st.error("No se pudieron cargar datos para uno o ambos escenarios. Verifique la configuración.")
            else:
                # --- Procesamiento de Datos ---
                annual_supply_s1 = get_annual_totals(df_s1, OFERTA_AGUA_COLS)
                annual_supply_s2 = get_annual_totals(df_s2, OFERTA_AGUA_COLS)
                annual_demand_s1 = get_annual_totals(df_s1, DEMANDA_AGUA_COLS)
                annual_demand_s2 = get_annual_totals(df_s2, DEMANDA_AGUA_COLS)
                
                monthly_supply_s1 = prepare_monthly_data(df_s1, OFERTA_AGUA_COLS, 'Escenario 1')
                monthly_supply_s2 = prepare_monthly_data(df_s2, OFERTA_AGUA_COLS, 'Escenario 2')
                monthly_demand_s1 = prepare_monthly_data(df_s1, DEMANDA_AGUA_COLS, 'Escenario 1')
                monthly_demand_s2 = prepare_monthly_data(df_s2, DEMANDA_AGUA_COLS, 'Escenario 2')

                composition_s1 = get_annual_composition(df_s1)
                composition_s2 = get_annual_composition(df_s2)

                # --- Renderizado de Gráficos ---
                st.header("Análisis de Oferta Hídrica")
                col1, col2 = st.columns(2)
                with col1:
                    plot_line_comparison(annual_supply_s1, annual_supply_s2, "Oferta Hídrica Anual Total", "Oferta (cmd)")
                with col2:
                    plot_boxplot_comparison(monthly_supply_s1, monthly_supply_s2, "Distribución Mensual de Oferta Hídrica", "Oferta (cmd)")

                st.header("Análisis de Demanda Hídrica")
                col3, col4 = st.columns(2)
                with col3:
                    plot_line_comparison(annual_demand_s1, annual_demand_s2, "Demanda Hídrica Anual Total", "Demanda (cmd)")
                with col4:
                    plot_boxplot_comparison(monthly_demand_s1, monthly_demand_s2, "Distribución Mensual de Demanda Hídrica", "Demanda (cmd)")

                st.header("Análisis de Composición de la Demanda")
                plot_composition_comparison(composition_s1, composition_s2)

        else:
            st.error("No se puede continuar. Revisa que 'manifest.json' esté cargado correctamente.")
    else:
        st.info("Configure los escenarios en la barra lateral y presione 'Generar Comparación' para ver los resultados.")

if __name__ == "__main__":
    main()
