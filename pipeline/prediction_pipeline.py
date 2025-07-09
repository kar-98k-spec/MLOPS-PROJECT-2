from config.paths_config import *
from utils.helpers import *

def hybrid_recommendation(user_id, user_weight=0.5, content_weight=0.5):  ##user recommendation section
    sim_users = find_similair_users(user_id, USER_WEIGHTS_PATH, USER2USER_ENCODED, USER2USER_DECODED)  ### find similar users to user id
    user_prefs = get_user_preferences(user_id, DF, RATING_DF)  ### get user preferences for user id
    user_recommended_animes = get_user_recommendations(sim_users,user_prefs, DF, RATING_DF, SYNOPSIS_DF)  ### get user recommendations for user id

    user_recommended_anime_list = user_recommended_animes["anime_name"].tolist()  ### get anime names from user recommended animes

    ##content recommendation section
    content_recommended_animes = []  ### create empty list for content recommended animes

    for anime in user_recommended_anime_list:  ### loop through user recommended animes
        sim_animes = find_similair_animes(anime, ANIME_WEIGHTS_PATH, ANIME2ANIME_ENCODED, ANIME2ANIME_DECODED, DF)

        if sim_animes is not None and not sim_animes.empty:
            content_recommended_animes.extend(sim_animes["name"].tolist())  ### append anime names to content recommended animes
        else:
            print(f"No similar animes found {anime}")

    combined_scores = {}

    for anime in user_recommended_anime_list:
        combined_scores[anime] = combined_scores.get(anime, 0) + user_weight  ### get combined score for user recommended animes
    for anime in content_recommended_animes:
        combined_scores[anime] = combined_scores.get(anime, 0) + content_weight


    sorted_recommendations = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)  ### sort recommendations by score

    return [anime for anime , score in sorted_recommendations[:10]]  ### return sorted recommendations
