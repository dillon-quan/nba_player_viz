import pandas as pd
from nba_api.stats.endpoints import (commonplayerinfo, playercareerstats,
                                     shotchartdetail)
from nba_api.stats.static import players, teams


def get_player_id(player_name):
    players_df = pd.DataFrame(players.get_players())
    return players_df.loc[(players_df.full_name.str.contains(player_name, regex=True, case=False)), 'id'].values[0]

def get_team_id(team_name):
    teams_df = pd.DataFrame(teams.get_teams())
    if len(team_name) <= 3:
        return teams_df.loc[(teams_df.abbreviation == team_name.upper()), 'id'].values[0]
    return teams_df.loc[(teams_df.full_name.str.contains(team_name, regex=True, case=False)), 'id'].values[0]

def get_player_detail(player_id):
    detail_df = commonplayerinfo.CommonPlayerInfo(player_id=player_id).get_data_frames()[0]
    detail_df['BIRTHDATE'] = detail_df['BIRTHDATE'].str.split('T')[0][0]
    return detail_df

def get_season_stats(player_name):
    player_id = get_player_id(player_name)
    stats_df = playercareerstats.PlayerCareerStats(player_id=player_id, 
                                                   per_mode36='PerGame').get_data_frames()
    reg_season_df = stats_df[0]
    reg_season_df['SEASON_TYPE'] = 'Regular Season'
    post_season_df = stats_df[2]
    post_season_df['SEASON_TYPE'] = 'Playoffs'
    df = pd.concat([reg_season_df, post_season_df])
    return df

def get_shot_chart_detail(player_id, team_id, season_id, season_type):
    shot_chart_dfs = shotchartdetail.ShotChartDetail(team_id=team_id, 
                                                    player_id=player_id, 
                                                    season_type_all_star=season_type, 
                                                    context_measure_simple='FGA',
                                                    season_nullable=season_id).get_data_frames()
    player_shot_df = shot_chart_dfs[0]
    league_avg_df = shot_chart_dfs[1]
    player_shot_df['SEASON_ID'] = season_id
    player_shot_df['SEASON_TYPE'] = season_type
    league_avg_df['SEASON_ID'] = season_id
    league_avg_df['SEASON_Type'] = season_type
    return player_shot_df, league_avg_df



    