import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
import numpy.random as random

def apply(features_to_exclude = [], hybrid_mode = True, trees_per_forest = 500, removal = -1, mix_ratio = 0.2):
  training_data = []
  training_labels = []
  test_data = []

  with open("train_features.csv") as f:
    feature_labels = f.readline().strip().split(",")
    feature_labels = feature_labels[1:-1]
    for line in f:
      data = line.strip().split(",")
      # print len(data)
      training_data.append([float(d) for d in data[1:-1]])
      training_labels.append(int(float(data[-1])))
      
  with open("test_features.csv") as f:
    test_labels = f.readline().strip().split(",")
    test_labels = test_labels[1:-1]
    
    for i in range(len(feature_labels)):
      assert feature_labels[i] == test_labels[i]
    
    for line in f:
      data = line.strip().split(",")
      test_data.append([float(d) for d in data[1:]])
    
  # Exclude selected features
  for ex in features_to_exclude:
    assert ex in feature_labels
    index = feature_labels.index(ex)
    for i in range(len(training_data)):
      del training_data[i][index]
    for i in range(len(test_data)):
      del test_data[i][index]
    feature_labels.remove(ex)

  # Remove data with no bids or only 1 bid from training data
  if removal >= 0:
    for datum in training_data:
      if abs(datum[1] - 0.0) < 0.0000001:
        ind = training_data.index(datum)
        training_data.remove(datum)
        training_labels = training_labels[:ind] + training_labels[ind+1:]
  if removal >= 1:
    for datum in training_data:
      if abs(datum[1] - 0.69314718056) < 0.0000001:
        ind = training_data.index(datum)
        training_data.remove(datum)
        training_labels = training_labels[:ind] + training_labels[ind+1:]    
      
  model = LogisticRegression()
  model.fit(training_data, training_labels)

  vals = model.predict_proba(test_data)
  vals = [v[1] for v in vals]

  if hybrid_mode:
    rf_model = RandomForestClassifier(n_estimators = trees_per_forest)
    rf_model.fit(training_data, training_labels)
    
    for i in range(len(feature_labels)):
      print feature_labels[i], rf_model.feature_importances_[i]
    
    vals2 = rf_model.predict_proba(test_data)
    vals2 = [v[1] for v in vals2]
    
    vals = [(mix_ratio * vals[i] + (1 - mix_ratio) * vals2[i]) for i in range(len(vals))]
    

  # Output solutions to a file
  with open("test_features.csv") as data:
    with open("solution.csv", "wb") as w:
      w.write("bidder_id,prediction\n")
      data.readline()
      i = 0
      for line in data:
        w.write(line.strip().split(",")[0] + "," + str(vals[i]) + "\n")
        i += 1
      
if __name__ == "__main__":
  apply()