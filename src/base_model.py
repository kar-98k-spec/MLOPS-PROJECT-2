from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Embedding, Dot, Flatten, Dense, Activation, BatchNormalization
from utils.common_functions import read_yaml
from src.logger import get_logger
from src.custom_exception import CustomException

logger = get_logger(__name__)

class BaseModel:
    def __init__(self,config_path):
        try:
            self.config = read_yaml(config_path)
            logger.info("Model configuration loaded successfully from config.yaml")
        except Exception as e:
            raise CustomException("Failed to load model configuration", e)
        
    
    def RecommenderNet(self, n_users, n_anime):

        try:
            embedding_size = self.config["model"]["embedding_size"]  ### embedding size for user and anime

            user_input = Input(name="user" , shape=[1])  ### input layer for user

            user_embedding = Embedding(name="user_embedding", input_dim=n_users, output_dim=embedding_size)(user_input)  ### embedding layer for user

            anime_input = Input(name="anime" , shape=[1])  ### input layer for anime

            anime_embedding = Embedding(name="anime_embedding", input_dim=n_anime, output_dim=embedding_size)(anime_input)  ### embedding layer for anime

            x = Dot(name="dot_product", normalize=True, axes=2)([user_embedding, anime_embedding])  ### dot product of user and anime embeddings, calculates similarity between user and anime

            x = Flatten()(x)  ### flatten the output of the dot product

            x = Dense(1, kernel_initializer='he_normal')(x)  ### dense layer
            x = BatchNormalization()(x)  ### batch normalization
            x = Activation("sigmoid")(x)  ### activation function

            model = Model([user_input, anime_input], outputs=x)  ### create the model

            model.compile(
                loss = self.config["model"]["loss"],  ### loss function
                optimizer = self.config["model"]["optimizer"],  ### optimizer
                metrics = self.config["model"]["metrics"]  ### metrics
            )
            logger.info("Model compiled successfully")
            return model  ### return the model
        
        except Exception as e:
            logger.error(f"Error in creating the model: {e}")
            raise CustomException("Failed to create the model", e)
        
    
