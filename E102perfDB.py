import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import pandas as pd
import numpy as np
from scipy.interpolate import spline,interp1d
from catmullrom import CatmullRomChain
#from catmullrom import CatmullRomSpline

app = dash.Dash()

colors = {
    'background': '#111111',
    'text': '#000000'
}

#loading data from two csv file
df_speed = pd.read_csv('MotorSpeedData.csv')
df_load = pd.read_csv('MotorLoadData.csv')

#MotorSpeedData extraction and array manipulation
#Array adding points @ start & end to manipulate 
#curve slope. Those are point P1, P4 as per catmull-rom
rpmArray = np.array(df_speed['RPM'])
rpmArray = np.insert(rpmArray,0,0) # adding 0 to start of array
rpmArray = np.append(rpmArray,rpmArray.max()) #adding max rpm to end of array

torqueArray = np.array(df_speed['Torque'])
torqueArray = np.insert(torqueArray,0,torqueArray[0]+1)
torqueArray = np.append(torqueArray,torqueArray[-1]-1)

currentArray=np.array(df_speed['Current'])  
currentArray = np.insert(currentArray,0,currentArray[0]+1)
currentArray = np.append(currentArray,currentArray[-1]-1)

torque_xy=np.column_stack((rpmArray,torqueArray))
current_xy=np.column_stack((rpmArray,currentArray))
#print rpmArray,torqueArray,torque_xy,current_xy

#MotorLoadData extraction and array manipulation
loadArray = np.array(df_load['Load'])
loadArray = np.insert(loadArray,0,0) # adding 0 to start of array
loadArray = np.append(loadArray,loadArray.max()) #adding max load to end of array

effArray = np.array(df_load['Eff'])
effArray = np.insert(effArray,1,effArray[1]-0.01)
effArray = np.append(effArray,effArray[-1]+0.01)

pfArray = np.array(df_load['PF'])
pfArray = np.insert(pfArray,0,pfArray[0]-0.01)
pfArray = np.append(pfArray,pfArray[-1]+0.01)

currloadArray = np.array(df_load['Current'])
currloadArray = np.insert(currloadArray,0,currloadArray[0]-0.01)
currloadArray = np.append(currloadArray,currloadArray[-1]+0.01)

eff_xy=np.column_stack((loadArray,effArray))
pf_xy=np.column_stack((loadArray,pfArray))
currload_xy=np.column_stack((loadArray,currloadArray))
print loadArray,effArray,eff_xy,pf_xy

#creating splines using catmullrom algorithm
c_torque = CatmullRomChain(torque_xy)
c_current = CatmullRomChain(current_xy)
c_eff = CatmullRomChain(eff_xy)
c_pf = CatmullRomChain(pf_xy)
c_currload = CatmullRomChain(currload_xy)

# coordinates point for curve catmullrom splines
xRPM, yTorque = zip(*c_torque)
xRPM, yCurrent = zip(*c_current)
xload, yEff = zip(*c_eff)
xload, yPF = zip(*c_pf)
xload, yCurrload = zip(*c_currload)

#coordinates point for data point
pxRPM, pyTorque = zip(*torque_xy)
pxRPM, pyCurrent = zip(*current_xy)
pxload, pyEff = zip(*eff_xy)
pxload, pyPF = zip(*pf_xy)
pxload, pyCurrload = zip(*currload_xy)

#html layout
app.layout = html.Div([
    html.H1(
        children='E102',
        style={
            'textAlign': 'center',
            'color': colors['text']
        }
    ),
    html.Div(
        dcc.Graph(
            id='speed-torque',
            figure={
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
                    range=[0,1300]
                    ),
                    yaxis=dict(
                        title= 'Torque - (lb-ft)',
                        titlefont=dict( color='rgb(200, 0, 0)' ),
                        tickfont=dict( color='rgb(200, 0, 0)' ),
                        range=[0, 1600],
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
                        range=[0, 1200],
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
            },
            style={'width':'600','height':'500'}
        ),
        style={'display':'inline-block'}
    ),

    html.Div(
        dcc.Graph(
            id='load-efficiency',
            figure={
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
                        range=[0, 200],
                        showline=True,
                        showgrid=False,
                        mirror="ticks",
                        ticks="inside",
                        tickwidth=1,
                        linewidth=2,
                        dtick= 20,
                    ),
                    margin={'l': 60, 'b': 40, 't': 30, 'r': 60},
                    #legend={'x': 0.5, 'y': 1},
                    hovermode='closest',
                    
                    showlegend=False,
                )
            },
            style={'width':'600','height':'500'}
        ),
        style={'display':'inline-block'}  
    ),
],
style={'width': '60%', 'display': 'inline-block'}
)

if __name__ == '__main__':
    app.run_server()