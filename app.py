import dash
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dash_table, dcc, html
from dash.dependencies import Input, Output, State

from load_data import (get_player_id, get_regular_season_stats,
                       get_shot_chart_detail, get_team_id)
from short_chart import draw_plotly_court

stat_cols = ['SEASON', 'GP', 'MIN', 'FG_PCT', 'FG3_PCT', 'FT_PCT', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'PF']

app = dash.Dash(__name__)
app.layout = html.Div(children=[
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
            html.Label(children="Team"),
            html.Div(children=[
                dcc.Input(id='team-search',
                          placeholder="golden state warriors / gsw"),
                ]
            ),
            ]
        ),
        html.Div(children=[
            html.Label(children="Season"),
            html.Div(children=[
                dcc.Input(id='season-search',
                          placeholder="Optional 2022-23"),
                ]
            ),
            ]
        ),
        html.Button(children="Search", 
                    id="search-stats-button", 
                    n_clicks=0)
        ], id='left_container'
    ),
    
    html.Div(children=[
        html.Div([
            html.H3(children="Regular Season Stats"),
            html.Br(),
            dash_table.DataTable(id='reg-season-stats',
                                columns=[{'name': i, 'id': i} for i in stat_cols]),
            ]
        ),
        html.Br(),
        html.Div(children=[
            dcc.Graph(id='shot-chart', figure={})
            # dcc.Graph(id='shot-type', figure={})
            ]
        ),
        ]
    )
    ]
)


@app.callback(
    Output(component_id='reg-season-stats', component_property='data'),
    Input(component_id='search-stats-button', component_property='n_clicks'),
    State(component_id='team-search', component_property='value'),
    State(component_id='player-search', component_property='value'),
    State(component_id='season-search', component_property='value')
)
def display_reg_stats(n_clicks, team_name, player_name, season):
    agg_cols = ['GP', 'MIN', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS']
    display_cols = ['SEASON_ID', 'GP', 'FG_PCT', 'FG3_PCT', 'FT_PCT']
    if n_clicks:
        stats_df = get_regular_season_stats(player_name)
        team_id = get_team_id(team_name)
        condition = (stats_df.TEAM_ID == team_id)
        if season:
            condition = (stats_df.TEAM_ID == team_id) & (stats_df.SEASON_ID == season)
        stats_df = stats_df.loc[condition]
        div = stats_df.loc[:, agg_cols].div(stats_df['GP'], axis=0).round(1).drop(columns=['GP'])
        stats_table = pd.concat([stats_df[display_cols], div], axis=1)
        stats_table = stats_table.rename(columns={'SEASON_ID': 'SEASON'})
        return stats_table.to_dict('records')
    
    
@app.callback(
    Output(component_id='shot-chart', component_property='figure'),
    Input(component_id='search-stats-button', component_property='n_clicks'),
    State(component_id='team-search', component_property='value'),
    State(component_id='player-search', component_property='value'),
    State(component_id='season-search', component_property='value')
)
def plot_shot_chart_data(n_clicks, team_name, player_name, season):
    if n_clicks:
        player_id = get_player_id(player_name=player_name)
        team_id = get_team_id(team_name=team_name)
        # All Seasons (No input to season)
        if not season:
            stats_df = get_regular_season_stats(player_name)
            shot_charts = []
            for season in stats_df['SEASON_ID'].values:
                tmp_df = get_shot_chart_detail(player_id=player_id, team_id=team_id, season=season)
                tmp_df['season'] = season
                shot_charts.append(tmp_df)
            df = pd.concat(shot_charts)
            miss_condition = (df.SHOT_MADE_FLAG == 0)
            made_condition = (df.SHOT_MADE_FLAG == 1)
            title = f'{df.PLAYER_NAME.values[0]} Career Shot Chart'
        # input for a single season
        else:
            df = get_shot_chart_detail(player_id=player_id, team_id=team_id, season=season)
            df['season'] = season
            miss_condition = (df.SHOT_MADE_FLAG == 0) & (df.season == season)
            made_condition = (df.SHOT_MADE_FLAG == 1) & (df.season == season)
            title = f'{df.PLAYER_NAME.values[0]} Shot Chart {season}'
            
        
        missed_shot_trace = go.Scatter(
            x=df.loc[miss_condition]['LOC_X'],
            y=df.loc[miss_condition]['LOC_Y'],
            mode='markers',
            name='Miss',
            marker={'color':'red', 'size':5},
            text=df.loc[miss_condition]['ACTION_TYPE'] + "<br>" +
                df.loc[miss_condition]['SHOT_ZONE_RANGE']
            )

        made_shot_trace = go.Scatter(
            x=df.loc[made_condition]['LOC_X'],
            y=df.loc[made_condition]['LOC_Y'],
            mode='markers',
            name='Made',
            marker={'color':'green', 'size':5},
            text=df.loc[made_condition]['ACTION_TYPE'] + "<br>" +
                df.loc[made_condition]['SHOT_ZONE_RANGE']
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
    return go.Figure()


if __name__ == '__main__':
    app.run_server(port="4000", debug=True)
