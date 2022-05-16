#!/usr/bin/env/python3
'''
Description: A script for machine learning based alogorithm for leaftype classification
             Script does automated feature selection and gridsearch with cross-validation
Authors: Suvarna Punalekar (Aberystwyth University).

link: https://www.kaggle.com/sureshshanmugam/xgboost-with-feature-selection
'''

# import warnings filter
from warnings import simplefilter
# ignore all future warnings
simplefilter(action='ignore', category=FutureWarning)

import glob, os, sys
from os import path
from sys import stdout
#import rasterio
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import sklearn
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import cross_validate
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.feature_selection import RFE
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.pipeline import Pipeline
from sklearn.model_selection import RandomizedSearchCV
from sklearn import metrics
from sklearn.metrics import confusion_matrix
import pickle
import lightgbm as lgb
from sklearn.metrics import accuracy_score
from sklearn.metrics import classification_report
from itertools import compress
import xgboost as xgb
####################################################################
jobs = -1
numb = 0
cv = 5
feature = 100
####################################################################
    
'''
Reading input data, Get response variable column 
Output directory and filenames
'''
############################################################################
Dir = 'data/LW_analysis/SeminaturalMapping_ver3/Ver3Plots_split_set2'
CalData = '/AllSps_CalSet.csv'
ValData = '/AllSps_ValSet.csv'


OutDir = Dir + '/testModel_xgb_feat' + str(feature)
if not os.path.exists(OutDir):
    os.mkdir(OutDir)
    
OutFile1 = OutDir + '/' + 'BestParam.csv'
OutFile2 = OutDir + '/' + 'Accuracy.csv'
OutFile3 = OutDir + '/' + 'ConfusionMatrix_set1_'
OutFile4 = OutDir + '/' + 'ConfusionMatrix_step2_'
OutFile5 = OutDir + '/' + 'CV_results.csv'
OutFile6 = OutDir + '/' + 'Selected_features.csv'
OutFile7 = OutDir + '/' + 'ConfusionMatrix_validplots_'

############################################################################

#Training data
EOData= pd.read_csv(Dir + CalData, ',', index_col=False)
EOData = EOData[EOData.columns.drop(list(EOData.filter(regex='min')))]
EOData = EOData[EOData.columns.drop(list(EOData.filter(regex='max')))]
# EOData = EOData[EOData.columns.drop(list(EOData.filter(regex='VV')))]
# EOData = EOData[EOData.columns.drop(list(EOData.filter(regex='VH')))]
# EOData = EOData[EOData.columns.drop(list(EOData.filter(regex='VHVV')))]

print(EOData.head())
EOData = EOData[EOData.JultoOctS2REP2016to2019med != -999]
EOData = EOData[EOData.AnnualVV2019sum != 32767]
# EOData = EOData[EOData.LIDARDerivedDTM10m != -32768]
# EOData = EOData[EOData.LIDARDerivedSlope10m != -9999]
print(EOData.shape)

EOData = EOData[~EOData.isin([np.nan, np.inf, -np.inf, -999, -9999, 32767, -32768]).any(1)]
#EOData = EOData[EOData["typecode"]<=2]
print(EOData.shape)

EOData["typecode"] = EOData["typecode"].astype(int)
#del LeafType
############################################################################
''' Defining Responses and predictors'
'''
predictors = list(EOData.columns)
print(predictors)
#predictors.remove('Unnamed: 0')
predictors.remove('ID_1')
predictors.remove('typecode')
predictors.remove('type')

print(predictors)
responses = ['typecode']
############################################################################
'''
Reading input independent test data
'''
#Testing data
TestData_all = pd.read_csv(Dir + ValData, ',', index_col=False)
TestData_all = TestData_all[TestData_all.columns.drop(list(TestData_all.filter(regex='min')))]
TestData_all = TestData_all[TestData_all.columns.drop(list(TestData_all.filter(regex='max')))]
# TestData_all = TestData_all[TestData_all.columns.drop(list(TestData_all.filter(regex='VV')))]
# TestData_all = TestData_all[TestData_all.columns.drop(list(TestData_all.filter(regex='VH')))]
# TestData_all = TestData_all[TestData_all.columns.drop(list(TestData_all.filter(regex='VHVV')))]

TestData_all = TestData_all[TestData_all.JultoOctS2REP2016to2019med != -999]
#TestData_all= TestData_all[TestData_all["typecode"]<=2]
TestData_all = TestData_all[TestData_all.AnnualVV2019sum != 32767]
# TestData_all = TestData_all[TestData_all.LIDARDerivedDTM10m != -32768]
# TestData_all = TestData_all[TestData_all.LIDARDerivedSlope10m != -9999]
print(TestData_all.shape)

TestData_all = TestData_all[~TestData_all.isin([np.nan, np.inf, -np.inf, -999, -9999, 32767, -32768]).any(1)]
print(TestData_all.shape)
TestData_all["typecode"] = TestData_all["typecode"].astype(int)

#print(TestData_all['Class'])
'''
Defining predictors and response variables for independet test data
'''
X_valid = TestData_all[predictors].values
y_valid = TestData_all[responses].values
y_valid = y_valid.reshape(y_valid.shape[0])

print(np.amin(X_valid))
print('X_valid matrix is sized: {sz}'.format(sz=X_valid.shape))
print('y_valid array is sized: {sz}'.format(sz=y_valid.shape))
# 
# ############################################################################
# 
# '''
# Defining predictors and response variables, Data are not split here, All training plots and pixels used for the model development.
# '''
# 
# What are our classification labels?
classes = EOData[responses].values
labels = np.unique(classes)
print('The training data include {n} classes: {classes}'.format(n=labels.size, classes=labels))

X = EOData[predictors].values
y = EOData[responses].values
print(y)
unique, counts = np.unique(y, return_counts=True)
print(dict(zip(unique, counts)))

#Split data for training and testing
#X_train, X_test, y_train, y_test = train_test_split(X, y, train_size= 0.8, test_size=0.2, random_state=42)
X_train, X_test = X, X
y_train, y_test = y, y
y_train = y_train.reshape(y_train.shape[0])
y_test = y_test.reshape(y_test.shape[0])
print(y_train.shape)
print(y_test.shape)


print(np.amin(X), np.amax(X))
print('X matrix is sized: {sz}'.format(sz=X.shape))
print('y array is sized: {sz}'.format(sz=y.shape))


print(np.amin(X_train), np.amax(X_train))
print('X_train matrix is sized: {sz}'.format(sz=X_train.shape))
print('y_train array is sized: {sz}'.format(sz=y_train.shape))

print(np.amin(X_test), np.amax(X_test))
print('X_test matrix is sized: {sz}'.format(sz=X_test.shape))
print('y_test array is sized: {sz}'.format(sz=y_test.shape))

############################################################################


'''
The scripts loops through number of features. For each number of features, it finds the best hyperparameter combination
through gridsearch. Feature selection is done using Recursive feature elemination.
Once the best parameters and features are found, three predictions are done.
step 1: Using the best model found though pipeline is directly applied on the test dataset and accuracy is calculated.
step 2: the best features and parameters are used to fit new model using the entire dataset abd then accuracy is caluclated.
step 3: Accuracies for independent set of 130 plots is calculated
'''

df_param_out = pd.DataFrame(columns=['num_features', 'n_estimators'])
df_accuracy = pd.DataFrame(columns=['num_features', 'Val_step1', 'Val_step2', 'Val_step3'])
df_cv_results = pd.DataFrame()
df_features = pd.DataFrame()



#estimator = lgb.LGBMClassifier(n_jobs=jobs)

estimator = xgb.XGBClassifier(learning_rate=0.05, n_estimators=500, random_state=1234)
fs = SelectKBest(score_func=f_classif, k=feature)
#selector = RFE(estimator, n_features_to_select=feature, step=1)
steps = [
    ('s', fs),
    ('m', estimator)
]
pipe = Pipeline(steps)

# 
#rfe = RFE(estimator=ExtraTreesClassifier(n_jobs=jobs, n_estimators=100), n_features_to_select=feature)

param_grid = {
    'm__learning_rate': np.arange(0.1, 1, 0.1),
    'm__max_depth': np.arange(5,15,1),
    'm__n_estimators': np.arange(500,2000,500),
    'm__colsample_bytree': np.arange(0.5, 1, 0.1)
}

# param_grid = {
#     'm__learning_rate': np.arange(0.1, 0.2, 0.1),
#     'm__max_depth': np.arange(5,7,1),
#     'm__n_estimators': np.arange(50,100,10),
#     'm__colsample_bytree': np.arange(0.5, 0.7, 0.1)
# }

clf = RandomizedSearchCV(estimator=pipe, param_distributions=param_grid, n_iter=5, cv=cv, verbose=False)

clf.fit(X_train, y_train)
# 
print('Best params selected: ')
# print(clf.best_params_)
param1 = clf.best_params_.get('m__n_estimators')
param2 = clf.best_params_.get('m__learning_rate')
param3 = clf.best_params_.get('m__max_depth')
param4 = clf.best_params_.get('m__colsample_bytree')
# # param3 = clf.best_params_.get('m__max_features')
df_param_out.at[numb,'n_estimators'] = param1
df_param_out.at[numb,'learning_rate'] = param2
df_param_out.at[numb,'max_depth'] = param3
df_param_out.at[numb,'max_depth'] = param4
 
df_cv_results['featnum_'+ str(feature)] = clf.cv_results_['mean_test_score']
# # ######################################################################
# # step 1
X_test_fs = clf.best_estimator_.named_steps['s'].transform(X_test)
y_pred_test = clf.best_estimator_.named_steps['m'].predict(X_test_fs)
accuracy_test = metrics.accuracy_score(y_test, y_pred_test)
df_accuracy.at[numb, 'Val_step1'] = accuracy_test
df_accuracy.at[numb,'num_features'] = feature
print('Validation accuracy setp 1: '+ str(round(accuracy_test, 3)))


# print('List of features selected ')
# print(list(compress(predictors, clf.best_estimator_.named_steps['s'].support_)))
#feature_list = list(compress(predictors, clf.best_estimator_.named_steps['s'].support_))
feature_list = list(compress(predictors, clf.best_estimator_.named_steps['s'].get_support()))
# print(clf.best_estimator_.named_steps['s'].ranking_)
# print(clf.best_estimator_.named_steps['s'].support_)

print(feature_list, len (feature_list))
df_features['featnum_'+ str(feature)] = feature_list

print(confusion_matrix(y_test, y_pred_test))

y_true_series = pd.Series(y_test.flat, name="Actual")
y_pred_series = pd.Series(y_pred_test.flat, name="Predicted")
df_confusion = pd.crosstab(y_true_series, y_pred_series)
outfile = OutFile3 + 'featurenumber_' + str(feature) + '.csv'
df_confusion.to_csv(outfile, sep=',')

del y_pred_test, outfile, y_true_series, y_pred_series, df_confusion, accuracy_test, feature_list
# ##########################################################################
# step 2
# 
X_train_selected = clf.best_estimator_.named_steps['s'].transform(X_train)
model_final = xgb.XGBClassifier(n_estimators=param1, learning_rate=param2, max_depth=param3, colsample_bytree=param4)

clf2 = model_final.fit(X_train_selected, y_train)
y_pred_final = clf2.predict(X_test_fs)
accuracy_test = metrics.accuracy_score(y_test, y_pred_final)
df_accuracy.at[numb, 'Val_step2'] = accuracy_test
print('Validation accuracy setp 2: '+ str(round(accuracy_test, 3)))
print(confusion_matrix(y_test, y_pred_final))

y_true_series = pd.Series(y_test.flat, name="Actual")
y_pred_series = pd.Series(y_pred_final.flat, name="Predicted")
df_confusion = pd.crosstab(y_true_series, y_pred_series)
outfile = OutFile4 + 'featurenumber_' + str(feature) + '.csv'
df_confusion.to_csv(outfile, sep=',')
# 
# #save the model to disk
# 
filename = OutDir + '/' + 'featurenum_' + str(feature) + '_model.sav'
pickle.dump(model_final, open(filename, 'wb'))
    

del y_pred_final, outfile, y_true_series, y_pred_series, df_confusion, accuracy_test, X_train_selected
##
###########################################################################
'''
 step 3 (independent validation)
'''

X_valid_trans = clf.best_estimator_.named_steps['s'].transform(X_valid)
y_valid_pred = clf2.predict(X_valid_trans)
accuracy_test = metrics.accuracy_score(y_valid, y_valid_pred)

df_accuracy.at[numb, 'Val_step3'] = accuracy_test
print('Validation accuracy setp 3: '+ str(round(accuracy_test, 3)))
print(confusion_matrix(y_valid, y_valid_pred))

y_true_series = pd.Series(y_valid.flat, name="Actual")
y_pred_series = pd.Series(y_valid_pred.flat, name="Predicted")
df_confusion = pd.crosstab(y_true_series, y_pred_series)
outfile = OutFile7 + 'featurenumber_' + str(feature) + '.csv'
df_confusion.to_csv(outfile, sep=',')


numb = numb + 1
del y_valid_pred, X_valid_trans, outfile, y_true_series, y_pred_series, df_confusion, accuracy_test,  clf2, clf
del X_valid
# 
# # # ############################################################################
# # # #plotting and saving
df_accuracy.to_csv(OutFile2, sep=',')
df_param_out.to_csv(OutFile1, sep=',')
df_cv_results.to_csv(OutFile5, sep=',')
df_features.to_csv(OutFile6, sep=',')
# 
# 
del df_accuracy, df_param_out, df_cv_results, df_features
# 
del X, y
 