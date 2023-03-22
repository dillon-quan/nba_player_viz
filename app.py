import json

import dash
import dash_daq as daq
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dash_table, dcc, html
from dash.dependencies import Input, Output, State

from load_data import (get_player_id, get_season_stats, get_shot_chart_detail,
                       get_team_id)
from short_chart import draw_plotly_court

stat_cols = ['SEASON', 'GP', 'MIN', 'FG_PCT', 'FG3_PCT', 'FT_PCT', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'PF']

app = dash.Dash(__name__)
app.layout = html.Div(children=[
    # Store data requests from nba API
    dcc.Store(id='player-stat-info', storage_type='local'),
    dcc.Store(id='shot-chart-info', storage_type='local'),
    dcc.Store(id='league-avg-info', storage_type='local'),
    
    # app layout
    html.Div(children=[
        html.H1(children="NBA Player Analysis"),
        html.P(children="Summary of NBA player season stats"),
        html.Img(src="../assets/nba_logo.png"),
        html.Div(children=[
            html.Label(children="Player"),
            html.Div(children=[
                dcc.Input(id='player-search',
                          placeholder="stephen curry"),
                ]
            ),
            
            ]
        ),
        html.Div(children=[
                html.Button(children="Search", 
                            id="search-stats-button", 
                            n_clicks=0),
                html.Br()
        ]),
        html.Div(children=[
            daq.BooleanSwitch(id='post-season-switch', 
                on=False,
                label="Playoff",
                labelPosition="bottom")
        ])
    ], id='left-container'
    ),
    
    html.Div(children=[
        html.Div([
            html.H3(children="",
                    id='table-header'),
            html.Br(),
            dash_table.DataTable(id='season-stats',
                                columns=[{'name': i, 'id': i} for i in stat_cols]),
            ]
        ),
        html.Br(),
        html.Div(children=[
            dcc.Graph(id='shot-chart', figure={}),
            dcc.Graph(id='shot-type', figure={})
            ]
        ),
        ], id='righ-container'
    )
    ]
)

# nba_api data request
@app.callback(
    Output(component_id='player-stat-info', component_property='data'),
    Output(component_id='shot-chart-info', component_property='data'),
    Output(component_id='league-avg-info', component_property='data'),
    Input(component_id='search-stats-button', component_property='n_clicks'),
    State(component_id='player-search', component_property='value')
)
def get_player_data(n_clicks, player_name):
    if n_clicks:
        stats_df = get_season_stats(player_name=player_name)
        shot_charts, league_avgs = [], []
        for _, series in stats_df.iterrows():
            tmp_shot_df, tmp_league_avg_df = get_shot_chart_detail(series['PLAYER_ID'], series['TEAM_ID'], series['SEASON_ID'], series['SEASON_TYPE'])
            shot_charts.append(tmp_shot_df)
            league_avgs.append(tmp_league_avg_df)
        shot_chart_df = pd.concat(shot_charts)
        league_avg_df = pd.concat(league_avgs)
        
        return stats_df.to_json(orient='split'), shot_chart_df.to_json(orient='split'), league_avg_df.to_json(orient='split')
    return {}, {}, {}

# table header
@app.callback(
    Output(component_id='table-header', component_property='children'),
    Input(component_id='post-season-switch', component_property='on')
)
def table_header(value):
    if value:
        return 'Playoffs Season Stats'
    return 'Regular Season Stats'
        
# table api
@app.callback(
    Output(component_id='season-stats', component_property='data'),
    Input(component_id='player-stat-info', component_property='data'),
    Input(component_id='post-season-switch', component_property='on')
)
def display_reg_stats(json_str_data, post_flag):
    if isinstance(json_str_data, dict):
        return []

    season_type = 'Regular Season'
    jsonified_data = json.loads(json_str_data)
    stats_df = pd.DataFrame(data=jsonified_data['data'], index=jsonified_data['index'], columns=jsonified_data['columns'])
    if post_flag:
        season_type = 'Playoffs'
    filtered_stats_df = stats_df.loc[(stats_df.SEASON_TYPE == season_type)]
    filtered_stats_df = filtered_stats_df.rename(columns={'SEASON_ID': 'SEASON'}).drop(columns=['SEASON_TYPE'])
    return filtered_stats_df.to_dict('records')
    
    
@app.callback(
    Output(component_id='shot-chart', component_property='figure'),
    Input(component_id='shot-chart-info', component_property='data'),
    Input(component_id='post-season-switch', component_property='on')
)
def plot_shot_chart_data(json_str_data, post_flag):
    if isinstance(json_str_data, dict):
        return go.Figure()
    
    jsonified_data = json.loads(json_str_data)
    df = pd.DataFrame(data=jsonified_data['data'], index=jsonified_data['index'], columns=jsonified_data['columns'])
    
    season_type = 'Regular Season'
    title = f'{df.PLAYER_NAME.values[0]} Regular Seasons Shot Chart'
    if post_flag:
        title = f'{df.PLAYER_NAME.values[0]} Playoffs Shot Chart'
        season_type = 'Playoffs'
    
    missed_shot_trace = go.Scatter(
        x=df.loc[(df.SHOT_MADE_FLAG == 0) & (df.SEASON_TYPE == season_type)]['LOC_X'],
        y=df.loc[(df.SHOT_MADE_FLAG == 0) & (df.SEASON_TYPE == season_type)]['LOC_Y'],
        mode='markers',
        name='Miss',
        marker=dict(symbol='x', color='#DA2F12', opacity=0.5, size=5),
        text=df.loc[(df.SHOT_MADE_FLAG == 0) & (df.SEASON_TYPE == season_type)]['ACTION_TYPE'] + "<br>" +
            df.loc[(df.SHOT_MADE_FLAG == 0) & (df.SEASON_TYPE == season_type)]['SHOT_ZONE_RANGE']
        )

    made_shot_trace = go.Scatter(
        x=df.loc[(df.SHOT_MADE_FLAG == 1) & (df.SEASON_TYPE == season_type)]['LOC_X'],
        y=df.loc[(df.SHOT_MADE_FLAG == 1) & (df.SEASON_TYPE == season_type)]['LOC_Y'],
        mode='markers',
        name='Made',
        marker=dict(symbol='circle', color='#00CC86', opacity=0.5, size=5),
        text=df.loc[(df.SHOT_MADE_FLAG == 1) & (df.SEASON_TYPE == season_type)]['ACTION_TYPE'] + "<br>" +
            df.loc[(df.SHOT_MADE_FLAG == 1) & (df.SEASON_TYPE == season_type)]['SHOT_ZONE_RANGE']
        )
        
    layout = go.Layout(
        title=title,
        showlegend=True,
        xaxis={'showgrid':False, 'range':[-300, 300]},
        yaxis={'showgrid':False, 'range':[-100, 500]},
        height=600,
        width=650
        )
    
    fig = go.Figure(data=[missed_shot_trace, made_shot_trace], layout=layout)
    draw_plotly_court(fig, 600, margins=5)
    fig.update_layout(margin={'l': 0, 'b': 0, 't': 30, 'r': 0})
    return fig


if __name__ == '__main__':
    app.run_server(port="4000", debug=True)
