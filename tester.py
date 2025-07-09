from utils.helpers import *
from config.paths_config import *
from pipeline.prediction_pipeline import hybrid_recommendation

#sim_users = find_similair_users(11880, USER_WEIGHTS_PATH, USER2USER_ENCODED, USER2USER_DECODED)
#print(sim_users)
#user_prefs = get_user_preferences(11880, DF, RATING_DF)
#print(user_prefs)

rec = hybrid_recommendation(11880)
print(rec)