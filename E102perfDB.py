__author__='Ali T.'

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import pandas as pd
import numpy as np
from scipy.interpolate import spline,interp1d
from catmullrom import CatmullRomChain
from pathlib import Path
from dash.dependencies import Input, Output
import logging
import cx_Oracle

app = dash.Dash()
app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})

colors = {
    'background': '#111111',
    'text': '#000000'
}

#winding number with more than one
#subid
#T445(4-6)16,K213(4-8)32
#mtrid
#K184260,K213269(21 MTRID),K2154249(38 MTRID)
#filering sequence should be
#Appwdg=>mtrid==>subid

#filepath variable to database
#root_dir = Path(r"C:\Users\User\Documents\E102\perf_dbase_wdg.xlsx")
#dbase = root_dir.glob('**/*.xlsx')
#database header names matrix
"""
Load    CurrentL    TorqueL         EffL        PfL
0       AMP_NL      0               NA          PF_NL
25      AMP_25      TQ_25           EFF_25      PF_25
50      AMP_50      TQ_50           EFF_50      PF_50
75      AMP_75      TQ_75           EFF_75      PF_75
100     AMP_100     TQ_100          EFF_100     PF_100
115     AMP_115     1.15*TQ_100     EFF_115     PF_115
125     AMP125      TQ_125          EFF_125     PF_125

Speed       CurrentS    TorqueS
0           AMP_LR      TQ_LR
RPM_PU      AMP_PU      TQ_PU
RPM_BD      AMP_BD      TQ_BD
RPM_100     AMP_100     TQ_100
APP_SRPM    AMP_NL      0
"""

#loading data from two csv file
# df_speed = pd.read_csv('MotorSpeedData.csv')
# df_load = pd.read_csv('MotorLoadData.csv')
#d = pd.read_excel(root_dir, sheet_name='dbase')
d=pd.read_pickle('perfdb.pkl') # serialised database in pickle file
row=1000

#saving index of mtrid to grab row location
index=pd.Index(d['MTRID'])

#Read from Oracle database
def read_from_db (username, password, connectString,query, mode=None, save=False):
 
    if mode is None:
        connection = cx_Oracle.connect(username, password, connectString)
    else:
        connection = cx_Oracle.connect(username, password, connectString, mode)
    with connection:
        try:
            df = pd.read_sql_query(query,connection)
            if save:
                df.to_csv('results.csv')
            return df
        except cx_Oracle.DatabaseError as dberror:
            print dberror

#to read from database into a pandas dataframe
query='SELECT MTRID FROM DESIGN.VPERFORMANCE_DATA'
mtridtable=read_from_db('***','***','***',query)
indexmtrid=pd.Index(mtridtable)

#extract data and save in dataframe table for load table
def populate_load_table(row):
    effLoadArray = np.array([np.nan,d.iloc[row]['EFF_25'],d.iloc[row]['EFF_50'],d.iloc[row]['EFF_75'],d.iloc[row]['EFF_100'],d.iloc[row]['EFF_115'],d.iloc[row]['EFF_125']])
    pfLoadArray = np.array([d.iloc[row]['PF_NL'],d.iloc[row]['PF_25'],d.iloc[row]['PF_50'],d.iloc[row]['PF_75'],d.iloc[row]['PF_100'],d.iloc[row]['PF_115'],d.iloc[row]['PF_125']])
    torqueLoadArray = np.array([0,d.iloc[row]['TQ_25'],d.iloc[row]['TQ_50'],d.iloc[row]['TQ_75'],d.iloc[row]['TQ_100'],1.15*d.iloc[row]['TQ_100'],d.iloc[row]['TQ_125']])
    currentLoadArray = np.array([d.iloc[row]['AMP_NL'],d.iloc[row]['AMP_25'],d.iloc[row]['AMP_50'],d.iloc[row]['AMP_75'],d.iloc[row]['AMP_100'],d.iloc[row]['AMP_115'],d.iloc[row]['AMP_125']])

    loadArray = np.array([0,25,50,75,100,115,125])
    loadtable = pd.DataFrame(
    {'Load-%': loadArray,
    'Current-Amps':currentLoadArray,
    'Torque-lb.ft':torqueLoadArray,
    'Efficiency':effLoadArray,
    'Power Factor':pfLoadArray})

    loadtable=loadtable[['Load-%','Current-Amps','Torque-lb.ft','Efficiency','Power Factor']]

    return loadtable

#extract data and save in dataframe table for speed table
def populate_speed_table(row):
    rpmArray = np.array([0,d.iloc[row]['RPM_PU'],d.iloc[row]['RPM_BD'],d.iloc[row]['RPM_100'],d.iloc[row]['APP_SRPM'] ])
    torqueArray = np.array([d.iloc[row]['TQ_LR'],d.iloc[row]['TQ_PU'],d.iloc[row]['TQ_BD'],d.iloc[row]['TQ_100'],0])
    currentArray = np.array([d.iloc[row]['AMP_LR'],d.iloc[row]['AMP_PU'],d.iloc[row]['AMP_BD'],d.iloc[row]['AMP_100'],d.iloc[row]['AMP_NL']])

    speedtable = pd.DataFrame(
    {' ':['Locked Rotor','Pull-Up','Breakdown','Rated','Idle'],
    'Speed': rpmArray,
    'Current-Amps':currentArray,
    'Torque-lb.ft':torqueArray,
    })
    speedtable=speedtable[[' ','Speed','Current-Amps','Torque-lb.ft']]
    
    return speedtable


#perform point and curve fitting using catmullrom algorithm. Outputs are variable to be plotted for torque speed graph
def torquespeed(row):
    #MotorSpeedData extraction and array manipulation
    #Array adding points @ start & end to manipulate 
    #curve slope. Those are point P1, P4 as per catmull-rom

    #reading points from database for selected filtered row from dropdown
    rpmArray = np.array([0,d.iloc[row]['RPM_PU'],d.iloc[row]['RPM_BD'],d.iloc[row]['RPM_100'],d.iloc[row]['APP_SRPM']])
    rpmArray = np.insert(rpmArray,0,-1) # adding 0 to start of array
    rpmArray = np.append(rpmArray,rpmArray.max()) #adding max rpm to end of array

    torqueArray = np.array([d.iloc[row]['TQ_LR'],d.iloc[row]['TQ_PU'],d.iloc[row]['TQ_BD'],d.iloc[row]['TQ_100'],0])
    torqueArray = np.insert(torqueArray,0,torqueArray[0])
    torqueArray = np.append(torqueArray,torqueArray[-1]-1)

    currentArray = np.array([d.iloc[row]['AMP_LR'],d.iloc[row]['AMP_PU'],d.iloc[row]['AMP_BD'],d.iloc[row]['AMP_100'],d.iloc[row]['AMP_NL']])
    currentArray = np.insert(currentArray,0,currentArray[0])
    currentArray = np.append(currentArray,currentArray[-1]-1)

    torque_xy=np.column_stack((rpmArray,torqueArray))
    current_xy=np.column_stack((rpmArray,currentArray))
    
    #creating splines using catmullrom algorithm
    c_torque = CatmullRomChain(torque_xy)
    c_current = CatmullRomChain(current_xy)

    # coordinates point for curve catmullrom splines
    xRPM, yTorque = zip(*c_torque)
    xRPM, yCurrent = zip(*c_current)
        
    #coordinates point for data point
    pxRPM, pyTorque = zip(*torque_xy)
    pxRPM, pyCurrent = zip(*current_xy)

    return xRPM,np.array(pxRPM),yTorque,np.array(pyTorque),yCurrent,np.array(pyCurrent)

#perform point and curve fitting using catmullrom algorithm. Outputs are variable to be plotted for load efficiency graph
def loadefficiency(row):

    #reading points from database for selected filtered row from dropdown
    #MotorLoadData extraction and array manipulation
    loadArray = np.array([0,0,25,50,75,100,115,125,125])

    effLoadArray = np.array([np.nan,d.iloc[row]['EFF_25'],d.iloc[row]['EFF_50'],d.iloc[row]['EFF_75'],d.iloc[row]['EFF_100'],d.iloc[row]['EFF_115'],d.iloc[row]['EFF_125']])
    effLoadArray = np.insert(effLoadArray,1,effLoadArray[1]-0.01)
    effLoadArray = np.append(effLoadArray,effLoadArray[-1]+0.01)

    pfLoadArray = np.array([d.iloc[row]['PF_NL'],d.iloc[row]['PF_25'],d.iloc[row]['PF_50'],d.iloc[row]['PF_75'],d.iloc[row]['PF_100'],d.iloc[row]['PF_115'],d.iloc[row]['PF_125']])
    pfLoadArray = np.insert(pfLoadArray,0,pfLoadArray[0]-0.01)
    pfLoadArray = np.append(pfLoadArray,pfLoadArray[-1]+0.01)

    currentLoadArray = np.array([d.iloc[row]['AMP_NL'],d.iloc[row]['AMP_25'],d.iloc[row]['AMP_50'],d.iloc[row]['AMP_75'],d.iloc[row]['AMP_100'],d.iloc[row]['AMP_115'],d.iloc[row]['AMP_125']])
    currentLoadArray = np.insert(currentLoadArray,0,currentLoadArray[0]-0.01)
    currentLoadArray = np.append(currentLoadArray,currentLoadArray[-1]+0.01)

    torqueLoadArray = np.array([0,d.iloc[row]['TQ_25'],d.iloc[row]['TQ_50'],d.iloc[row]['TQ_75'],d.iloc[row]['TQ_100'],1.15*d.iloc[row]['TQ_100'],d.iloc[row]['TQ_125']])
    torqueLoadArray = np.insert(torqueLoadArray,0,torqueLoadArray[0]-0.01)
    torqueLoadArray = np.append(torqueLoadArray,torqueLoadArray[-1]+0.01)

    eff_xy=np.column_stack((loadArray,effLoadArray))
    pf_xy=np.column_stack((loadArray,pfLoadArray))
    currload_xy=np.column_stack((loadArray,currentLoadArray))
    
    #creating splines using catmullrom algorithm
    c_eff = CatmullRomChain(eff_xy)
    c_pf = CatmullRomChain(pf_xy)
    c_currload = CatmullRomChain(currload_xy)

    # coordinates point for curve catmullrom splines
    xload, yEff = zip(*c_eff)
    xload, yPF = zip(*c_pf)
    xload, yCurrload = zip(*c_currload)

    #coordinates point for data point
    pxload, pyEff = zip(*eff_xy)
    pxload, pyPF = zip(*pf_xy)
    pxload, pyCurrload = zip(*currload_xy)

    return np.array(xload),np.array(pxload),np.array(yEff),np.array(pyEff),np.array(yCurrload),np.array(pyCurrload),np.array(yPF),np.array(pyPF)


#function to generate table from pandas dataframe
def generate_table(dataframe, max_rows=8):
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in dataframe.columns])] +

        # Body
        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))]
    )


appWdg_indicators = d['APP_WDG'].unique()
mtrid_indicators = d['MTRID'].unique()

#html layout
app.layout = html.Div([
    html.H1(
        children='Perfomance database web app',
        style={
            'textAlign': 'center',
            'color': colors['text'],
        }
    ),

html.Div([

        html.Div(className="five columns",children=[
        html.H5('App Winding'),
        dcc.Dropdown(
            id='appWdg',
            options=[{'label': i, 'value': i} for i in appWdg_indicators],
            value=1000
        )],
 #       style={'width': '30%'}
        ),

        html.Div(className="five columns",children=[
        html.H5('Motor Id'),
        dcc.Dropdown(
            id='mtrid'
        )],
#        style={'width': '30%'}
        ),

    ],
    style={'width':'100%', 'display': 'inline-block','marginRight': 'auto','marginLeft': 'auto','float': 'center',}),


    html.Div(className="five columns",children=[
        dcc.Graph(
            id='speed-torque',
            style={'height':'400'}
        )],
        style={'display':'inline-block','marginTop': '30'}
    ),

    html.Div(className="five columns",children=[
        dcc.Graph(
            id='load-efficiency',         
            style={'height':'400'}
        )],
        style={'display':'inline-block','marginTop': '30',}  
    ),

     
    html.Div([
        html.Div(className="five columns",children=[html.H5('Motor speed data'),html.Div(id='speedtable')] ,style={'marginLeft': '10','marginTop': '10'} ),
        html.Div(className="five columns",children=[html.H5('Motor load data'),html.Div(id='loadtable')] ,style={'marginTop': '10'} ),
    ],
    style={'width':'100%','float': 'center'}
    ),
],
style={'width':'100%','float': 'center','display': 'inline-block','padding': 2,'border': 'thin lightgrey solid','border-radius':'5'}
)


#callback to update MTRID dropdown
@app.callback(
    Output(component_id='mtrid',component_property='options'),
    [Input(component_id='appWdg',component_property='value')]
)

def loadMTRid(wdg):
    mtrid=d[ d['APP_WDG'] == wdg ]['MTRID']
    return [{'label':i,'value':i} for i in mtrid]
    
#callback to update load table
@app.callback(
    Output('loadtable', 'children'),
    [Input('mtrid', 'value')]
)

def update_loadtable(value):
    row=index.get_loc(value)
    dff = populate_load_table(row)
    return generate_table(dff)

    
#callback to update speed table
@app.callback(
    Output('speedtable', 'children'),
    [Input('mtrid', 'value')]
)

def update_speedtable(value):
    row=index.get_loc(value)
    dff = populate_speed_table(row)
    return generate_table(dff)


#calllback to update torque speed graph
@app.callback(
    Output('speed-torque','figure'),
    [Input('mtrid','value')]
)

def update_speedtorque(value):
    row=index.get_loc(value)
    xRPM,pxRPM,yTorque,pyTorque,yCurrent,pyCurrent = torquespeed(row)
    #logging.warning('type(row) is %s, value is %s', type(row),row)
    #logging.warning('type(value) is %s, value is %s', type(value),value)
    #logging.warning('type(xload) is %s, value is %s', type(xRPM),xRPM)

    return {
        'data': [
                    go.Scatter(
                        x=xRPM,
                        y=yTorque,
                        mode='lines',
                        line = dict(width = 5,color = 'rgb(200, 0, 0)'),
                        name='Torque curve',
                    ),
                    go.Scatter(
                        x=pxRPM,
                        y=pyTorque,
                        mode='markers',
                        #opacity=0.7,
                        marker = dict(
                        size = 10,
                        color = 'rgb(200, 0, 0)',
                        line = dict(width = 2,color = 'rgb(0, 0, 0)'),
                        ),
                        name='Torque data',
                        text=['','Locked Rotor','Pull up','Break Down','RATED','IDLE','']
                    ),
                    go.Scatter(
                        x=xRPM,
                        y=yCurrent,
                        mode='lines',
                        line=dict(width=5,color = 'rgb(0, 0, 200)'),
                        name='Current curve',
                        yaxis='y2',
                    ),
                    go.Scatter(
                        x=pxRPM,
                        y=pyCurrent,
                        mode='markers',
                        #opacity=0.7,
                        marker = dict(
                        size = 10,
                        color = 'rgb(0, 0, 200)',
                        line = dict(width = 2,color = 'rgb(0, 0, 0)'),
                        ),
                        name='Current data',
                        yaxis='y2',
                        text=['','Locked Rotor','Pull up','Break Down','RATED','IDLE','']
                    ),
                ],
                'layout': go.Layout(
                    title='Torque Speed curve',
                    xaxis=dict(
    #               type='line',
                    title='Speed - (RPM)',
                    showgrid=True,
                    #zeroline=True,
                    showline=True,
                    gridcolor='#bdbdbd',
                    mirror="ticks",
                    ticks="inside",
                    tickwidth=1,
                    linewidth=2,
                    range=[0,pxRPM.max()+pxRPM.max()/10]
                    ),
                    yaxis=dict(
                        title= 'Torque - (lb-ft)',
                        titlefont=dict( color='rgb(200, 0, 0)' ),
                        tickfont=dict( color='rgb(200, 0, 0)' ),
                        range=[0, pyTorque.max()+pyTorque.max()/10],
                        showgrid=True,
                        #zeroline=True,
                        showline=True,
                        gridcolor='#bdbdbd',
                        mirror="ticks",
                        ticks="inside",
                        tickwidth=1,
                        linewidth=2
                    ),
                    
                    yaxis2=dict(
                        title='Current - (Amps)',
                        titlefont=dict( color='rgb(0, 0, 200)' ),
                        tickfont=dict( color='rgb(0, 0, 200)' ),
                        anchor='x', #or 'x'
                        overlaying='y',
                        side='right',
                        range=[0, pyCurrent.max()+pyCurrent.max()/10],
                        showline=True,
                        showgrid=False,
                        mirror="ticks",
                        ticks="inside",
                        tickwidth=1,
                        linewidth=2
                    ),
                    margin={'l': 60, 'b': 40, 't': 30, 'r': 60},
                    #legend={'x': 0.5, 'y': 1},
                    hovermode='closest',
                    showlegend=False,
                )
        }

#calllback to update load efficiency graph
@app.callback(
    Output('load-efficiency','figure'),
    [Input('mtrid','value')]
)

def update_loadefficiency(value):
    row=index.get_loc(value)
    xload,pxload,yEff,pyEff,yCurrload,pyCurrload,yPF,pyPF = loadefficiency(row)
    #logging.warning('type(row) is %s, value is %s', type(row),row)
    #logging.warning('type(value) is %s, value is %s', type(value),value)
    #logging.warning('type(pyPF) is %s, value is %s', type(pyPF),pyPF)
    
    return {
            'data': [
                    go.Scatter(
                        x=xload,
                        y=yEff,
                        mode='lines',
                        line = dict(width = 5,color = 'rgb(200, 0, 0)'),
                        name='Efficiency curve',
                    ),
                    go.Scatter(
                        x=pxload[2:-1],
                        y=pyEff[2:-1],
                        mode='markers',
                        #opacity=0.7,
                        marker = dict(
                        size = 10,
                        color = 'rgb(200, 0, 0)',
                        line = dict(width = 2,color = 'rgb(0, 0, 0)'),
                        ),
                        name='Eff data',
                        #text=['','Locked Rotor','Pull up','Break Down','RATED','IDLE','']
                    ),
                    go.Scatter(
                        x=xload,
                        y=yCurrload,
                        mode='lines',
                        line=dict(width=5,color = 'rgb(0, 0, 200)'),
                        name='Current curve',
                        yaxis='y2',
                    ),
                    go.Scatter(
                        x=pxload,
                        y=pyCurrload,
                        mode='markers',
                        #opacity=0.7,
                        marker = dict(
                        size = 10,
                        color = 'rgb(0, 0, 200)',
                        line = dict(width = 2,color = 'rgb(0, 0, 0)'),
                        ),
                        name='Current data',
                        yaxis='y2',
                        #text=['','Locked Rotor','Pull up','Break Down','RATED','IDLE','']
                    ),
                    go.Scatter(
                        x=xload,
                        y=yPF,
                        mode='lines',
                        line=dict(width=5,color = 'rgb(200, 0, 0)',dash='dot'),
                        name='PF curve',
                        
                    ),
                    go.Scatter(
                        x=pxload,
                        y=pyPF,
                        mode='markers',
                        #opacity=0.7,
                        marker = dict(
                        size = 10,
                        color = 'rgb(200, 0, 0)',
                        line = dict(width = 2,color = 'rgb(0, 0, 0)'),
                        ),
                        name='PF data',
                        #text=['','Locked Rotor','Pull up','Break Down','RATED','IDLE','']
                    ),
                ],
                'layout': go.Layout(
                    title='Load Efficiency curve',
                    xaxis=dict(
        #               type='line',
                        title='Load - (%)',
                        showgrid=True,
                        #zeroline=True,
                        showline=True,
                        gridcolor='#bdbdbd',
                        mirror="ticks",
                        ticks="inside",
                        tickwidth=1,
                        linewidth=2,
                        range=[0,140],
                        dtick=10,
                    ),
                    yaxis=dict(
                        title= 'Efficiency (solid) & PF (dots) - (%)',
                        titlefont=dict( color='rgb(200, 0, 0)' ),
                        tickfont=dict( color='rgb(200, 0, 0)' ),
                        range=[0, 100],
                        showgrid=True,
                        #zeroline=True,
                        showline=True,
                        gridcolor='#bdbdbd',
                        mirror="ticks",
                        ticks="inside",
                        tickwidth=1,
                        linewidth=2,
                        dtick = 5,
                    ),
                    
                    yaxis2=dict(
                        title='Current - (Amps)',
                        titlefont=dict( color='rgb(0, 0, 200)' ),
                        tickfont=dict( color='rgb(0, 0, 200)' ),
                        anchor='x', #or 'x'
                        overlaying='y',
                        side='right',
                        range=[0, pyCurrload.max()+pyCurrload/10],
                        showline=True,
                        showgrid=False,
                        mirror="ticks",
                        ticks="inside",
                        tickwidth=1,
                        linewidth=2,
                        #dtick= 20,
                    ),
                    margin={'l': 60, 'b': 40, 't': 30, 'r': 60},
                    #legend={'x': 0.5, 'y': 1},
                    hovermode='closest',
                    showlegend=False
                )
            }

if __name__ == '__main__':
    app.run_server(debug=True)
