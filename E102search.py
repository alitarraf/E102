__author__='ali.tarraf@gmail.com'

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table_experiments as dt
import json
import pandas as pd
import numpy as np
import plotly
import logging
from scipy.interpolate import spline,interp1d
from catmullrom import CatmullRomChain

app = dash.Dash()

app.scripts.config.serve_locally = True
# app.css.config.serve_locally = True

#DF_WALMART = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/1962_2006_walmart_store_openings.csv')

# DF_GAPMINDER = pd.read_csv(
#     'https://raw.githubusercontent.com/plotly/datasets/master/gapminderDataFiveYear.csv'
# )
# DF_GAPMINDER = DF_GAPMINDER[DF_GAPMINDER['year'] == 2007]
# DF_GAPMINDER.loc[0:20]

# DF_SIMPLE = pd.DataFrame({
#     'x': ['A', 'B', 'C', 'D', 'E', 'F'],
#     'y': [4, 3, 1, 2, 3, 6],
#     'z': ['a', 'b', 'c', 'a', 'b', 'c']
# })

# ROWS = [
#     {'a': 'AA', 'b': 1},
#     {'a': 'AB', 'b': 2},
#     {'a': 'BB', 'b': 3},
#     {'a': 'BC', 'b': 4},
#     {'a': 'CC', 'b': 5},
#     {'a': 'CD', 'b': 6}
# ]

DF_GAPMINDER = pd.read_csv('searchDb.csv')# search table database
d=pd.read_pickle('perfdb.pkl') # performance curves serialised database in pickle file
row=1000
index=pd.Index(d['APP_WDG'])


#################################
#functions for performance curves
##################################
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

####################################
####################################

app.layout = html.Div([
    html.H4('SEARCH WINDING & PERFORMANCE CURVES WEBPAGE'),
    dt.DataTable(
        rows=DF_GAPMINDER.to_dict('records'),

        # optional - sets the order of columns
        columns=sorted(DF_GAPMINDER.columns),

        row_selectable=True,
        filterable=True,
        sortable=True,
        selected_row_indices=[],
        id='datatable-gapminder'
    ),
    html.Div(id='selected-indexes'),
    dcc.Graph(
        id='graph-gapminder'
    ),
], className="container")


@app.callback(
    Output('datatable-gapminder', 'selected_row_indices'),
    [Input('graph-gapminder', 'clickData')],
    [State('datatable-gapminder', 'selected_row_indices')])
def update_selected_row_indices(clickData, selected_row_indices):
    if clickData:
        for point in clickData['points']:
            if point['pointNumber'] in selected_row_indices:
                selected_row_indices.remove(point['pointNumber'])
            else:
                selected_row_indices.append(point['pointNumber'])
    return selected_row_indices


@app.callback(
    Output('graph-gapminder', 'figure'),
    [Input('datatable-gapminder', 'rows'),
     Input('datatable-gapminder', 'selected_row_indices')])

def update_figure(rows, selected_row_indices):

    dff = pd.DataFrame(rows)
    fig = plotly.tools.make_subplots(
        rows=1, cols=2,
        subplot_titles=('Torque-speed', 'Load-efficiency'),
        shared_xaxes=False)
    marker = {'color': ['#0074D9']*len(dff)}
    # for i in (selected_row_indices or []):
    #     marker['color'][i] = '#FF851B'

    value=dff['WINDING'][selected_row_indices[0]]
    row=index.get_loc(value)
    
    xRPM,pxRPM,yTorque,pyTorque,yCurrent,pyCurrent = torquespeed(row)
    xload,pxload,yEff,pyEff,yCurrload,pyCurrload,yPF,pyPF = loadefficiency(row)

    ##################################
    ##Sub Fig 1 Torque Speed
    ##################################
   

    trace10 = dict(type='scatter',
                        x=xRPM,
                        y=yTorque,
                        mode='lines',
                        line = dict(width = 5,color = 'rgb(200, 0, 0)'),
                        name='Torque curve'
                        )
    trace11 = dict(type='scatter',
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
                        text=['','Locked Rotor','Pull up','Break Down','RATED','IDLE',''],
                        )
    trace12 = dict(type='scatter',
                        x=xRPM,
                        y=yCurrent,
                        mode='lines',
                        line=dict(width=5,color = 'rgb(0, 0, 200)'),
                        name='Current curve',
                        )
    trace13 = dict(type='scatter',
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
                        text=['','Locked Rotor','Pull up','Break Down','RATED','IDLE',''],
                    )
    
    ##################################3
    ##Sub Fig 2 load efficiency
    ##################################

    trace20 = dict(type='scatter',
                        x=xload,
                        y=yEff,
                        mode='lines',
                        line = dict(width = 5,color = 'rgb(200, 0, 0)'),
                        name='Efficiency curve',)
    trace21 = dict(type='scatter',
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
                        text=['','Locked Rotor','Pull up','Break Down','RATED','IDLE',''])
    trace22 = dict(type='scatter',
                        x=xload,
                        y=yCurrload,
                        mode='lines',
                        line=dict(width=5,color = 'rgb(0, 0, 200)'),
                        name='Current curve',
                        )
    trace23 = dict(type='scatter',
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
                        text=['','Locked Rotor','Pull up','Break Down','RATED','IDLE',''],
                        )
    trace24 = dict(type='scatter',
                        x=xload,
                        y=yPF,
                        mode='lines',
                        line=dict(width=5,color = 'rgb(200, 0, 0)',dash='dot'),
                        name='PF curve')
    trace25 = dict(type='scatter',
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
                        text=['','Locked Rotor','Pull up','Break Down','RATED','IDLE','']
                    )

    #traces of subplot 1
    fig.append_trace(trace10, 1, 1) #data[0]---x1,y1
    fig.append_trace(trace11, 1, 1) #data[1]---x1,y1
    fig.append_trace(trace12, 1, 1) #data[2]---x1,y3
    fig.append_trace(trace13, 1, 1) #data[3]---x1,y3
    
    #traces of subplot 2
    fig.append_trace(trace20, 1, 2) #data[4]---x2,y2
    fig.append_trace(trace21, 1, 2) #data[5]---x2,y2
    fig.append_trace(trace22, 1, 2) #data[6]---x2,y4
    fig.append_trace(trace23, 1, 2) #data[7]---x2,y4
    fig.append_trace(trace24, 1, 2) #data[8]---x2,y2
    fig.append_trace(trace25, 1, 2) #data[9]---x2,y2

    #Assigning subplot y axis as per data above...default is x1,y1,y3 and x2,y2,y4 for each left and right subplot
    fig['data'][2].update(yaxis='y3')
    fig['data'][3].update(yaxis='y3')
    fig['data'][6].update(yaxis='y4')
    fig['data'][7].update(yaxis='y4')

    #logging.warning('name data[6] value is %s',fig['data'][6]['name'])
    #logging.warning('xaxis data[6] value is %s',fig['data'][6]['xaxis'])
    #logging.warning('yaxis data[6] value is %s',fig['data'][6]['yaxis'])

    #layout for subplot 1
    fig['layout']['xaxis1'].update(
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
    )
    fig['layout']['yaxis1'].update(
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
    )

    fig['layout']['yaxis3'].update(
                    title='Current - (Amps)',
                    titlefont=dict( color='rgb(0, 0, 200)' ),
                    tickfont=dict( color='rgb(0, 0, 200)' ),
                    anchor='x1', #or 'x'
                    overlaying='y1',
                    side='right',
                    range=[0, pyCurrent.max()+pyCurrent.max()/10],
                    showline=True,
                    showgrid=False,
                    mirror="ticks",
                    ticks="inside",
                    tickwidth=1,
                    linewidth=2
    )

    # layout for subplot 2

    fig['layout']['xaxis2'].update(
                        type='line',
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
                    )
    fig['layout']['yaxis2'].update(
                        title= 'Efficiency (solid) & PF (dots) - (%)',
                        titlefont=dict( color='rgb(200, 0, 0)' ),
                        tickfont=dict( color='rgb(200, 0, 0)' ),
                        range=[0, 100],
                        #anchor='x2', #or 'x'
                        #overlaying='y2',
                        showgrid=True,
                        #zeroline=True,
                        showline=True,
                        gridcolor='#bdbdbd',
                        mirror="ticks",
                        ticks="inside",
                        tickwidth=1,
                        linewidth=2,
                        dtick = 5,
                    )
    fig['layout']['yaxis4'].update(
                        title='Current - (Amps)',
                        titlefont=dict( color='rgb(0, 0, 200)' ),
                        tickfont=dict( color='rgb(0, 0, 200)' ),
                        anchor='x2', #or 'x'
                        overlaying='y2',
                        side='right',
                        range=[0, pyCurrload.max()+pyCurrload/10],
                        showline=True,
                        showgrid=False,
                        mirror="ticks",
                        ticks="inside",
                        tickwidth=1,
                        linewidth=2,
                        #dtick= 20,
                    )
    
    fig['layout']['showlegend'] = False
    fig['layout']['height'] = 600
    fig['layout']['margin'] = {
        'l': 40,
        'r': 40,
        't': 60,
        'b': 100
    }
    #fig['layout']['yaxis3']['type'] = 'log'
    
    #logging.warning('type(selected row) is %s, value is %s', type(selected_row_indices),selected_row_indices)
    #logging.warning('type(dff) is %s, value is %s', type(dff['WINDING'][selected_row_indices[0]]),dff['WINDING'][selected_row_indices[0]] )
    #logging.warning('Fig(layout) value is %s', fig['layout'])
    #logging.warning('Fig(data) value is %s', fig['data'])
     
    
 
    return fig


app.css.append_css({
    'external_url': 'https://codepen.io/alitarraf/pen/bvxdOY.css'
})

if __name__ == '__main__':
    app.run_server(debug=True)


#try app wdg T3654213