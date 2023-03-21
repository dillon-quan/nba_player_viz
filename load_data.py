import pandas as pd
from nba_api.stats.endpoints import playercareerstats, shotchartdetail
from nba_api.stats.static import players, teams


def get_player_id(player_name):
    players_df = pd.DataFrame(players.get_players())
    return players_df.loc[(players_df.full_name.str.contains(player_name, regex=True, case=False)), 'id'].values[0]

def get_team_id(team_name):
    teams_df = pd.DataFrame(teams.get_teams())
    if len(team_name) <= 3:
        return teams_df.loc[(teams_df.abbreviation == team_name.upper()), 'id'].values[0]
    return teams_df.loc[(teams_df.full_name.str.contains(team_name, regex=True, case=False)), 'id'].values[0]

def get_regular_season_stats(player_name):
    player_id = get_player_id(player_name)
    stats_df = playercareerstats.PlayerCareerStats(player_id=player_id).get_data_frames()[0]
    return stats_df

def get_shot_chart_detail(player_id, team_id, season):
    shot_chart_df = shotchartdetail.ShotChartDetail(team_id=team_id, 
                                                    player_id=player_id, 
                                                    season_type_all_star='Regular Season', 
                                                    context_measure_simple='FGA',
                                                    season_nullable=season).get_data_frames()[0]
    return shot_chart_df



    