# Importation des bibliothèques nécessaires
import streamlit as st  # Pour créer l'interface utilisateur
import pandas as pd  # Pour manipuler les données
import folium  # Pour créer des cartes interactives
from streamlit_folium import folium_static  # Pour afficher les cartes Folium dans Streamlit
from geopy.geocoders import Nominatim  # Pour géocoder des adresses (transformer une adresse en coordonnées)
from geopy.distance import geodesic  # Pour calculer des distances géographiques
import numpy as np  # Pour des calculs numériques
from scipy.spatial import Voronoi  # Pour générer des diagrammes de Voronoï
from shapely.geometry import Point, Polygon  # Pour manipuler des formes géométriques
from streamlit.components.v1 import html  # Pour intégrer du HTML personnalisé

# Configuration de la page Streamlit
st.set_page_config(
    page_title="Toilettes en Île-de-France",  # Titre de la page
    page_icon="🚽",  # Icône de la page
    layout="wide",  # Utiliser toute la largeur de la page
    initial_sidebar_state="collapsed"  # Réduire la barre latérale par défaut
)

# Ajout de styles CSS personnalisés pour une interface utilisateur moderne
st.markdown("""
<style>
    /* Fond sombre pour l'application */
    .stApp {
        background-color: #1a1a1a;
        color: white;
    }
    /* Conteneurs en verre avec effet de flou */
    .glass-container {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 1rem;
        padding: 1.5rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: all 0.3s ease;
    }
    .glass-container:hover {
        background: rgba(255, 255, 255, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    /* Cartes de métriques */
    .metric-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 1rem;
        padding: 1.5rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        background: rgba(255, 255, 255, 0.15);
        transform: translateY(-2px);
    }
    /* Titres des métriques */
    .metric-title {
        color: rgba(255, 255, 255, 0.7);
        font-size: 0.875rem;
        margin-bottom: 0.5rem;
    }
    /* Valeurs des métriques */
    .metric-value {
        color: white;
        font-size: 2rem;
        font-weight: bold;
    }
    /* Styles pour les boutons */
    .stButton>button {
        background: rgba(59, 130, 246, 0.8);
        color: white;
        border: none;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: rgba(59, 130, 246, 1);
        transform: translateY(-2px);
    }
    /* Styles pour les champs de texte */
    .stTextInput>div>div>input {
        background: rgba(255, 255, 255, 0.1);
        color: white;
        border: 1px solid rgba(59, 130, 246, 0.5);
        border-radius: 0.5rem;
        transition: all 0.3s ease;
    }
    .stTextInput>div>div>input:focus {
        border-color: rgba(59, 130, 246, 1);
        background: rgba(255, 255, 255, 0.15);
    }
    /* Styles pour les sélecteurs et multi-sélecteurs */
    .stSelectbox>div>div, .stMultiSelect>div>div {
        background: rgba(255, 255, 255, 0.1);
        color: white;
        border: 1px solid rgba(59, 130, 246, 0.5);
        border-radius: 0.5rem;
        transition: all 0.3s ease;
    }
    .stSelectbox>div>div:hover, .stMultiSelect>div>div:hover {
        border-color: rgba(59, 130, 246, 1);
        background: rgba(255, 255, 255, 0.15);
    }
    /* Styles pour les onglets */
    .stTabs>div>div>div>div {
        background: rgba(255, 255, 255, 0.1);
        color: white;
    }
    /* Styles pour les sections de contenu */
    .content-section {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 1rem;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# Fonction pour charger les données des toilettes depuis un fichier CSV
@st.cache_data  # Mise en cache pour éviter de recharger les données à chaque interaction
def load_data():
    df = pd.read_csv('data_toilette.csv')  # Chargement du fichier CSV
    df['coordinates'] = df['coordinates'].str.strip('[]')  # Nettoyage des coordonnées
    df[['latitude', 'longitude']] = df['coordinates'].str.split(',', expand=True).astype(float)  # Séparation en latitude et longitude
    return df

# Fonction pour créer une carte avec un diagramme de Voronoï
def create_voronoi_map(df):
    coordinates = df[['latitude', 'longitude']].to_numpy()  # Extraction des coordonnées
    
    if len(coordinates) < 3:
        st.error("Le diagramme de Voronoï nécessite au moins 3 points.")  # Message d'erreur si moins de 3 points
        return None
        
    vor = Voronoi(coordinates)  # Génération du diagramme de Voronoï
    
    # Création de la carte centrée sur la moyenne des coordonnées
    m = folium.Map(
        location=[df['latitude'].mean(), df['longitude'].mean()],
        zoom_start=12,
        tiles='OpenStreetMap'
    )
    
    # Ajout des toilettes existantes sur la carte
    for _, row in df.iterrows():
        folium.CircleMarker(
            [row['latitude'], row['longitude']],
            radius=6,
            color='#3b82f6',
            fill=True,
            popup="Toilette existante"
        ).add_to(m)
    
    # Conversion des polygones de Voronoï en formes géométriques
    def voronoi_to_polygons(vor, coordinates):
        polygons = []
        for region_idx in vor.point_region:
            region = vor.regions[region_idx]
            if -1 not in region and region:  # Éviter les régions infinies
                vertices = [vor.vertices[i] for i in region]
                polygons.append(Polygon(vertices))
        return polygons
    
    try:
        polygons = voronoi_to_polygons(vor, coordinates)  # Obtention des polygones
        
        # Identification des centres des zones vides
        empty_zone_centers = []
        for poly in polygons:
            if poly.is_valid and not any(Point(lon, lat).within(poly) for lat, lon in coordinates):
                centroid = poly.centroid.coords[0]
                empty_zone_centers.append(centroid)
        
        # Ajout des propositions d'installation sur la carte
        for lat, lon in empty_zone_centers:
            folium.CircleMarker(
                location=[lat, lon],
                radius=8,
                color='#22c55e',
                fill=True,
                popup="Proposition d'installation",
                fill_opacity=0.7
            ).add_to(m)
            
    except Exception as e:
        st.warning(f"Erreur lors de la création des polygones Voronoï: {str(e)}")  # Gestion des erreurs
    
    return m

# Fonction pour créer une carte interactive avec la position de l'utilisateur et les toilettes
def create_map(user_lat, user_lon, toilets_df):
    m = folium.Map(
        location=[user_lat, user_lon],
        zoom_start=14,
        tiles='OpenStreetMap'
    )
    
    # Ajout d'un marqueur pour la position de l'utilisateur
    folium.Marker(
        [user_lat, user_lon],
        icon=folium.Icon(icon='info-sign', color='blue'),
        popup='Votre position'
    ).add_to(m)
    
    # Ajout des marqueurs pour les toilettes
    for _, toilet in toilets_df.iterrows():
        color = 'green' if toilet['tarif'] == 'Gratuit' else 'red'  # Couleur en fonction du tarif
        
        # Popup HTML pour afficher les détails de la toilette
        popup_html = f"""
        <div style="font-family: system-ui; color: white; background-color: #1e293b; padding: 1rem; border-radius: 0.5rem; min-width: 200px;">
            <div style="font-weight: bold; margin-bottom: 0.5rem;">
                {toilet['distance']:.0f}m
            </div>
            <div style="color: {color}; margin-bottom: 0.5rem;">
                {toilet['tarif']}
            </div>
            <div style="margin-bottom: 0.25rem;">
                ♿️ {toilet['accessibilite_pmr']}
            </div>
            <div style="margin-bottom: 0.25rem;">
                👶 {toilet['relais_bebe']}
            </div>
            <div style="color: #94a3b8; font-size: 0.875rem;">
                {toilet['horaires'] if toilet['horaires'] != "pas d'info" else 'Horaires non disponibles'}
            </div>
        </div>
        """
        
        folium.Marker(
            [toilet['latitude'], toilet['longitude']],
            icon=folium.Icon(icon='info-sign', color=color),
            popup=folium.Popup(popup_html, max_width=300)
        ).add_to(m)
    
    return m

# Fonction pour géocoder une adresse (transformer une adresse en coordonnées)
def geocode_address(address):
    try:
        geolocator = Nominatim(user_agent="toilet_finder")
        location = geolocator.geocode(address)
        if location:
            return location.latitude, location.longitude
        return None
    except:
        return None

# Fonction pour trouver les toilettes les plus proches de l'utilisateur
def get_nearest_toilets(user_lat, user_lon, df, max_distance=1000):
    distances = []
    user_location = (user_lat, user_lon)
    
    for _, row in df.iterrows():
        toilet_location = (row['latitude'], row['longitude'])
        distance = geodesic(user_location, toilet_location).meters
        distances.append(distance)
    
    df['distance'] = distances
    return df[df['distance'] <= max_distance].sort_values('distance')

# Fonction pour créer une carte de statistiques
def create_stats_card(title, value, icon, color):
    return f"""
    <div class="metric-card">
        <div class="metric-title">{title}</div>
        <div class="metric-value">
            <span style="color: {color}">{icon}</span> {value}
        </div>
    </div>
    """

# Fonction principale pour l'application
def main():
    st.title("🚽 Courage, les toilettes sont plus proches que tu ne le penses!")
    
    # Chargement des données
    df = load_data()
    
    # Création des onglets
    tab1, tab2 = st.tabs(["🔍 Recherche de toilettes", "🗺️ Cartographie des potentiel d'installation"])
    
    with tab1:
        # Affichage des métriques principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(create_stats_card(
                "Total des toilettes",
                len(df),
                "🚽",
                "#3b82f6"
            ), unsafe_allow_html=True)
        
        with col2:
            free_count = len(df[df['tarif'] == 'Gratuit'])
            st.markdown(create_stats_card(
                "Toilettes gratuites",
                free_count,
                "💶",
                "#22c55e"
            ), unsafe_allow_html=True)
        
        with col3:
            accessible_count = len(df[df['accessibilite_pmr'] == 'Oui'])
            st.markdown(create_stats_card(
                "Accessibles PMR",
                accessible_count,
                "♿️",
                "#f97316"
            ), unsafe_allow_html=True)
        
        with col4:
            baby_count = len(df[df['relais_bebe'] == 'Oui'])
            st.markdown(create_stats_card(
                "Relais bébé",
                baby_count,
                "👶",
                "#8b5cf6"
            ), unsafe_allow_html=True)
        
        # Recherche et filtres
        st.markdown("### 🔍 Recherche")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            address = st.text_input("Votre adresse:", "Tour Eiffel, Paris")
        
        with col2:
            max_distance = st.select_slider(
                "Distance max:",
                options=[500, 750, 1000, 1500, 2000],
                value=1000,
                format_func=lambda x: f"{x}m"
            )
        
        with col3:
            tarif_filter = st.multiselect(
                "Tarif:",
                options=['Tous'] + list(df['tarif'].unique()),
                default='Tous'
            )
        
        with col4:
            pmr_filter = st.multiselect(
                "Accessibilité PMR:",
                options=['Tous'] + list(df['accessibilite_pmr'].unique()),
                default='Tous'
            )
        
        with col5:
            baby_filter = st.multiselect(
                "Relais bébé:",
                options=['Tous'] + list(df['relais_bebe'].unique()),
                default='Tous'
            )
        
        if st.button("🔍 Rechercher"):
            location = geocode_address(address)
            
            if location:
                user_lat, user_lon = location
                
                filtered_df = df.copy()
                if 'Tous' not in tarif_filter:
                    filtered_df = filtered_df[filtered_df['tarif'].isin(tarif_filter)]
                if 'Tous' not in pmr_filter:
                    filtered_df = filtered_df[filtered_df['accessibilite_pmr'].isin(pmr_filter)]
                if 'Tous' not in baby_filter:
                    filtered_df = filtered_df[filtered_df['relais_bebe'].isin(baby_filter)]
                
                nearest_toilets = get_nearest_toilets(user_lat, user_lon, filtered_df, max_distance)
                
                if len(nearest_toilets) > 0:
                    st.markdown(f"### 📍 {len(nearest_toilets)} toilettes trouvées")
                    m = create_map(user_lat, user_lon, nearest_toilets)
                    folium_static(m, width=1300, height=600)
                    
                    st.markdown("### 📋 Liste des toilettes")
                    for _, toilet in nearest_toilets.iterrows():
                        with st.expander(f"{toilet['distance']:.0f}m - {toilet['type']}"):
                            st.markdown(f"""
                            - 💶 **Tarif:** {toilet['tarif']}
                            - ♿️ **Accessibilité PMR:** {toilet['accessibilite_pmr']}
                            - 👶 **Relais bébé:** {toilet['relais_bebe']}
                            - 🕒 **Horaires:** {toilet['horaires']}
                            - 📍 **Localisation:** {toilet['indications_localisation']}
                            """)
                else:
                    st.warning("Aucune toilette trouvée dans le rayon spécifié")
            else:
                st.error("Impossible de trouver les coordonnées de l'adresse indiquée")
    
    with tab2:
        st.header("📍 Cartographie des potentiel d'installation")
        st.write("Cette carte montre les emplacements existants (en bleu) et les propositions d'installation (en rouge) basées sur l'analyse Voronoï.")
        
        voronoi_map = create_voronoi_map(df)
        if voronoi_map:
            folium_static(voronoi_map, width=1300, height=600 )
            st.info("""
            Les points rouges indiquent les zones où l'installation de nouvelles toilettes pourrait être bénéfique, 
            basé sur l'analyse de la distribution spatiale des toilettes existantes.
            """)

# Point d'entrée de l'application
if __name__ == "__main__":
    main()