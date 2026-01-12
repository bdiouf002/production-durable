import pandas as pd
import streamlit as st
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
#Pour faire le style
st.markdown(
    
    """
    <style>
    /* Fond de l'application en Vert Foncé */
    .stApp {
        background-color: #1b5e20;
    }

    /* Style des titres pour qu'ils soient visibles sur le vert foncé */
    h1, h2, h3, p, span, label {
        color: #ffffff !important;
    }

    /* Panneaux des onglets : on garde un fond blanc/clair pour les graphiques */
    [data-baseweb="tab-panel"] {
        background-color: #ffffff;
        padding: 30px;
        border-radius: 15px;
        box-shadow: 0px 10px 25px rgba(0, 0, 0, 0.3);
    }
    
    /* Adaptation des textes à l'intérieur des onglets blancs */
    [data-baseweb="tab-panel"] p, 
    [data-baseweb="tab-panel"] h1, 
    [data-baseweb="tab-panel"] h2, 
    [data-baseweb="tab-panel"] h3,
    [data-baseweb="tab-panel"] span {
        color: #1b5e20 !important;
    }

    /* Style des onglets eux-mêmes (en haut) */
    button[data-baseweb="tab"] {
        color: #ffffff !important;
        font-weight: bold;
    }
    
    button[aria-selected="true"] {
        background-color: rgba(255, 255, 255, 0.2) !important;
        border-radius: 10px 10px 0 0;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- En-tête avec Titre et Logo ---
st.set_page_config(layout="wide")
col_title, col_logo = st.columns([4, 1])
#titre
st.title("🌱Production Durable")
st.markdown("Analyse de la production durable dans différents secteurs")

#Création du logo
with col_logo :
    try:
        st.image("logo.jpg", width=200) 
    except:
        st.write("Logo ici 🖼️") # Message de secours si l'image manque

# Pour charger les données
file_path = "Données.xlsx"


# --- 2. Fonctions de Nettoyage (Centralisées) ---


def clean_numeric_mix(value):
    """Convertit la valeur en pourcentage numérique. Gère les chaînes comme '<1'."""
    if pd.isna(value): return 0.0
    value_str = str(value).strip().lower()
    if '<1' in value_str or 'faible' in value_str: return 0.5
    try: return float(value_str.replace(',', '.'))
    except: return 0.0


def clean_emissions_range_avg(value):
    """Calcule la moyenne d'une plage de valeurs ou nettoie le format."""
    if isinstance(value, str):
        cleaned_value = value.replace('–', '-').replace(',', '.')
        parts = cleaned_value.split('-')
        try:
            if len(parts) == 2:
                low = float(parts[0].strip())
                high = float(parts[1].strip())
                return (low + high) / 2
            if '<' in parts[0]:
                return float(parts[0].replace('<', '').strip()) / 2
            return float(parts[0].strip())
        except: return np.nan
    try: return float(value)
    except: return np.nan


# --- 1.2 Chargement et Préparation des Données (Fonction Cache) ---


@st.cache_data
def load_and_prepare_data(file_path):
    
    # Initialisation
    df_raw_eu, df_ciment, df_electro_agg, df_electro_detail, df_electro_size_power, df_impact_numerique, df_v_plot, df_v2_plot = None, None, None, None, None, None, None, None
    
    # Création du DataFrame de substitution pour Electroniques3
    data_substitute = {
        'Taille_Ecran_Pouces': [20, 25, 30, 35, 40, 45, 50, 55, 60],
        'Puissance_W': [18, 24, 30, 42, 60, 70, 85, 100, 145]
    }
    df_electro_size_power_sub = pd.DataFrame(data_substitute) 
    
    # --- DONNÉES DU NOUVEAU GRAPHIQUE (Impact Numérique - Extraction des images) ---
    # Ces données sont utilisées si la feuille 'Electronique4' est introuvable
    data_impact_numerique = {
        'Indicateur': [
            'Empreinte carbone',
            'Ressources utilisées*',
            'Consommation d\'énergie finale',
            'Consommation de métaux et minéraux'
        ],
        '2020': [0, 0, 0, 0],
        '2030': [45, 38, 79/4, 59/4], # Estimation basée sur le graphique
        '2050': [187, 179, 79, 59]
    }
    df_impact_numerique_sub = pd.DataFrame(data_impact_numerique).set_index('Indicateur')
    
    
    try:
        # Tente de charger toutes les feuilles
        df_raw_eu = pd.read_excel(file_path, sheet_name="Electricite", skiprows=1, header=None)
        df_ciment = pd.read_excel(file_path, sheet_name="Ciment")
        df_electro_agg = pd.read_excel(file_path, sheet_name="Electroniques")
        df_electro_detail = pd.read_excel(file_path, sheet_name="Electroniques2")
        df_electro_size_power = pd.read_excel(file_path, sheet_name="Electroniques3")
        df_v_plot = pd.read_excel(file_path, sheet_name="Vehicules")
        df_tex_habill = pd.read_excel(file_path, sheet_name="textile et habillement")
        df_v2_plot = pd.read_excel(file_path, sheet_name="Vehicules2")


    # --- PRÉPARATION VÉHICULES ---
        
            # Nettoyage : suppression des lignes vides sur les colonnes clés
        df_v_plot = df_v_plot.dropna(subset=['Mode de propulsion', 'Émissions totales (g équiv. CO2/km)'])
      # --- PRÉPARATION textile et habillement ---    
    # On définit la première colonne comme index (Fibre textile)
        df_tex_habill = df_tex_habill.set_index(df_tex_habill.columns[0])
    
    # Nettoyage des plages de valeurs (ex: "2,1 - 3,6" -> 2.85)
        for col in df_tex_habill.columns:
            df_tex_habill[col] = df_tex_habill[col].apply(clean_emissions_range_avg)
    
        
        
    except Exception as e:
        # Gestion des erreurs de chargement initial
        if "Electroniques3" in str(e):
             st.warning("La feuille 'Electroniques3' n'a pas été trouvée. Utilisation de données substituts pour le nuage de points.")
             df_electro_size_power = df_electro_size_power_sub
        else:
             st.error(f"Erreur lors du chargement des données. Détail: {e}")
             return None*9
    
    
    # --- Préparation Électricité ---
    expected_names = ['Technologie', 'PRG_UE_str', 'PRG_MONDE_str', 'FR_Mix', 'DE_Mix', 'CH_Mix', 'IT_Mix', 'G_Source']
    try:
        df_raw_eu.columns = expected_names + list(df_raw_eu.columns[len(expected_names):])
    except ValueError:
        st.error("Erreur de colonnes dans la feuille EU. Veuillez vérifier la structure.")
        return None, None, None, None, None, None
        
    df_eu = df_raw_eu.dropna(subset=['Technologie']).copy()
    df_eu = df_eu[~df_eu['Technologie'].isin(['...', 'Total (Facteur émission du Mix Final)'])]
    df_eu = df_eu.reset_index(drop=True)
    df_eu = df_eu.drop(columns=['G_Source'], errors='ignore')
    df_eu = df_eu.set_index('Technologie')


    mix_cols = ['FR_Mix', 'DE_Mix', 'CH_Mix', 'IT_Mix']
    for col in mix_cols:
        df_eu[col] = df_eu[col].apply(clean_numeric_mix)
    df_eu['PRG_Num_UE'] = df_eu['PRG_UE_str'].apply(clean_emissions_range_avg)
    
    # On nettoie pour ne garder que les lignes de données (CEM I, II, III)
    # et on exclut la ligne "Source Officielle" pour le graphique
    df_ciment = df_ciment[df_ciment.iloc[:, 0].str.contains("CEM", na=False)]
    df_ciment = df_ciment.set_index(df_ciment.columns[0])
        
    # --- Préparation Electroniques AGRÉGÉES  ---
    if df_electro_agg is not None:
        df_electro_agg = df_electro_agg.copy()
        electro_column_mapping = {
            'Catégorie': 'Categorie',
            'Part des Terminaux (%)': 'Part_Terminaux',
            'Part de l\'Empreinte Carbone (%)': 'Part_Empreinte_Carbone'
        }
        df_electro_agg = df_electro_agg.rename(columns=electro_column_mapping, errors='ignore')


        required_cols = ['Categorie', 'Part_Terminaux', 'Part_Empreinte_Carbone']
        
        if all(col in df_electro_agg.columns for col in required_cols):
            for col in ['Part_Terminaux', 'Part_Empreinte_Carbone']:
                df_electro_agg[f'{col}_Num'] = df_electro_agg[col].apply(clean_numeric_mix)
            df_electro_agg = df_electro_agg.dropna(subset=['Categorie']).set_index('Categorie')
        else:
            df_electro_agg = None
            
    # --- Préparation Electroniques DÉTAILLÉES  ---
    if df_electro_detail is not None:
        df_electro_detail = df_electro_detail.copy()
        detail_column_mapping = {
            'Catégorie': 'Categorie',
            'Part de l\'Empreinte Carbone (%)': 'Part_Empreinte_Carbone'
        }
        df_electro_detail = df_electro_detail.rename(columns=detail_column_mapping, errors='ignore')


        required_cols_detail = ['Categorie', 'Part_Empreinte_Carbone']
        
        if all(col in df_electro_detail.columns for col in required_cols_detail):
            df_electro_detail['Part_Empreinte_Carbone_Num'] = df_electro_detail['Part_Empreinte_Carbone'].apply(clean_numeric_mix)
            df_electro_detail = df_electro_detail.dropna(subset=['Categorie']).set_index('Categorie')
        else:
            df_electro_detail = None
            
    # --- PRÉPARATION DU NUAGE DE POINTS  ---
    if df_electro_size_power is not None and df_electro_size_power is not df_electro_size_power_sub:
        size_power_mapping = {
             'Taille d\'écran (pouces)': 'Taille_Ecran_Pouces',
             'Puissance Utilisée (W)': 'Puissance_W'
        }
        df_electro_size_power = df_electro_size_power.rename(columns=size_power_mapping, errors='ignore')
        
        required_cols_sp = ['Taille_Ecran_Pouces', 'Puissance_W']


        if all(col in df_electro_size_power.columns for col in required_cols_sp):
             df_electro_size_power['Taille_Ecran_Pouces'] = pd.to_numeric(df_electro_size_power['Taille_Ecran_Pouces'], errors='coerce')
             df_electro_size_power['Puissance_W'] = pd.to_numeric(df_electro_size_power['Puissance_W'], errors='coerce')
             df_electro_size_power = df_electro_size_power.dropna(subset=required_cols_sp)
        else:
            df_electro_size_power = df_electro_size_power_sub
            
    elif df_electro_size_power is None:
        df_electro_size_power = df_electro_size_power_sub
        
    # --- Assigner df_impact_numerique à la version substitut si le chargement a échoué ---
    if df_impact_numerique is None:
         df_impact_numerique = df_impact_numerique_sub




    if df_eu is None:
        st.stop()


    # Le retour de la fonction inclut maintenant df_impact_numerique
   
    return df_eu, df_ciment, df_electro_agg, df_electro_detail, df_electro_size_power, df_impact_numerique, df_v_plot, df_tex_habill, df_v2_plot

# Lancement du chargement
df_eu, df_ciment, df_electro_agg, df_electro_detail, df_electro_size_power, df_impact_numerique, df_v_plot, df_tex_habill, df_v2_plot = load_and_prepare_data(file_path)


if df_eu is None:
    st.stop()


# --- 2. Définition des Onglets (Reste inchangé) ---
tab_elec, tab_ciment, tabs_electro = st.tabs([
    "Secteur de l'Énergie & transport",
    "🧱 Secteur de la Construction & matériaux ",
    "Secteur industriel"
])
# -----------------------------------------------------------
# Contenu du Premier Onglet : Analyse Électrique
# -----------------------------------------------------------

with tab_elec :
    st.header("⚡️ Analyse Électrique (Mix & PRG)")

    st.header("Empreinte carbone selon les sources de production d’électricité dans UE")
    
    df_prg_chart = df_eu[['PRG_Num_UE']].sort_values(by='PRG_Num_UE', ascending=False)
    st.bar_chart(df_prg_chart)
    st.caption("Source : (Ecoinvent / GaBi), Wikipédia")
    st.info("**Analyse :** l’électricité produite à partir du charbon est celle qui génère le plus d’émissions de CO₂, suivie par le gaz naturel. À l’inverse, l’électricité d’origine nucléaire présente une empreinte carbone plus faible et peut être considérée comme une source à faible intensité carbone.")
    
    st.markdown("---")
    st.header(" Contribution au Mix Final dans differents pays en 2023")
    mix_options = {'🇫🇷 France (FR)': 'FR_Mix', '🇩🇪 Allemagne (DE)': 'DE_Mix', '🇨🇭 Suisse (CH)': 'CH_Mix', '🇮🇹 Italie (IT)': 'IT_Mix'}
    col1, col2 = st.columns([1, 2])
    mix_selection_label = col1.selectbox('**Sélectionnez le Pays à Analyser**', options=list(mix_options.keys()), key='elec_mix_selector')
    mix_column = mix_options[mix_selection_label]
    prg_pour_calcul = df_eu['PRG_Num_UE']
    proportion_mix = df_eu[mix_column] / 100
    empreinte_moyenne = (prg_pour_calcul * proportion_mix).sum()
    col2.metric(label=f"Empreinte Carbone Moyenne du Mix Électrique : {mix_selection_label}", value=f"{empreinte_moyenne:.2f} g eqCO₂/kWh", delta="Indicateur de Durabilité")
    df_pie = df_eu[[mix_column]].reset_index()
    df_pie.columns = ['Technologie', 'Part']
    fig = px.pie(df_pie, values='Part', names='Technologie', title=f'Répartition du Mix Électrique : {mix_selection_label}', hover_data=['Part'], labels={'Part':'Part (%)'})
    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Source : ADEM,..")
    st.info("**Analyse :** Dans le cas de la Suisse, on observe que l’hydroélectricité domine largement le mix électrique avec 56,3 de pourcentage, suivie du nucléaire à hauteur de 32,2 de pourcentage.")


    st.markdown("---")
    st.header("Empreinte carbone des types de voitures🚗")
    if df_v_plot is not None:
        fig_vehicule = px.bar(
            df_v_plot,
            x='Mode de propulsion',
            y='Émissions totales (g équiv. CO2/km)',
            color='Mode de propulsion',
            text='Émissions totales (g équiv. CO2/km)',
            title="Émissions de CO2e par kilomètre selon le mode de propulsion",
            labels={'Émissions totales (g équiv. CO2/km)': 'g CO2e/km'},
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_vehicule.update_traces(texttemplate='%{text} g', textposition='outside')
        st.plotly_chart(fig_vehicule, use_container_width=True)
    else:
        st.error("Les données des véhicules n'ont pas pu être chargées.")
    st.caption("Source : Mobilservice(Swiss eMobility)")
    st.info("**Analyse :** les voitures à essence sont celles qui génèrent le plus d’émissions de CO₂, avec environ 264 g, suivies des voitures diesel à hauteur de 243 g. À l’inverse, les voitures électriques présentent l’empreinte carbone la plus faible.")


    st.markdown("---")
    st.header("📊 Nouvelles immatriculations (Suisse & Liechtenstein)")

    if df_v2_plot is not None:
        # Transformation des données pour Plotly
        df_melted_v2 = df_v2_plot.melt(
            id_vars='Année', 
            var_name='Motorisation', 
            value_name='Part de marché (%)'
        )

        # Création du graphique
        fig_v2 = px.bar(
            df_melted_v2,
            x='Année',
            y='Part de marché (%)',
            color='Motorisation',
            barmode='group',
            title='Évolution des immatriculations par type de motorisation',
            color_discrete_map={
                'Essence': '#ef553b',
                'Diesel': '#f4a582',
                'BEV (électrique)': '#1f77b4',
                'PHEV (hybride rechargeable)': '#46bac2'
            }
        )
        
        fig_v2.update_layout(xaxis=dict(tickmode='linear'), hovermode="x unified")
        st.plotly_chart(fig_v2, use_container_width=True)
    else:
        st.error("Données 'Vehicules2' manquantes.")
    st.caption("Source : Mobilservice(Swiss eMobility)")    
    st.info("**Analyse :** le recul des motorisations essence et diesel, parallèlement à la montée des véhicules électriques (BEV) et hybrides rechargeables (PHEV), traduisant une orientation progressive de la Suisse vers des modes de production et de mobilité plus durables. ")

    try:
        st.image("image1.png", use_container_width=True)
    except FileNotFoundError:
        st.error("L'image locale est introuvable. Vérifiez le chemin : images/votre_image_locale.png")
    try:
        st.image("image2.png", use_container_width=True)
    except FileNotFoundError:
        st.error("L'image locale est introuvable. Vérifiez le chemin : images/votre_image_locale.png")
    try:
        st.image("image3.png", caption="Source : Mobilservice(Swiss eMobility)", use_container_width=True)
    except FileNotFoundError:
        st.error("L'image locale est introuvable. Vérifiez le chemin : images/votre_image_locale.png")

# -----------------------------------------------------------
# Contenu du Deuxième Onglet : Analyse Ciment 
# -----------------------------------------------------------


with tab_ciment:
    st.header("🧱 Comparatif International par Type de Ciment")
    if df_ciment is not None:
        # 1. Nettoyage : On ne garde que les lignes CEM et on enlève la ligne "Source Officielle"
        df_clean = df_ciment.loc[['CEM I (Portland)', 'CEM II (Moyen)', 'CEM III (Bas Carbone)']]
        
        # 2. Pivotement : On transpose pour avoir les Pays sur l'axe X
        # .T transforme les colonnes (Pays) en lignes
        df_t = df_clean.T.reset_index()
        df_t.columns = ['Pays', 'CEM I', 'CEM II', 'CEM III']

        # 3. Transformation pour Plotly (format long)
        df_plot = df_t.melt(id_vars='Pays', var_name='Type de Ciment', value_name='kg CO2/t')

        # 4. Création du graphique avec Pays sur l'axe X
        fig_pays = px.bar(
            df_plot,
            x='Pays', 
            y='kg CO2/t',
            color='Type de Ciment',
            barmode='group',
            title="Comparaison de l'empreinte carbone par pays et par type de ciment",
            color_discrete_sequence=px.colors.qualitative.Antique
        )

        st.plotly_chart(fig_pays, use_container_width=True)
        st.info("**Analyse :** le ciment CEM I (Portland) est celui qui génère le plus d’émissions de CO₂ dans l’ensemble des pays étudiés, bien que son niveau varie d’un pays à l’autre. Il est notamment plus faible en Suisse, avec environ 765 kg CO₂e par tonne, et plus élevé en Italie. Le ciment CEM II présente une empreinte carbone intermédiaire, inférieure à celle du CEM I dans certains pays, mais restant néanmoins significative. À l’inverse, le CEM III affiche l’empreinte carbone la plus faible, ce qui en fait une alternative plus favorable d’un point de vue environnemental.")
        # Affichage des sources pour valider la fiabilité
        st.markdown("### 🔍 Détails des sources et fiabilité")
        st.write("Les données proviennent des inventaires nationaux certifiés :")
        st.info("- **France** : 860 kg (CEM I) via **Base INIES**")
        st.info("- **Suisse** : 765 kg (CEM I) via **cimentsuisse**")
        st.info("- **Allemagne** : Données via **Ökobaudat**")
# -----------------------------------------------------------
# Contenu du Troisième Onglet : Secteur Industriel (Numérique)
# -----------------------------------------------------------


with tabs_electro:
     # --- GRAPHIQUE 1 :
    st.markdown("---")
    st.header("🧵 Impact Environnemental du Textile et de l'Habillement")
    
    if df_tex_habill is not None:
        # On transpose pour avoir les Pays sur l'axe X
        df_tex_habill_t = df_tex_habill.T.reset_index()
        df_tex_habill_t.columns = ['Pays'] + list(df_tex_habill.index)
        
        # Transformation pour Plotly
        df_tex_habill = df_tex_habill_t.melt(id_vars='Pays', var_name='Fibre', value_name='kg CO2e/kg')
        
        fig_textile = px.bar(
            df_tex_habill,
            x='Pays',
            y='kg CO2e/kg',
            color='Fibre',
            barmode='group',
            title="Empreinte carbone par type de fibre textile et par pays",
            labels={'kg CO2e/kg': 'Émissions (kg CO2e par kg de fibre)'},
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        
        st.plotly_chart(fig_textile, use_container_width=True)
        st.caption("Source : ADEME – Base IMPACTS, Ecoinvent, Product Environmental Footprint (PEF)") 
        st.info("**Analyse :** La laine présente l'impact le plus élevé (jusqu'à 32 kg CO2e/kg en Pologne), tandis que le chanvre et le lin sont les options les plus durables.")

    
    # --- GRAPHIQUE 2 3 et 4 :
    st.markdown("---")
    st.header("📊 Numérique : Analyse de l’impact du numérique sur l’environnement en Suisse")
    try:
        st.image("image4.png", caption="Source : E4S & Resilio White Paper", use_container_width=True)
    except FileNotFoundError:
        st.error("L'image locale est introuvable. Vérifiez le chemin : images/votre_image_locale.png")
    st.info("**Analyse :** Les équipements (Tier I) concentrent la majorité des impacts environnementaux, tant en termes d’empreinte carbone (GWP) que d’épuisement des ressources (ADP), avec une contribution dominante des équipements à usage personnel")

    try:
        st.image("image5.png", caption="Source : E4S & Resilio White Paper", use_container_width=True)
    except FileNotFoundError:
        st.error("L'image locale est introuvable. Vérifiez le chemin : images/votre_image_locale.png")
    st.info("**Analyse :** En matière d’empreinte carbone des équipements à usage personnel, les smartphones constituent le principal poste d’impact, avec environ 26 %. Ils contribuent également à l’épuisement des ressources, mais leur part reste inférieure à celle des télévisions.")
    try:
        st.image("image6.png", caption="Source : E4S & Resilio White Paper", use_container_width=True)
    except FileNotFoundError:
        st.error("L'image locale est introuvable. Vérifiez le chemin : images/votre_image_locale.png")
    st.info("**Analyse :** En ce qui concerne l’empreinte carbone des équipements à usage professionnel, les ordinateurs constituent la principale source d’impact. En revanche, pour l’épuisement des ressources, ce sont les télévisions et les écrans d’ordinateur qui contribuent le plus.")

    # --- GRAPHIQUE 5 :
    st.markdown("---")
    st.subheader(" Répartition des Terminaux vs. Part de l'Empreinte Carbone en France")
    
    if df_electro_agg is None:
        st.warning("Les données agrégées (Feuille Electroniques) pour ce graphique ne sont pas disponibles.")
    else:
        st.markdown("Ce graphique compare, pour chaque catégorie, le **Pourcentage d'équipements** (Bleu) et le **Pourcentage d'empreinte carbone** (Rouge).")
        
        df = df_electro_agg.reset_index().copy()
        df.columns.values[0] = 'Categorie'


        df_long = pd.melt(
            df,
            id_vars='Categorie',
            value_vars=['Part_Empreinte_Carbone_Num', 'Part_Terminaux_Num'],
            var_name='Légendre',
            value_name='Pourcentage'
        )


        df_long['Légendre'] = df_long['Légendre'].replace({
            'Part_Terminaux_Num': 'Répartition des Terminaux',
            'Part_Empreinte_Carbone_Num': "Part de l'Empreinte Carbone"
        })
        
        df_long['Texte_Pourcentage'] = df_long['Pourcentage'].apply(lambda x: f"{x:.0f}%" if pd.notna(x) else "")
        cat_order = df.sort_values('Part_Terminaux_Num', ascending=False)['Categorie'].tolist()


        fig_bar = px.bar(
            df_long,
            x='Pourcentage',
            y='Categorie',
            color='Légendre',
            barmode='group',
            orientation='h',
            title="Pourcentage des Équipements vs. Pourcentage d'Empreinte Carbone par Catégorie en France",
            labels={"Categorie": "Type d'Équipement", "Pourcentage": "Pourcentage du Total (%)"},
            color_discrete_map={'Répartition des Terminaux': '#007BFF', "Part de l'Empreinte Carbone": '#DC3545'},
            category_orders={"Categorie": cat_order},
            text='Texte_Pourcentage'
        )
        
        fig_bar.update_traces(textposition='outside', cliponaxis=False)
        max_pourcentage = df_long['Pourcentage'].max()
        fig_bar.update_layout(font_size=10, height=500, xaxis=dict(range=[0, max_pourcentage * 1.15]))


        st.plotly_chart(fig_bar, use_container_width=True)
        st.caption("Source : Rapport ADEME (2020) – La face cachée du numérique.")
    



    # --- GRAPHIQUE 6 : CAMEMBERT (Données Détaillées - Electroniques2) ---
    st.markdown("---")
    st.subheader(" Répartition détaillée de l'Empreinte Carbone du Numérique")
    
    if df_electro_detail is None:
        st.warning("Les données détaillées (Feuille Electroniques2) pour le graphique circulaire ne sont pas disponibles.")
    else:
        df_pie_electro = df_electro_detail.reset_index().copy()
        
        value_col = 'Part_Empreinte_Carbone_Num'
        name_col = 'Categorie'
        
        df_pie_electro = df_pie_electro.dropna(subset=[value_col])


        fig_pie_electro = px.pie(
            df_pie_electro,
            values=value_col,
            names=name_col,
            title='Répartition détaillée de l\'Empreinte Carbone du Numérique (Terminaux + DataCenters)',
            category_orders={name_col: df_pie_electro.sort_values(value_col, ascending=False)[name_col].tolist()}
        )
        
        pull_list = [0.05 if name in ['DataCenters et réseaux', 'Smartphones'] else 0 for name in df_pie_electro[name_col]]


        fig_pie_electro.update_traces(
            textposition='inside',
            textinfo='percent+label',
            pull=pull_list
        )
        
        st.plotly_chart(fig_pie_electro, use_container_width=True)
        st.caption("Source : Rapport ADEME (2020) – La face cachée du numérique.")

        # Ajout d'une image pour illustrer le camembert
        st.info("**Analyse :** En dehors des data centers et des réseaux, ce sont les smartphones qui contribuent le plus aux émissions, avec 15,2 de pourcentage, suivis des téléviseurs à hauteur de 14,6 de pourcentage. Presque la même chose que la suisse")        


    # -----------------------------------------------------------
    # GRAPHIQUE 7 : Nuage de Points (Taille vs Puissance) - Electroniques3
    # -----------------------------------------------------------
    st.markdown("---")
    st.subheader(" Analyse : L'impact de la Taille d'Écran sur la Puissance Utilisée 📈")
    
    if df_electro_size_power is None or df_electro_size_power.empty:
        st.error("Les données pour le nuage de points (Feuille Electroniques3) ne sont pas disponibles.")
    else:
        st.markdown("Nuage de Points : Puissance Utilisée (W) en fonction de la Taille d'Écran (pouces) pour 58 références.")
        
        fig_scatter = px.scatter(
            df_electro_size_power,
            x='Taille_Ecran_Pouces',
            y='Puissance_W',
            title="Puissance Utilisée vs. Taille d'Écran (58 Références)",
            labels={
                'Taille_Ecran_Pouces': "Taille d'Écran (pouces)",
                'Puissance_W': "Puissance Utilisée (W)"
            },
            template="plotly_white",
            trendline="ols" # Requiert le module statsmodels
        )
        
        # Ajout de la ligne verticale pour la taille moyenne de 40 pouces
        fig_scatter.add_vline(
            x=40,
            line_width=1,
            line_dash="dash",
            line_color="grey",
            annotation_text="Taille moyenne d'un téléviseur en France (estimation)",
            annotation_position="top left"
        )
        
    st.plotly_chart(fig_scatter, use_container_width=True)
    st.caption("Source : Rapport ADEME (2020) – La face cachée du numérique.")
    st.info("**Analyse :**  plus la taille de l’écran augmente, plus la puissance consommée est élevée, ce qui entraîne une augmentation des émissions de carbone associées. Cette relation montre que, dans une optique de production et de consommation plus durables, il est préférable de privilégier des écrans de petite ou de taille moyenne afin de limiter l’impact environnemental.")
    
    # --- GRAPHIQUE 8 : Évolution de l'Impact Environnemental du Numérique ---
    st.markdown("---")
    st.subheader(" Scénario Tendanciel de l'Impact Environnemental du Numérique (2020-2050)")

    if df_impact_numerique is None or df_impact_numerique.empty:
        st.error("Les données pour le Scénario Tendanciel (Feuille Electronique4) ne sont pas disponibles.")
    else:
        st.markdown(
        """
        Ce graphique montre l'augmentation de l'impact du numérique sans actions de réduction.
        L'empreinte carbone pourrait presque tripler d'ici 2050.
        """
        )

        # 1. Préparation des données
        df_long_impact = df_impact_numerique.reset_index().melt(
            id_vars='Indicateur',
            var_name='Année',
            value_name='Augmentation_pourcentage'
    )
        df_long_impact['Année'] = pd.to_numeric(df_long_impact['Année'])
        
        couleurs = {
            'Empreinte carbone': '#DC3545',          
            'Ressources utilisées*': '#FF69B4',
            'Consommation d\'énergie finale': '#34495E',
            'Consommation de métaux et minéraux': '#3498DB',
        }

        # 2. Création du graphique
        fig_impact = px.line(
            df_long_impact,
            x='Année',
            y='Augmentation_pourcentage',
            color='Indicateur',
            title='Évolution de l\'Impact Environnemental (2020-2050)',
            labels={'Augmentation_pourcentage': 'Augmentation (%)', 'Année': 'Année'},
            color_discrete_map=couleurs,
            markers=True
        )

        # 3. Personnalisation des axes et annotations
        fig_impact.update_layout(
            xaxis=dict(tickvals=[2020, 2030, 2050]),
            hovermode="x unified",
            height=550
        )

        # Ajout des étiquettes de texte sur les points
        for i, row in df_long_impact.iterrows():
            if row['Année'] in [2030, 2050]:
                fig_impact.add_annotation(
                    x=row['Année'],
                    y=row['Augmentation_pourcentage'],
                    text=f"+{row['Augmentation_pourcentage']:.0f}%",
                    showarrow=False,
                    yshift=15
                )

        # --- ÉTAPE CRUCIALE MANQUANTE : Affichage dans Streamlit ---
        st.plotly_chart(fig_impact, use_container_width=True)
        st.caption("Source : Rapport ADEME (2020) – La face cachée du numérique.")
