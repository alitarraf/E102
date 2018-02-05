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

#df_load = pd.read_csv('MotorLoadData.csv')

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

c_torque = CatmullRomChain(torque_xy)
c_current = CatmullRomChain(current_xy)

# coordinates point for curve catmullrom splines
xRPM, yTorque=zip(*c_torque)
xRPM, yCurrent=zip(*c_current)

#coordinates point for data point
pxRPM, pyTorque =zip(*torque_xy)
pxRPM, pyCurrent =zip(*current_xy)

#html layout
app.layout = html.Div([
    html.H1(
        children='E102',
        style={
            'textAlign': 'center',
            'color': colors['text']
        }
    ),
    dcc.Graph(
        id='speed-torque',
        figure={
            'data': [
                go.Scatter(
                    x=xRPM,
                    y=yTorque,
                    mode='lines',
                    name='Torque curve'
                ),
                go.Scatter(
                    x=pxRPM,
                    y=pyTorque,
                    mode='markers',
                    opacity=0.7,
                    marker={
                        'size': 15,
                        'line': {'width': 0.5, 'color': 'white'}
                    },
                    name='Torque data',
                    
                ),
                go.Scatter(
                    x=xRPM,
                    y=yCurrent,
                    mode='lines',
                    name='Current curve',
                    yaxis='y2',
                ),
                go.Scatter(
                    x=pxRPM,
                    y=pyCurrent,
                    mode='markers',
                    opacity=0.7,
                    marker={
                        'size': 15,
                        'line': {'width': 0.5, 'color': 'white'}
                    },
                    name='Current data',
                    yaxis='y2',
                ),
            ],
            'layout': go.Layout(
                xaxis={'type': 'line', 'title': 'Speed (RPM)'},
                yaxis={'title': 'Torque (lb-ft)'},
                margin={'l': 60, 'b': 40, 't': 10, 'r': 60},
                legend={'x': 0, 'y': 1},
                hovermode='closest',
                
                yaxis2=dict(
                title='Current (Amps)',
                titlefont=dict( color='rgb(148, 103, 189)' ),
                tickfont=dict( color='rgb(148, 103, 189)' ),
                anchor='free', #or 'x'
                overlaying='y',
                side='right'
                )
            )
        }
    )
])

if __name__ == '__main__':
    app.run_server()