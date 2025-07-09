import pandas as pd
import numpy as np
import joblib
from config.paths_config import *

## 1.get_anime_frame
# This function retrieves a DataFrame row corresponding to a specific anime.
def get_anime_frame(anime,path_df):
    df = pd.read_csv(path_df)
    if isinstance(anime, int):
        return df[df.anime_id == anime]
    if isinstance(anime, str):
        return df[df.eng_version == anime]
    
## 2.get_synopsis
# This function retrieves the synopsis of an anime based on its ID or name.
def get_synopsis(anime, path_synopsis_df):  ### function to get synopsis from anime id
    synopsis_df = pd.read_csv(path_synopsis_df)  ### read the synopsis dataframe
    if isinstance(anime, int):
        return synopsis_df[synopsis_df.MAL_ID == anime].sypnopsis.values[0]  ### get synopsis from anime id
    if isinstance(anime, str):
        return synopsis_df[synopsis_df.Name == anime].sypnopsis.values[0]  ### get synopsis from anime name
    return None  ### if anime not found, return null

##3.content recommendations
###

def find_similair_animes(name, path_anime_weights, path_anime2anime_encoded, path_anime2anime_decoded, path_df, n=10, return_dist=False, neg=False):
    
    anime_weights = joblib.load(path_anime_weights)  ### load anime weights from file
    anime2anime_encoded = joblib.load(path_anime2anime_encoded)  ### load encoded anime ids from file
    anime2anime_decoded = joblib.load(path_anime2anime_decoded)


    try:
       index = get_anime_frame(name, path_df).anime_id.values[0]  ### get anime id from anime name
       encoded_index = anime2anime_encoded.get(index)  ### get encoded anime id from anime id

       weights = anime_weights

       dists = np.dot(weights, weights[encoded_index])  ### calculate distance between anime weights and encoded anime id
       sorted_dists = np.argsort(dists)

       n=n+1

       if neg:
            closest = sorted_dists[:n]  ### get closest anime ids
       else:
            closest = sorted_dists[-n:]
            

       if return_dist:
          return dists, closest
       
       SimilarityArr = []

       for close in closest:
           decoded_id = anime2anime_decoded.get(close)  ### get decoded anime id from encoded anime id

           anime_frame = get_anime_frame(decoded_id, path_df)

           anime_name = anime_frame.eng_version.values[0]  ### get anime name from anime id
           genre = anime_frame.Genres.values[0]  ### get anime genre from anime id
           similarity = dists[close]

           SimilarityArr.append({
                "anime_id": decoded_id,
                "name": anime_name,
                "similarity": similarity,
                "genre": genre
           })
           

       Frame = pd.DataFrame(SimilarityArr).sort_values(by="similarity", ascending=False)  ### create dataframe from similarity array
       return Frame[Frame.anime_id != index].drop(["anime_id"], axis=1)  ### return dataframe without the original anime id
       
    except:
        print("Error:Anime not found")


## 4. find similair users

###These funstions are just to find similar users to a given user###

def find_similair_users(item_input , path_user_weights , path_user2user_encoded , path_user2user_decoded , n=10, return_dist=False, neg=False):


    user_weights = joblib.load(path_user_weights)  ### load user weights from file
    user2user_encoded = joblib.load(path_user2user_encoded)  ### load encoded user ids from file
    user2user_decoded = joblib.load(path_user2user_decoded)  ### load decoded user ids from file


    try:
        index = item_input
        encoded_index = user2user_encoded.get(index)  ### get encoded user id from user id
        
        weights = user_weights

        dists = np.dot(weights, weights[encoded_index])  ### calculate distance between user weights and encoded user id
        sorted_dists = np.argsort(dists)

        n=n+1
        if neg:
            closest = sorted_dists[:n]  ### get closest user ids
        else:
            closest = sorted_dists[-n:]
        
        if return_dist:
            return dists, closest
        
        SimilarityArr = []

        for close in closest:
            similarity = dists[close]  ### get similarity from distance array

            if isinstance(item_input, int):
                decoded_id = user2user_decoded.get(close)
                SimilarityArr.append({
                    "similair_users": decoded_id,
                    "similarity": similarity
                })

        similair_users = pd.DataFrame(SimilarityArr).sort_values(by="similarity", ascending=False)  ### create dataframe from similarity array
        similair_users = similair_users[similair_users.similair_users != index]  ### remove original user id from dataframe
        return similair_users  ### return dataframe without the original user id
    
    except Exception as e:
        print("Error:", e)  ### print error message



##5. get user preferences
### find user preferences for a specific user ####

def get_user_preferences(user_id, path_df, path_rating_df, plot=False):

    rating_df = pd.read_csv(path_rating_df)  ### read the rating dataframe
    df = pd.read_csv(path_df)  ### read the anime dataframe

    animes_watched_by_user = rating_df[rating_df.user_id == user_id]  ### get animes watched by user

    user_rating_percentile = np.percentile(animes_watched_by_user.rating , 75)  ### get top 75th percentile rated anime by user

    animes_watched_by_user = animes_watched_by_user[animes_watched_by_user.rating >= user_rating_percentile]  ### filter animes watched by user by rating

    top_animes_by_user = (
        animes_watched_by_user.sort_values(by="rating", ascending=False).anime_id.values
    )

    anime_df_rows = df[df["anime_id"].isin(top_animes_by_user)]  ### get anime dataframe rows for top animes watched by user 
    anime_df_rows = anime_df_rows[["anime_id", "eng_version", "Genres"]]  ### select only anime_id, eng_version and Genres columns


    return anime_df_rows  ### return dataframe of top animes watched by user




##6. get user recomendations
### beginning actual user based recommendation functions ###

def get_user_recommendations(similair_users, user_pref, path_df, path_rating_df, path_synopsis_df, n=10):


    recommended_animes = []  ### create empty list for recommended animes
    anime_list = []  ### create empty list for anime ids

    for user_id in similair_users.similair_users.values:  ### loop through similar users
        pref_list = get_user_preferences(int(user_id), path_df, path_rating_df)  ### get user preferences for similar user

        pref_list = pref_list[~pref_list.eng_version.isin(user_pref.eng_version.values)]  ### remove animes that the user has already watched from similar user preferences

        if not pref_list.empty:
            anime_list.append(pref_list.eng_version.values)  ### append anime names to anime list
        
    if anime_list:
            anime_list = pd.DataFrame(anime_list)  ### convert anime list to dataframe

            sorted_list = pd.DataFrame(pd.Series(anime_list.values.ravel()).value_counts()).head(n)  ##ravel flattens results to 1d array

            for i,anime_name in enumerate(sorted_list.index):
                n_user_pref = sorted_list[sorted_list.index == anime_name].values[0][0]

                if isinstance(anime_name, str):
                    frame = get_anime_frame(anime_name, path_df)  ### get anime frame from anime name
                    anime_id = frame.anime_id.values[0]  ### get anime id from anime frame
                    genre = frame.Genres.values[0]  ### get genre from anime frame
                    synopsis = get_synopsis(int(anime_id), path_synopsis_df)  ### get synopsis from anime id

                    recommended_animes.append({
                        "n": n_user_pref,
                        "anime_name": anime_name,                   
                        "synopsis": synopsis,
                        "genre": genre
                    })
    
    return pd.DataFrame(recommended_animes).head(n)  ### return dataframe of recommended animes




