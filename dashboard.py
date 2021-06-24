import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

def createHisto(title, histoDatas, ordonnee, abscisse):
    df = histoDatas
    figures = []
    for ord,tit in zip(ordonnee, title):
        figures.append(px.bar(df, x=abscisse, y=ord, color=ord, barmode="group", title=tit, template="plotly_dark",
        labels={
            abscisse:"Départements",
            ord:ord
        },))
    return figures
   
    
import folium
import os.path as path

def create_map_hospi(project_path, data, filter=None):
    Map = folium.Map(location=[47.1539,2.2508], tiles="cartodbpositron" ,zoom_start=5)#centre de la france
    choropleth = folium.Choropleth(
        geo_data=path.join(project_path, 'departements.geojson'),
        name="departements",
        data=data,
        columns=['nom', 'hospitalises'],
        key_on='feature.properties.nom',
        fill_color='PuRd',
        fill_opacity=0.7,
        line_opacity=0.2
    ).add_to(Map)

    folium.LayerControl().add_to(Map)
    choropleth.geojson.add_child(
        folium.features.GeoJsonTooltip(['nom'], labels=False)
    )
    Map.save(outfile=path.join(project_path, 'html/new_hospi.html'))

def create_map_gueris(project_path, data, filter=None):
    Map = folium.Map(location=[47.1539,2.2508], tiles="cartodbpositron" ,zoom_start=5)#centre de la france
    choropleth = folium.Choropleth(
        geo_data=path.join(project_path, 'departements.geojson'),
        name="departements",
        data=data,
        columns=['nom', 'gueris'],
        key_on='feature.properties.nom',
        fill_color='YlGn',
        fill_opacity=0.7,
        line_opacity=0.2
    ).add_to(Map)

    folium.LayerControl().add_to(Map)
    choropleth.geojson.add_child(
        folium.features.GeoJsonTooltip(['nom'], labels=False)
    )
    Map.save(outfile=path.join(project_path, 'html/gueris.html'))

def create_map_deces(project_path, data, filter=None):
    Map = folium.Map(location=[47.1539,2.2508], tiles="cartodbpositron" ,zoom_start=5)#centre de la france
    choropleth = folium.Choropleth(
        geo_data=path.join(project_path,'departements.geojson'),
        name="departements",
        data=data,
        columns=['nom', 'deces'],
        key_on='feature.properties.nom',
        fill_color='PuRd',
        fill_opacity=0.7,
        line_opacity=0.2
    ).add_to(Map)

    folium.LayerControl().add_to(Map)
    choropleth.geojson.add_child(
        folium.features.GeoJsonTooltip(['nom'], labels=False)
    )
    Map.save(outfile=path.join(project_path, 'html/deces.html'))


# In[3]:


import requests
import json
import psycopg2

from sqlalchemy import create_engine

def get_data_json(lien):
    liste=[]
    try:
        r = requests.get(lien,timeout=3)
        r.raise_for_status()
        req_json = json.loads(r.text)
        for data in req_json.values():
            for elements in data:
                liste.append(elements)    
        return pd.DataFrame(data=liste)
    
    except requests.exceptions.HTTPError as errh:
        print ("Http Error:",errh)
    except requests.exceptions.ConnectionError as errc:
        print ("Error Connecting:",errc)
    except requests.exceptions.Timeout as errt:
        print ("Timeout Error:",errt)
    except requests.exceptions.RequestException as err:
        print ("OOps: Something Else",err)
        
def get_data_postgres(username, password, host, port, database, table):
    engine = create_engine('postgresql+psycopg2://'+username+':'+password+'@'+host+':'+port+'/'+database)
    dbConnection = engine.connect()
    df = pd.read_sql("select * from "+table, dbConnection)
    pd.set_option('display.expand_frame_repr', False)
    dbConnection.close()
    return df


import os
from configparser import ConfigParser
#on recupere les datas
df = get_data_json("https://coronavirusapi-france.now.sh/AllLiveData")
db_info = ConfigParser()
db_info.read("config_info.ini")
#df = get_data_postgres(db_info.get("postgres", "USERNAME"), db_info.get("postgres", "PASSWORD"), db_info.get("postgres", "HOST"), 
                          #db_info.get("postgres", "PORT"), db_info.get("postgres", "DATABASE"), db_info.get("postgres", "TABLE"))
#On supprime les colonnes qu'on a pas besoin
#del df['source']
del df['sourceType']
del df['nouvellesHospitalisations']
del df['nouvellesReanimations']

app.title='Sujet COVID-19'    
#On supprime les lignes de regions qui ne nous sont pas utiles
number_regions = ["01", "02", "03", "04", "06", "05", "11", "24", "27", "28", "32", "44", "52", "53", "75", "76", "84", "93", "94"]
for region in number_regions:
    index = df.index
    condition = df["code"] == "REG-"+region
    indices = index[condition]
    df.drop(indices, inplace=True)
    
#On mets de cote les valeurs pour la France entiere
indexNames = df[df['nom'] == 'France'].index
df_France = df[df['nom'] == 'France'].values
#on les enleve du DataFrame
df.drop(indexNames, inplace=True)

project_path = os.getcwd()
#project_path = "/"
#creations des cartes
create_map_hospi(project_path, df)
create_map_deces(project_path, df)
create_map_gueris(project_path, df)
#creation des histogrammes
figures = createHisto(["Nombre de personnes ayant été hospitalisées selon le département", "Nombre de personnes décédés selon le département", "Nombre de guérisons selon le département"], df, ["hospitalises","deces","gueris"], "nom")
colors = {
    'background': '#111111',
    'text': '#7FDBFF',
    'subtitle': 'white'
    }

#-----------------------Haut de page---------------------------------
app.layout = html.Div(style={
    'backgroundColor': colors['background'],
    'textAlign': 'center'
    }, 
    children=[
html.H1(children='DASHBOARD 1% per Day', style={
        'textAlign': 'center',
        'color': colors['text']
    }
),
html.P(children="Cette page est répartie en trois morceaux et montre l'impact de la COVID-19 depuis le début de l'épidémie selon différents critères et selon les départements Français", style={
    'color':colors['subtitle']
}),
html.P(children="Les données sont mises à jour tous les jours !", style={
    'color':colors['subtitle']
}),
html.Hr(),
#----------------------Données totales----------------------------------
html.Div(style={
    'textAlign':'left',
    'color': colors['subtitle']
    },
    children=[
    html.H3(" Données totales en France depuis le début de la pandémie"),
    html.H4(" Nombre de guéris total : " + str(df_France[0][6])),
    html.H4(" Nombre d'hospitalisés total : " + str(df_France[0][3])),
    html.H4(" Nombre de décès total : " + str(df_France[0][5])),
]),
html.Hr(),
#---------------------PARTIE 1------------------------------------------
html.H3(children='Carte de France des hospitalisations de la COVID-19', style={
    'color': colors['subtitle']
}),
html.Iframe(id='map_hospi', srcDoc=open('html/new_hospi.html', 'r').read(), width='80%', height='400'),
    dcc.Graph(
        id='covid-rea',
        figure=figures[0]
        ),
html.Hr(),
#---------------------PARTIE 2-----------------------------------------
html.H3('Carte de France des guérisons de la COVID-19', style={
    'textAlign': 'center',
    'color': colors['subtitle']
}),
html.Iframe(id='map_gueris', srcDoc=open('html/gueris.html', 'r').read(), width='80%', height='400'),
    dcc.Graph(
        id='covid-healed',
        figure=figures[2]
    ),
html.Hr(),
#---------------------PARTIE 3-----------------------------------------
html.H3('Carte de France des décès de la COVID-19',style={
    'textAlign': 'center',
    'color': colors['subtitle']
}),
html.Iframe(id='map_deces', srcDoc=open('html/deces.html', 'r').read(), width='80%', height='400'),
    dcc.Graph(
        id='covid-dead',
        figure=figures[1]
    ),      
])

if __name__ == '__main__':
    app.run_server(debug=False)



