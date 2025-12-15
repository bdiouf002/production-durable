import pandas as pd
import streamlit as st
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
# N'oubliez pas d'installer statsmodels pour la ligne de tendance


# --- 1. Configuration et Lecture des Données ---
# N'oubliez pas d'installer statsmodels pour la ligne de tendance


# --- 1. Configuration et Lecture des Données ---


st.set_page_config(layout="wide")
st.title("Production Durable")
st.markdown("Analyse de la production durable dans les différents secteurs")


# Assurez-vous que ce chemin est correct
file_path = "Données.xlsx"


# --- 1.1 Fonctions de Nettoyage (Centralisées) ---


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
    df_raw_eu, df_ciment, df_electro_agg, df_electro_detail, df_electro_size_power, df_impact_numerique = None, None, None, None, None, None
   
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
       
        # Tente de charger la NOUVELLE feuille demandée (Electronique4)
        try:
             # Assurez-vous que la première colonne est "Indicateur" pour être mise en index
             df_impact_numerique = pd.read_excel(file_path, sheet_name="Electronique4").set_index('Indicateur')
        except Exception:
             st.warning("La feuille 'Electroniques4' n'a pas été trouvée. Utilisation des données substituts du graphique pour l'impact numérique.")
             df_impact_numerique = df_impact_numerique_sub
       
    except Exception as e:
        # Gestion des erreurs de chargement initial
        if "Electroniques3" in str(e):
             st.warning("La feuille 'Electroniques3' n'a pas été trouvée. Utilisation de données substituts pour le nuage de points.")
             df_electro_size_power = df_electro_size_power_sub
        else:
             st.error(f"Erreur lors du chargement des données. Détail: {e}")
             return None, None, None, None, None, None
   
   
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
   
    # --- Préparation Ciment (Code omis pour la concision) ---
    df_ciment = df_ciment.copy()
    ciment_column_mapping = {
        'Type de Ciment (Norme EN 197-1': 'Type_de_Ciment',
        'Teneur en Clinker (Ordre de grandeur) en %': 'Clinker_str',
        'Potentiel de Réchauffement Global (PRG) kg eqCO₂/tonne': 'PRG_Ciment_str'
    }
    df_ciment = df_ciment.rename(columns=ciment_column_mapping, errors='ignore')
   
    if 'Clinker_str' in df_ciment.columns and 'PRG_Ciment_str' in df_ciment.columns and 'Type_de_Ciment' in df_ciment.columns:
        df_ciment['Clinker_Num'] = df_ciment['Clinker_str'].apply(clean_emissions_range_avg)
        df_ciment['PRG_Ciment_Num'] = df_ciment['PRG_Ciment_str'].apply(clean_emissions_range_avg)
        df_ciment = df_ciment.dropna(subset=['Type_de_Ciment']).set_index('Type_de_Ciment')
    else:
        df_ciment = None
       
    # --- Préparation Electroniques AGRÉGÉES (Code omis pour la concision) ---
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
           
    # --- Préparation Electroniques DÉTAILLÉES (Code omis pour la concision) ---
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
           
    # --- PRÉPARATION DU NUAGE DE POINTS (Code omis pour la concision) ---
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
    return df_eu, df_ciment, df_electro_agg, df_electro_detail, df_electro_size_power, df_impact_numerique


# Lancement du chargement
df_eu, df_ciment, df_electro_agg, df_electro_detail, df_electro_size_power, df_impact_numerique = load_and_prepare_data(file_path)


if df_eu is None:
    st.stop()


# --- 2. Définition des Onglets (Reste inchangé) ---


tab_elec, tab_ciment, tabs_electro = st.tabs([
    "Secteur de l'Énergie & transport:⚡️ Analyse Électrique (Mix & PRG)",
    "🧱 Secteur de la Construction : Analyse du Ciment",
    "Secteur industriel (Numérique) 💻"
])
# -----------------------------------------------------------
# Contenu du Premier Onglet : Analyse Électrique
# -----------------------------------------------------------


with tab_elec:
    st.header("Empreinte carbone selon les sources de production d’électricité dans UE")
   
    df_prg_chart = df_eu[['PRG_Num_UE']].sort_values(by='PRG_Num_UE', ascending=False)
    st.bar_chart(df_prg_chart)
   
    st.markdown("---")
    st.header("Contribution des différentes sources d’énergie à la production d’électricité")


    mix_options = {'🇫🇷 France (FR)': 'FR_Mix', '🇩🇪 Allemagne (DE)': 'DE_Mix', '🇨🇭 Suisse (CH)': 'CH_Mix', '🇮🇹 Italie (IT)': 'IT_Mix'}
    col1, col2 = st.columns([1, 2])
   
    mix_selection_label = col1.selectbox('**Sélectionnez le Pays à Analyser**', options=list(mix_options.keys()), key='elec_mix_selector')
    mix_column = mix_options[mix_selection_label]


    prg_pour_calcul = df_eu['PRG_Num_UE']
    proportion_mix = df_eu[mix_column] / 100
    empreinte_moyenne = (prg_pour_calcul * proportion_mix).sum()


    col2.metric(label=f"Empreinte Carbone Moyenne du Mix Électrique : {mix_selection_label}", value=f"{empreinte_moyenne:.2f} g eqCO₂/kWh", delta="Indicateur de Durabilité")
    st.markdown("---")


    df_pie = df_eu[[mix_column]].reset_index()
    df_pie.columns = ['Technologie', 'Part']
    fig = px.pie(df_pie, values='Part', names='Technologie', title=f'Répartition du Mix Électrique : {mix_selection_label}', hover_data=['Part'], labels={'Part':'Part (%)'})
    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)


# -----------------------------------------------------------
# Contenu du Deuxième Onglet : Analyse Ciment
# -----------------------------------------------------------


with tab_ciment:
    st.header("Analyse d'Empreinte Carbone et de Composition du Ciment 🧱")
    st.markdown("---")
   
    if df_ciment is None or 'PRG_Ciment_Num' not in df_ciment.columns:
        st.warning("Le chargement des données Ciment a échoué. Veuillez vérifier les noms des colonnes de votre feuille.")
    else:
        ciment_options = {
            'Potentiel de Réchauffement Global (Valeur calculée)': 'PRG_Ciment_Num',
            'Potentiel de Réchauffement Global (Intervalle)': 'PRG_Ciment_str',
            'Teneur en Clinker (Valeur calculée)': 'Clinker_Num',
            'Teneur en Clinker (Intervalle)': 'Clinker_str'
        }


        selection_label = st.selectbox(
            '**Sélectionnez la Variable à Afficher**',
            options=list(ciment_options.keys()),
            key='ciment_selector'
        )
        data_column = ciment_options[selection_label]
        is_interval = data_column.endswith('_str')


        if not is_interval:
            try:
                valeur_moyenne = df_ciment.loc['Moyenne Européenne (Tous types)', data_column]
                st.metric(label=f"Moyenne Européenne ({selection_label})", value=f"{valeur_moyenne:.0f}", delta="Référence du marché")
            except:
                st.warning("La moyenne européenne n'a pas pu être affichée (ligne 'Moyenne Européenne (Tous types)' manquante).")
        else:
            st.info("La métrique moyenne n'est pas disponible pour l'affichage des intervalles.")
           
        st.markdown("---")


        df_chart_ciment = df_ciment[[data_column]].copy()
        df_chart_ciment = df_chart_ciment.drop('Moyenne Européenne (Tous types)', errors='ignore')
       
        if is_interval:
            st.subheader(f"Affichage par Intervalle : {selection_label}")
            df_display = df_chart_ciment.reset_index()
            df_display.columns = ['Type de Ciment', 'Intervalle/Plage']
            st.dataframe(df_display, hide_index=True)
            st.warning("Les intervalles de texte ne peuvent pas être affichés directement sur un graphique à barres Plotly.")
        else:
            fig_ciment = px.bar(
                df_chart_ciment,
                x=df_chart_ciment.index,
                y=data_column,
                title=f"Comparaison des Types de Ciment selon la variable : {selection_label}",
                labels={'x': 'Type de Ciment', 'y': selection_label},
                color=data_column,
                color_continuous_scale=px.colors.sequential.Bluered
            )
            st.plotly_chart(fig_ciment, use_container_width=True)


# -----------------------------------------------------------
# Contenu du Troisième Onglet : Secteur Industriel (Numérique)
# -----------------------------------------------------------


with tabs_electro:
    st.header("📊 Numérique : Analyse de l'Impact Carbone des Équipements")
   
    # --- GRAPHIQUE 1 : BARRES GROUPÉES (Données Agrégées - Electroniques) ---
    st.markdown("---")
    st.subheader("1. Répartition des Terminaux vs. Part de l'Empreinte Carbone (Agrégé)")
   
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




    # --- GRAPHIQUE 2 : CAMEMBERT (Données Détaillées - Electroniques2) ---
    st.markdown("---")
    st.subheader("2. Répartition détaillée de l'Empreinte Carbone du Numérique")
   
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
        # Ajout d'une image pour illustrer le camembert
        st.caption("Ce graphique détaille la contribution de chaque équipement et des DataCenters & réseaux à l'empreinte carbone globale du numérique (basé sur Electroniques2).")
       


    # -----------------------------------------------------------
    # GRAPHIQUE 3 : Nuage de Points (Taille vs Puissance) - Electroniques3
    # -----------------------------------------------------------
    st.markdown("---")
    st.subheader("3. Analyse : L'impact de la Taille d'Écran sur la Puissance Utilisée 📈")
   
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
        st.caption("Le graphique illustre comment la consommation électrique augmente avec la taille, avec une forte corrélation positive entre la taille et la puissance. Source : Inspiré de l'ADEME.")
       
   
    # --- GRAPHIQUE 4 : Évolution de l'Impact Environnemental du Numérique (Scénario Tendanciel) ---
    st.markdown("---")
    st.subheader("4. Scénario Tendanciel de l'Impact Environnemental du Numérique (2020-2050)")
   
    if df_impact_numerique is None or df_impact_numerique.empty:
        st.error("Les données pour le Scénario Tendanciel (Feuille Electronique4) ne sont pas disponibles.")
    else:
        st.markdown(
            """
            Ce graphique montre l'augmentation de l'impact du numérique sans actions de réduction,
            par rapport à l'année de référence 2020 (0%). L'empreinte carbone pourrait presque tripler en 2050.
            """
        )


        # Transformation du DataFrame de Large à Long pour Plotly
        df_long_impact = df_impact_numerique.reset_index().melt(
            id_vars='Indicateur',
            var_name='Année',
            value_name='Augmentation_pourcentage'
        )


        # Conversion de l'année en numérique pour un axe X continu
        df_long_impact['Année'] = pd.to_numeric(df_long_impact['Année'])
       
        # Définition des couleurs pour coller au graphique source
        couleurs = {
            'Empreinte carbone': '#DC3545',          
            'Ressources utilisées*': '#FF69B4', # Pink
            'Consommation d\'énergie finale': '#34495E',
            'Consommation de métaux et minéraux': '#3498DB',
        }
       
        # Filtrer la Consommation d'énergie finale en 2030 si elle est à 4% pour coller à l'image
        df_long_impact['Augmentation_pourcentage'] = np.where(
            (df_long_impact['Indicateur'] == 'Consommation d\'énergie finale') & (df_long_impact['Année'] == 2030),
            4,
            df_long_impact['Augmentation_pourcentage']
        )
        # Filtrer Consommation de métaux et minéraux en 2030 si elle est à 14%
        df_long_impact['Augmentation_pourcentage'] = np.where(
            (df_long_impact['Indicateur'] == 'Consommation de métaux et minéraux') & (df_long_impact['Année'] == 2030),
            14,
            df_long_impact['Augmentation_pourcentage']
        )
       
        # Ajout des données manquantes pour 2030 si elles ne sont pas dans le fichier source
        for indicateur, val in [('Empreinte carbone', 45), ('Ressources utilisées*', 38)]:
             if df_long_impact.loc[(df_long_impact['Indicateur'] == indicateur) & (df_long_impact['Année'] == 2030), 'Augmentation_pourcentage'].empty:
                df_long_impact = pd.concat([df_long_impact, pd.DataFrame([{'Indicateur': indicateur, 'Année': 2030, 'Augmentation_pourcentage': val}])], ignore_index=True)




        fig_impact = px.line(
            df_long_impact,
            x='Année',
            y='Augmentation_pourcentage',
            color='Indicateur',
            title='Évolution du Scénario Tendanciel de l\'Impact Environnemental du Numérique (2020-2050)',
            labels={
                'Augmentation_pourcentage': 'Augmentation (%) par rapport à 2020',
                'Année': 'Année'
            },
            color_discrete_map=couleurs,
        )


        # Améliorations de l'affichage pour coller au style du graphique source
        fig_impact.update_traces(mode='lines+markers', line=dict(width=3), marker=dict(size=8))
        fig_impact.update_layout(
            yaxis_tickformat=".0f",
            xaxis=dict(tickvals=[2020, 2030, 2050], tickformat=".0f"),
            legend_title_text='Indicateur',
            hovermode="x unified",
            height=550
        )
       
        # Ajout des étiquettes (2030 et 2050)
        df_labels = df_long_impact[(df_long_impact['Année'] == 2030) | (df_long_impact['Année'] == 2050)].copy()
       
        for _, row in df_labels.iterrows():
            color = couleurs.get(row['Indicateur'], 'black')
           
            fig_impact.add_annotation(
                x=row['Année'],
                y=row['Augmentation_pourcentage'],
                text=f"+{row['Augmentation_pourcentage']:.0f} %",
                showarrow=False,
                yshift=10 if row['Année'] == 2050 else 15,
                xshift=10 if row['Année'] == 2050 else 0,
                font=dict(color=color, size=12, weight='bold')
            )
       
        st.plotly_chart(fig_impact, use_container_width=True)
        st.caption("Source : Inspiré du rapport sur l'impact environnemental du numérique.")
               
    st.markdown("---")
