import joblib
import comet_ml
import numpy as np
import os
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, LearningRateScheduler, TensorBoard
from src.logger import get_logger
from src.custom_exception import CustomException
from src.base_model import BaseModel
from config.paths_config import *

logger = get_logger(__name__)

class ModelTraining:
    def __init__(self,data_path):
        self.data_path = data_path
        ## Initialize Comet-ML experiment
        self.experiment = comet_ml.Experiment(
            api_key = "shG9Bw9g5G9Ex36lMBNyUU6Ec",
            project_name = "mlops-project-2",
            workspace="kar-98k-spec"
        )
        logger.info("Model training & Comet-ML initialized")

    def load_data(self):
        try:
            X_train_array = joblib.load(X_TRAIN_ARRAY)
            X_test_array = joblib.load(X_TEST_ARRAY)
            y_train = joblib.load(Y_TRAIN)
            y_test = joblib.load(Y_TEST)

            logger.info("Data loaded successfully")
            return X_train_array, X_test_array, y_train, y_test
        
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise CustomException("Failed to load data", e)
        
    
    def train_model(self):
        try:
            X_train_array, X_test_array, y_train, y_test = self.load_data()

            n_users = len(joblib.load(USER2USER_ENCODED))
            n_anime = len(joblib.load(ANIME2ANIME_ENCODED))

            base_model = BaseModel(config_path=CONFIG_PATH)

            model = base_model.RecommenderNet(n_users=n_users, n_anime=n_anime)

            start_lr = 0.00001  ### starting learning rate
            min_lr = 0.00001  ### minimum learning rate
            max_lr = 0.00005  ### maximum learning rate
            batch_size = 10000  ### batch size

            ramup_epochs = 5  ### number of epochs to ramp up learning rate
            sustain_epochs = 0  ### number of epochs to sustain learning rate
            exp_decay = 0.8  ### exponential decay rate

            ### This function will be used to calculate the learning rate for each epoch, and find best learning rate for the model ###
            def lrfn(epoch):
                if epoch < ramup_epochs:
                    return (max_lr - start_lr) / ramup_epochs * epoch + start_lr
                elif epoch < ramup_epochs + sustain_epochs:
                    return max_lr
                else:
                    return (max_lr - min_lr) * exp_decay ** (epoch - ramup_epochs - sustain_epochs) + min_lr
            
            lr_callback = LearningRateScheduler(lambda epoch: lrfn(epoch) , verbose=0)  ### learning rate callback

            model_Checkpoint = ModelCheckpoint(filepath=CHECKPOINT_FILE_PATH, save_weights_only=True, save_best_only=True, monitor='val_loss', mode='min', verbose=1)  ### checkpoint callback

            early_stopping = EarlyStopping(monitor='val_loss', patience=3, verbose=1, mode='min', restore_best_weights=True)  ### early stopping callback, to stop model if no improvement in val_loss for 3 epochs

            my_callbacks = [lr_callback, model_Checkpoint, early_stopping]  ### list of callbacks

            os.makedirs(os.path.dirname(CHECKPOINT_FILE_PATH), exist_ok=True)  ### create directory for checkpoint file if it does not exist
            os.makedirs(MODEL_DIR, exist_ok=True)  ### create directory for model file if it does not exist
            os.makedirs(WEIGHTS_DIR, exist_ok=True)  ### create directory for weights file if it does not exist

            try:
                history = model.fit(
                        x=X_train_array, 
                        y=y_train, 
                        batch_size=batch_size, 
                        epochs=20, 
                        verbose=1,
                        validation_data=(X_test_array, y_test),
                        callbacks=my_callbacks,
                    )
                model.load_weights(CHECKPOINT_FILE_PATH)  ### load weights from checkpoint file
                logger.info("Model trained successfully")

                for epoch in range(len(history.history['loss'])):  ### Comet-ML logs the metrics for each epoch
                    train_loss = history.history['loss'][epoch]
                    val_loss = history.history['val_loss'][epoch]

                    self.experiment.log_metric("train_loss", train_loss, step=epoch)  ### log train loss to comet-ml
                    self.experiment.log_metric("val_loss", val_loss, step=epoch)  ### log val loss to comet-ml

            except Exception as e:
                logger.error(str(e))
                raise CustomException("Failed to train the model", e)
            
            self.save_model_weights(model)  ### save the model weights

        except Exception as e:
            logger.error(str(e))      ### f"Error in training the model: {e}"
            raise CustomException("Error during model training process", e)
    

    def extract_weights(self, layer_name, model):
        try:
            weight_layer = model.get_layer(layer_name)  ### get weights from the model
            weights = weight_layer.get_weights()[0]  ### get weights from the layer
            weights = weights / np.linalg.norm(weights, axis=1).reshape((-1,1))  ### normalize the weights
            logger.info(f"Weights extracted successfully from layer: {layer_name}")
            return weights  ### return the weights
        except Exception as e:
            logger.error(f"Error extracting weights from layer {layer_name}: {e}")
            raise CustomException(f"Failed to extract weights from layer {layer_name}", e)
            
        

    def save_model_weights(self,model):
        try:
            model.save(MODEL_PATH)  ### save the model
            logger.info(f"Model saved successfully to {MODEL_PATH}")

            user_weights = self.extract_weights("user_embedding", model)  ### extract user weights
            anime_weights = self.extract_weights("anime_embedding", model)  ### extract anime weights

            joblib.dump(user_weights, USER_WEIGHTS_PATH)  ### save user weights
            joblib.dump(anime_weights, ANIME_WEIGHTS_PATH)  ### save anime weights

            self.experiment.log_asset(MODEL_PATH)  ### log model to comet-ml
            self.experiment.log_asset(USER_WEIGHTS_PATH)  ### log user weights to comet-ml
            self.experiment.log_asset(ANIME_WEIGHTS_PATH)  ### log anime weights to comet-ml


            logger.info(f"User and anime weights saved successfully to {USER_WEIGHTS_PATH} and {ANIME_WEIGHTS_PATH}")

        except Exception as e:
            logger.error(f"Error saving the model: {e}")
            raise CustomException("Failed to save the model", e)


if __name__ == "__main__":
    model_trainer = ModelTraining(data_path=PROCESSED_DIR)
    model_trainer.train_model()