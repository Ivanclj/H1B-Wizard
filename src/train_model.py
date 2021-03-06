import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')
import argparse
import yaml
from scipy import stats
from scipy.stats import randint
import random

# prep
from sklearn.model_selection import train_test_split
from sklearn import preprocessing
from sklearn.datasets import make_classification
from sklearn.preprocessing import binarize, LabelEncoder, MinMaxScaler
from sklearn.feature_selection import SelectFromModel

# models
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier

# Validation libraries
from sklearn import metrics
from sklearn.metrics import accuracy_score, mean_squared_error, precision_recall_curve,confusion_matrix, classification_report, roc_auc_score, f1_score
from sklearn.model_selection import cross_val_score

#Neural Network
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import RandomizedSearchCV
from sklearn.model_selection import GridSearchCV
from sklearn.model_selection import StratifiedKFold

#Bagging
from sklearn.ensemble import BaggingClassifier, AdaBoostClassifier
from sklearn.neighbors import KNeighborsClassifier

#Naive bayes
from sklearn.naive_bayes import GaussianNB

#XGBoost
import xgboost as xgb
import pickle

import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)



def tuningRandomizedSearchCV(X,y,model, param_dist, num_times=20, cv=10, n_iter=20):
    '''
    Using random search to tune hyper parameters

    :param X: The table contains all covariates
    :param y: The response variable
    :param model: the predictive model
    :param param_dist: the ranges to sample from for each parameter to search
    :param num_times: how many times to repeat the search
    :param cv: number of folds in cross validation
    :param n_iter: number of starting search point
    :return: list of best parameters
    '''
    # Searching multiple parameters simultaneously
    # n_iter controls the number of searches

    # run RandomizedSearchCV 20 times (with n_iter=10) and record the best score
    logging.info("hyper parameter tunning started")
    best_scores = []
    best_params = []
    i = 0
    print('tunning parameter starts, total round: %s' % num_times)
    for _ in range(num_times):
        print('on %s/%s'%(i+1,num_times))
        rand = RandomizedSearchCV(model, param_dist, cv=cv, scoring='accuracy', n_iter=n_iter)
        rand.fit(X, y)
        best_scores.append(round(rand.best_score_, 3))
        best_params.append(rand.best_params_)
        i += 1
    logging.info(best_scores)
    logging.info(best_params[best_scores.index(max(best_scores))])

    return best_params[best_scores.index(max(best_scores))]



def randomForest(X,y,X_train, y_train, X_test,best_prams, n_estimators=50, seed=123):
    '''
    build the random forest model

    :param X:The table contains all covariates
    :param y: the response variable
    :param X_train: training set of all covariates
    :param y_train: training set of response
    :param X_test: training set of all covariates
    :param best_prams: best set of parameters
    :param n_estimators: number of trees
    :param seed: for reproducible purposes
    :return: random forest model
    '''
    # Calculating the best parameters
    forest = RandomForestClassifier(n_estimators=n_estimators)

    # param_dist = {"max_depth": randint(1, 7),
    #               "max_features": randint(1, 8),
    #               "min_samples_split": randint(2, 9),
    #               "min_samples_leaf": randint(1, 9),
    #               "criterion": ["gini", "entropy"]}
    # best_prams = tuningRandomizedSearchCV(X,y,forest, param_dist)

    # Building and fitting my_forest
    forest = RandomForestClassifier(max_depth=best_prams['max_depth'],
                                    max_features=best_prams['max_features'],
                                    min_samples_leaf=best_prams['max_features'],
                                    min_samples_split=best_prams['max_features'],
                                    n_estimators=n_estimators,
                                    random_state=seed)
    my_forest = forest.fit(X_train, y_train)


    # print('########### Random Forests ###############')
    #
    # accuracy_score = evalClassModel(my_forest, y_test, y_pred_class, True)
    #
    # # Data for final graph
    # methodDict['R. Forest'] = accuracy_score * 100


    return my_forest


def make_data(my_df):
    '''
    split predictors and response
    :param my_df: the original dataset
    :return: table of all covariates, response
    '''
    X = my_df.drop("treatment", axis=1)
    y = my_df.treatment

    return X,y

def split_data(X,y,test_size,random_state=123):
    '''
    train test split
    :param X: table of all covariates
    :param y: the response
    :param test_size: proportion to put in test
    :param random_state: for reproducible purposes
    :return: train and test set for both covariates and response
    '''
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size,
                                                        random_state=random_state)

    return X_train,X_test,y_train,y_test

# read in data
def main(args):
    ## read in data
    with open(args.config, "r") as f:
        config = yaml.load(f)

    config = config['train_model']
    if args.loadcsv is not None:
        my_df = pd.read_csv(args.loadcsv,index_col=0)
    else:
        my_df = pd.read_csv(config['read_path'],index_col=0)


    # define X and y
    #my_df = my_df.drop('work_interfere', axis=1)
    X,y = make_data(my_df)

    # select features
    y = pd.DataFrame(y)

    # save data

    X.to_csv(config['data']['X'])
    y.to_csv(config['data']['y'])
    logging.info("saved X.csv and y.csv")

    # split X and y into training and testing sets
    X_train, X_test, y_train, y_test = split_data(X, y, test_size=config['split_data']['test_size'],
                                                        random_state=config['split_data']['random_state'])

    logging.info("train test split done")

    # train model
    best_prams = config['best_params']
    forest = randomForest(X,y,X_train,y_train,X_test,best_prams,n_estimators=best_prams['n_estimator'])
    logging.info('model done')

    # # feature selection
    # sel = SelectFromModel(forest, prefit=True)
    # selected_features = list(X_train.columns[sel.get_support()])
    #
    # # define X and y
    # X_trunk = X[selected_features]
    # # split X and y into training and testing sets
    # X_train, X_test, y_train, y_test = train_test_split(X_trunk, y, test_size=0.20, random_state=123)
    #
    #
    #
    # forest = randomForest(X_trunk,y,X_train,y_train,X_test,n_estimators=10)
    #

    if args.savemodel is not None:
        path = args.savemodel
    else:
        path = config['save_tmo']
    with open(path, 'wb') as output:
        save_model = pickle.dump(forest, output, pickle.HIGHEST_PROTOCOL)

    logging.info("model saved")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")
    parser.add_argument('--config', default= 'config/config.yml',help='path to yaml file with configurations')
    parser.add_argument('--loadcsv', help='Path to where the cleaned data is stored (optional)')
    parser.add_argument('--savemodel', help='Path to where the model should be saved to (optional)')

    args = parser.parse_args()

    main(args)











