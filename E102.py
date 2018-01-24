import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import pandas as pd

app = dash.Dash()

colors = {
    'background': '#111111',
    'text': '#000000'
}

df_speed = pd.read_csv(
    'MotorSpeedData.csv')

df_load = pd.read_csv(
    'MotorLoadData.csv')


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
                    x=df_speed['RPM'],
                    y=df_speed['Torque'],
                    mode='markers',
                    opacity=0.7,
                    marker={
                        'size': 15,
                        'line': {'width': 0.5, 'color': 'white'}
                    },
                ),
                go.Scatter(
                    x=df_speed['RPM'],
                    y=df_speed['Current'],
                    mode='markers',
                    opacity=0.7,
                    marker={
                        'size': 15,
                        'line': {'width': 0.5, 'color': 'white'}
                    },
                    name='yaxis2 data',
                    yaxis='y2' 
                ),
            ],
            'layout': go.Layout(
                xaxis={'type': 'line', 'title': 'Speed (RPM)'},
                yaxis={'title': 'Torque (lb-ft)'},
                margin={'l': 40, 'b': 40, 't': 10, 'r': 40},
                legend={'x': 0, 'y': 1},
                hovermode='closest',
                yaxis2=dict(
                title='yaxis2 title',
                titlefont=dict(
                color='rgb(148, 103, 189)'
                ),
                tickfont=dict(
                color='rgb(148, 103, 189)'
                ),
                overlaying='y',
                side='right'
                )
            )
        }
    )
])

if __name__ == '__main__':
    app.run_server()