import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
#from sklearn import tree
#from sklearn.ensemble import RandomForestClassifier
#from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score
from sklearn.metrics import roc_auc_score
from xgboost import XGBClassifier
from sklearn.multiclass import OneVsRestClassifier
from sklearn.multiclass import OneVsOneClassifier
from sklearn.model_selection import train_test_split
from sklearn import cross_validation
from sklearn.metrics import confusion_matrix
from collections import defaultdict
from sklearn import preprocessing
import itertools
import seaborn as sns

def plot_confusion_matrix(cm,
                          target_names,
                          title='Confusion matrix',
                          cmap=None,
                          normalize=True):
    """
    given a sklearn confusion matrix (cm), make a nice plot

    Arguments
    ---------
    cm:           confusion matrix from sklearn.metrics.confusion_matrix

    target_names: given classification classes such as [0, 1, 2]
                  the class names, for example: ['high', 'medium', 'low']

    title:        the text to display at the top of the matrix

    cmap:         the gradient of the values displayed from matplotlib.pyplot.cm
                  see http://matplotlib.org/examples/color/colormaps_reference.html
                  plt.get_cmap('jet') or plt.cm.Blues

    normalize:    If False, plot the raw numbers
                  If True, plot the proportions

    Usage
    -----
    plot_confusion_matrix(cm           = cm,                  # confusion matrix created by
                                                              # sklearn.metrics.confusion_matrix
                          normalize    = True,                # show proportions
                          target_names = y_labels_vals,       # list of names of the classes
                          title        = best_estimator_name) # title of graph

    Citiation
    ---------
    http://scikit-learn.org/stable/auto_examples/model_selection/plot_confusion_matrix.html

    """

    accuracy = np.trace(cm) / float(np.sum(cm))
    misclass = 1 - accuracy

    if cmap is None:
        cmap = plt.get_cmap('Blues')

    plt.figure(figsize=(8, 6))
    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    plt.title(title)
    plt.colorbar()

    if target_names is not None:
        tick_marks = np.arange(len(target_names))
        plt.xticks(tick_marks, target_names, rotation=45)
        plt.yticks(tick_marks, target_names)

    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]


    thresh = cm.max() / 1.5 if normalize else cm.max() / 2
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        if normalize:
            plt.text(j, i, "{:0.4f}".format(cm[i, j]),
                     horizontalalignment="center",
                     color="white" if cm[i, j] > thresh else "black")
        else:
            plt.text(j, i, "{:,}".format(cm[i, j]),
                     horizontalalignment="center",
                     color="white" if cm[i, j] > thresh else "black")


    plt.tight_layout()
    plt.ylabel('True label')
    plt.xlabel('Predicted label\naccuracy={:0.4f}; misclass={:0.4f}'.format(accuracy, misclass))
    plt.show()

def df_encode(df):
	le  = preprocessing.LabelEncoder()
	ohe = preprocessing.OneHotEncoder(sparse=False)

	le.fit(df)
	np_ = le.fit_transform(df)
	np_ = np_.reshape((len(np_),1))
	ohe.fit(np_)
	np_ = ohe.fit_transform(np_)
	df  = pd.DataFrame(np_)
	return df, le, ohe

def df_transform(df, le, ohe):
	return pd.DataFrame(ohe.transform(le.transform(df).reshape(len(df),1)))

def extract_features(df, send_to_csv):
	# DROP PLACES ONLY SEEN LESS THAN x TIMES
	df = df.groupby('Name').filter(lambda x: len(x) >= 3)
	# DROP PLACES WITHOUT CATEGORIES
	df = df.dropna()

	#extract features
	name_df, name_le, name_ohe             = df_encode(df['Name'])
	time_df                                = df['BeginTime'].str.split(':').str.get(0).apply(lambda x: int(x))
	week_df                                = df['WeekDay']
#	week_df, week_le, week_ohe	       = df_encode(df['WeekDay'])
	duration_df                            = df['Duration'].str.split('h').str.get(0).apply(lambda x: int(x))
	category_df, category_le, category_ohe = df_encode(df['Category'])
	weather_df, weather_le, weather_ohe    = df_encode(df['Weather']) 
	people_df                              = df.filter(regex='People') 
	mood_df                                = df['Mood']
	#mood_df                                = mood_df.replace(5,4)
	#mood_df                                = mood_df.replace(1,2)
	
	#%matplotlib inline
	#plt.scatter(dataset[:,0], dataset[:,1], c='blue', s=10)
	#plot.show()

	table_df= pd.concat([name_df, time_df, week_df, duration_df, category_df, weather_df, people_df, mood_df], axis=1, join='inner').dropna(how='any', axis=0)
       #table_df = pd.concat([name_df, time_df, week_df, duration_df, category_df, weather_df, people_df, mood_df], axis=1, join='inner').dropna(how='any', axis=0)
#	print table_df
#       if send_to_csv:
#       		table_df.to_csv('features.csv')
	return table_df

df = pd.read_csv("tung_hist_jan_mar_weather_nolocomotion_people_mood.csv", index_col=0)
table_df = extract_features(df, False)

feature_df = table_df.drop('Mood', axis=1)
label_df, label_le, label_ohe = df_encode(table_df['Mood'])
#print feature_df
#print label_df

seed = 7
test_size = 0.33
X_train, X_test, y_train, y_test = train_test_split(feature_df.values, label_df.values, test_size=test_size, random_state = seed)


for i in range(-20,20,1):
	clf_multiclass = OneVsRestClassifier(XGBClassifier(objective='binary:logistic', learning_rate=0.1, n_estimators=1000, max_depth=1, min_child_weight=1, gamma=0.1, subsample=.7, colsample_bytree=.9, scale_pos_weight=1, seed = seed, reg_alpha=.048, reg_lambda=.99))
			
	clf_multiclass.fit(X_train, y_train)
	y_pred = clf_multiclass.predict_proba(X_test) #predict_proba
	y_pred_mood = np.argmax(y_pred, axis=1)
	y_test_mood = np.argmax(y_test, axis=1)
	
	#print y_pred_mood
	#print y_test_mood
	#print y_pred_mood - y_test_mood
	
	#cm_mood = confusion_matrix(y_test_mood, y_pred_mood)
	#plot_confusion_matrix(cm_mood, ['1', '2', '3', '4', '5']);
	
	print "reg_lambda " + str(i*.01+1)
	sum = 0
	for x in range(0,len(y_test[0])):
		sum = sum + roc_auc_score(y_test[:,x], y_pred[:,x])
#		print roc_auc_score(y_test[:,x], y_pred[:,x])
	print sum/5

#model = XGBClassifier()
#model.fit(X_train, y_train[:,4])
#
#
#y_pred = model.predict_proba(X_test)
#print y_pred
#print y_test[:,4]
##print roc_auc_score(y_test[:,4], y_pred)

#####

#scores = cross_validation.cross_val_score(model, feature_df, label_df, cv=10)
#print scores.mean()
#print scores.std()*2

#y_pred = model.predict(X_test)
#accuracy = accuracy_score(y_test, y_pred)
#
#print("Accuracy: %.2f%%" % (accuracy * 100.0))
#print feature_df
#print label_df
#
#
#clf = tree.DecisionTreeClassifier()
#clf = RandomForestClassifier(n_estimators=200,max_depth=None,random_state=1,class_weight='balanced_subsample')
#clf = MLPClassifier(solver='lbfgs', alpha=1e-5, hidden_layer_sizes=(100,20), random_state=1)
#scores = cross_validation.cross_val_score(clf, feature_df, label_df, cv=10)
#print scores
#print scores.mean() 
#print scores.std()*2


#clf = clf.fit(feature_df, label_df)
#print feature_df.iloc[0:1]
#print clf.predict(feature_df.iloc[0:1])
#print clf.predict(feature_df[0])

#pd.concat([df_transform(['Home'], name_le, name_ohe),pd.DataFrame([9]),pd.DataFrame([3]),pd.DataFrame([4]), df_transform(['Apartment Building'], category_le, category_ohe), df_transform([' clear-day'], weather_le, weather_ohe)]))



