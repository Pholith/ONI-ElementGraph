# libraries
import pandas as pd

import typing
import os
import re
import json

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_cytoscape as cyto
from dash.dependencies import Input, Output
import dash_reusable_components as drc

import style


# CONST
elementFiles: str = "E:\Program Files (x86)\Steam\steamapps\common\OxygenNotIncluded\OxygenNotIncluded_Data\StreamingAssets\elements\\"
pattern = re.compile("([a-z]+): ([^\W ]*).*$", flags=re.IGNORECASE+re.MULTILINE)
showTemp = False

# Load Dash
app = dash.Dash(__name__)
server = app.server

# Load layouts 
cyto.load_extra_layouts()

# Functions
def LoadRecipes():
    with open("datas.json") as f:
        fileContent: str = f.read()
    recipes = json.loads(fileContent)

    datas = []

    for recipe in recipes:
        for elementIn in recipe["input"]:
            if elementIn["id"] == "":
                break
            for elementOut in recipe["output"]:
                datas.append({"data": {"source": elementIn["id"], "target": elementOut["id"], "label":  str(round(float(elementOut["mass"]) / float(elementIn["mass"]) * 100))+"%" } })

    return datas

def LoadElements(fileName: str):
    file = os.path.join(elementFiles, fileName)

    with open(file) as f:
        fileContent: str = f.read()

    dct = {} # associe le nom de l'element à un dict qui contient les infos
    datas = [] # Données renvoyés par la fonction

    for element in re.split("\n\W*\n", fileContent):
        res = re.findall(pattern, element)
        for match in res:
            if res[0][1] not in dct:
                dct[res[0][1]] = {}
            dct[res[0][1]][match[0]] = match[1]
        # print(res[0][1]) # id de l'élément

    
    for key in dct.keys(): # Pour tous les éléments

        
        if dct[key]["state"] == "Solid":
            clazz = "solid"
        elif dct[key]["state"] == "Gas":
            clazz = "gas"
        else:
            clazz = "liquid"

        datas.append({"data": {"id": key, "label": key}, "classes": clazz})

        if "lowTempTransitionTarget" in dct[key]:
            labelTxt = dct[key]["lowTemp"]+"°C" if showTemp else ""
            datas.append({"data": {"source": key, "target": dct[key]["lowTempTransitionTarget"], "label": labelTxt}, "classes": "blue"})

        if "highTempTransitionTarget" in dct[key]:
            labelTxt = dct[key]["highTemp"]+"°C" if showTemp else ""

            if (dct[key]["highTempTransitionTarget"] == "COMPOSITION"):
                pass # gérer le cas de la mud qui a plusieurs états
            else:
                datas.append({"data": {"source": key, "target": dct[key]["highTempTransitionTarget"], "label": labelTxt}, "classes": "red"})

    return datas

# Callbacks
@app.callback(Output('cytoscape', 'stylesheet'), Input('tempBox', 'value'))
def show_hide_element(boxValues):
    if boxValues and "temp" in boxValues:
        style.myStylesheet[1]['style']['content'] = 'data(label)'
        return style.myStylesheet
    else:
        style.myStylesheet[1]['style']['content'] = ''
        return style.myStylesheet

@app.callback(Output('cytoscape', 'layout'), Input('dropdown-layout', 'value'))
def update_cytoscape_layout(layout):
    return {'name': layout}

@app.callback( Output("cytoscape", "generateImage"), Input("btn-get-svg", "n_clicks"))
def get_image(get_svg_clicks):
    ctx = dash.callback_context
    if ctx.triggered[0]["value"] == None:
        return {'action': 'none'}
    return {'type': "svg", 'action': "download"}

# Chargement des données
datas = []
print("Loading solids...")
datas.extend(LoadElements("solid.yaml"))
print("Loading liquids...")
datas.extend(LoadElements("liquid.yaml"))
print("Loading gas...")
datas.extend(LoadElements("gas.yaml"))
print("Loading recipes...")
datas.extend(LoadRecipes())

jsonOut = json.dumps(datas)
with open("dataOutout.json", "w") as f:
    f.write(jsonOut)

app.layout = html.Div([
    #html.P("Dash Cytoscape:"),
    cyto.Cytoscape(
        id='cytoscape',
        elements=datas,
        layout={"name": 'cose-bilkent',
                "animate": False, #}, # dagre, klay et cose-bilkent sont pas trop mal
                "fit": False, 
                "idealEdgeLength": 256, 
                "edgeElasticity": 512, 
                "nodeDimensionsIncludeLabels": True,
                "nodeOverlap": 40, 
                "nodeRepulsion": 4048
                },
        stylesheet=style.myStylesheet,
        style={'width': '1100px', 'height': '550px'}
    ),
    html.Div([
        dcc.Checklist(
            id="tempBox",
            options=[
                {'label': 'Show temp', 'value': 'temp'},
            ],
            value=["temp"]
        ),
        #html.Button("as svg", id="btn-get-svg")
        dcc.Tab(label='Control Panel', children=[
        drc.NamedDropdown(
            name='Layout',
            id='dropdown-layout',
            options=drc.DropdownOptionsList(
                'random',
                'grid',
                'circle',
                'concentric',
                'breadthfirst',
                'cose',
                'cose-bilkent',
                'dagre',
                'cola',
                'klay',
                'spread',
                'euler'
            ),
            value='klay',
            clearable=False
            ),
        ]),
        html.Button("Export svg", id="btn-get-svg")
    ])
], style = {"display": "flex", "flex-direction": "row", "width": "90%"}
)

app.run_server(debug=True)

