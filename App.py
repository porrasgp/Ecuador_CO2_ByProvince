import streamlit as st
import pandas as pd
!pip install folium
import folium
from streamlit_folium import folium_static
import math
import re
from folium.plugins import MarkerCluster, HeatMap

# Load the dataset
@st.cache_data
def load_data():
    # Load the Excel file and parse the relevant sheet
    file_path = 'Coordenadas ecuador.xlsx'  # Ensure the file is in the same directory as the app
    data_excel = pd.ExcelFile(file_path)
    data = data_excel.parse('Hoja1')

    # Convert LATITUD and LONGITUD from DMS to decimal
    def dms_to_decimal(dms):
        match = re.match(r"(-?\d+)\u00b0(\d+)[\u2032'](\d+)[\u2033'']?", str(dms))
        if not match:
            return None
        degrees, minutes, seconds = map(float, match.groups())
        decimal = degrees + (minutes / 60) + (seconds / 3600)
        return round(decimal, 6)

    data['LATITUD'] = data['LATITUD'].apply(dms_to_decimal)
    data['LONGITUD'] = data['LONGITUD'].apply(dms_to_decimal)

    return data


# Configuración inicial de la página
st.set_page_config(
    page_title="Geltonas agrotech UAB",
    page_icon="🌍",
    layout="wide"
)

# Cargar datos con caché
@st.cache_data
def load_data():
    data_excel = pd.ExcelFile('Coordenadas ecuador.xlsx')
    data = data_excel.parse('Hoja1')

    def dms_to_decimal(dms):
        match = re.match(r"(-?\d+)\u00b0(\d+)[\u2032'](\d+)[\u2033'']?", str(dms))
        if not match:
            return None
        degrees, minutes, seconds = map(float, match.groups())
        return round(degrees + (minutes / 60) + (seconds / 3600), 6)

    data['LATITUD'] = data['LATITUD'].apply(dms_to_decimal)
    data['LONGITUD'] = data['LONGITUD'].apply(dms_to_decimal)
    
    return data.dropna(subset=['LATITUD', 'LONGITUD'])

data = load_data()

# Sidebar para controles
with st.sidebar:
    st.header("🛠 Configuración del Mapa")
    lat_input = st.number_input("Latitud:", 
                              min_value=-90.0, 
                              max_value=90.0,
                              value=-0.2295,
                              format="%.6f")
    
    lon_input = st.number_input("Longitud:", 
                              min_value=-180.0, 
                              max_value=180.0,
                              value=-78.5249,
                              format="%.6f")
    
    shape_type = st.radio("Tipo de Área:", 
                        ["Cuadrado", "Círculo"],
                        horizontal=True)
    
    size_param = st.slider(
        "Tamaño del área (km):",
        1, 1000, 10,
        help="Radio o lado del área de análisis en kilómetros"
    )
    
    if st.button("🚨 Analizar Riesgo", use_container_width=True):
        st.session_state.analyze = True

# Conversión de km a grados aproximada
def km_to_degrees(km):
    return km / 111.32  # 1 grado ≈ 111.32 km

# Contenedor principal
main_container = st.container()

if 'analyze' in st.session_state:
    with main_container:
        st.subheader(f"🔍 Resultados del Análisis: {shape_type} de {size_param} km")
        
        with st.spinner('Buscando ubicaciones de riesgo...'):
            area_degrees = km_to_degrees(size_param)
            m = folium.Map(location=[lat_input, lon_input], 
                         zoom_start=10, 
                         tiles='cartodbpositron')
            
            # Filtrado de datos
            if shape_type == "Cuadrado":
                square_coords = [
                    (lat_input + area_degrees/2, lon_input - area_degrees/2),
                    (lat_input + area_degrees/2, lon_input + area_degrees/2),
                    (lat_input - area_degrees/2, lon_input + area_degrees/2),
                    (lat_input - area_degrees/2, lon_input - area_degrees/2)
                ]
                
                filtered = data[
                    (data.LATITUD.between(square_coords[3][0], square_coords[0][0])) &
                    (data.LONGITUD.between(square_coords[0][1], square_coords[1][1]))
                ]
                
                folium.Polygon(
                    locations=square_coords,
                    color='#3186cc',
                    weight=2,
                    fill=True,
                    fill_opacity=0.2
                ).add_to(m)
                
            else:  # Círculo
                filtered = data[
                    ((data.LATITUD - lat_input)**2 + 
                    ((data.LONGITUD - lon_input) * 
                     math.cos(math.radians(lat_input)))**2) <= (area_degrees**2)
                ]
                
                folium.Circle(
                    location=(lat_input, lon_input),
                    radius=size_param * 1000,
                    color='#3186cc',
                    weight=2,
                    fill=True,
                    fill_opacity=0.2
                ).add_to(m)
            
            # Capa de calor
            HeatMap(
                data=filtered[['LATITUD', 'LONGITUD']].values,
                radius=20,
                blur=15,
                max_zoom=13
            ).add_to(m)
            
            # Cluster de marcadores
            marker_cluster = MarkerCluster().add_to(m)
            for _, row in filtered.iterrows():
                folium.Marker(
                    location=[row['LATITUD'], row['LONGITUD']],
                    popup=folium.Popup(
                        f"""
                        <b>Provincia:</b> {row['Provincia']}<br>
                        <b>Nivel Riesgo:</b> <span style="color:red">{row['Riesgo']}</span><br>
                        <b>CO2:</b> {row['CO2 TONELADAS']:,.1f} tons
                        """,
                        max_width=250
                    ),
                    icon=folium.Icon(color='red', icon='exclamation-triangle', prefix='fa')
                ).add_to(marker_cluster)
            
            # Controles del mapa
            folium.plugins.Fullscreen().add_to(m)
            folium.plugins.MousePosition().add_to(m)
            
            # Mostrar mapa
            col1, col2 = st.columns([3, 1])
            with col1:
                folium_static(m, height=600)
            
            with col2:
                st.metric("📍 Ubicaciones Detectadas", len(filtered))
                st.metric("☁️ Emisiones Totales CO2", 
                        f"{filtered['CO2 TONELADAS'].sum():,.0f} tons")
                
                st.download_button(
                    label="📥 Exportar Datos",
                    data=filtered.to_csv(index=False).encode('utf-8'),
                    file_name='datos_riesgo.csv',
                    mime='text/csv',
                    use_container_width=True
                )
                
                if not filtered.empty:
                    st.write("**Top 5 Ubicaciones con Mayor Riesgo:**")
                    st.dataframe(
                        filtered.sort_values('Riesgo', ascending=False)
                        .head(5)[['Provincia', 'Riesgo', 'CO2 TONELADAS']],
                        hide_index=True
                    )
else:
    with main_container:
        st.info("ℹ️ Ingrese los parámetros en el panel lateral y haga clic en 'Analizar Riesgo'")

# Estilos CSS personalizados
st.markdown("""
<style>
    .stNumberInput input {border: 1px solid #4a4a4a;}
    .stButton>button {background-color: #ff4b4b; transition: all 0.3s;}
    .stButton>button:hover {background-color: #ff2b2b; transform: scale(1.05);}
    .stMetric {border: 1px solid #4a4a4a; border-radius: 10px; padding: 15px;}
    .stAlert {border-radius: 10px;}
</style>
""", unsafe_allow_html=True)
