# -*- coding: utf-8 -*-
"""AutoEncoder_ReconstructionError.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1q44IkfP2kU4p1lBizCHiDczEwqmrjIcq
"""

!git clone https://github.com/tuanio/nsl_kdd.git

import numpy as np
import pandas as pd
import tensorflow as tf
import matplotlib.pyplot as plt
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    mean_squared_error,
    f1_score,
    ConfusionMatrixDisplay, 
    classification_report,
    precision_recall_fscore_support
)
import scipy
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras import layers, losses
from tensorflow.keras.models import Model
from sklearn.metrics import r2_score
import seaborn as sns
from dataclasses import dataclass

train = pd.read_csv('nsl_kdd/KDDTrain+.txt', header=None)
test = pd.read_csv('nsl_kdd/KDDTest+.txt', header=None)

def preprocess(data):
  df = data.copy()
  # normal is 1, abnormal is 0
  df[41] = df[41].apply(lambda x: 1 if x == 'normal' else 0)
  # all zeros
  df = df.drop(19, axis=1)
  # difficulty columns, not affect
  df = df.drop(42, axis=1)

  # get label
  label = df.iloc[:, -1].values
  df = df.iloc[:, :-1]
  # one hot encoder
  df = pd.get_dummies(df)
  # min max scaler
  df = pd.DataFrame(MinMaxScaler().fit_transform(df))

  # assign label
  df['label'] = label 
  return df

# Commented out IPython magic to ensure Python compatibility.
# %%time
# train = preprocess(train)
# test = preprocess(test)

normal = train[train.iloc[:, -1] == 1].iloc[:, :-1].values
abnormal = train[train.iloc[:, -1] == 0].iloc[:, :-1].values

normal.shape, abnormal.shape

X = train.iloc[:, :-1].values
y = train.iloc[:, -1].values
Xtrain, Xtest, ytrain, ytest = train_test_split(X, y, test_size=0.2, random_state=12)
Xtrain.shape, Xtest.shape

class AnomalyDetector(Model):
  def __init__(self):
    super(AnomalyDetector, self).__init__()
    self.encoder = tf.keras.Sequential([
      layers.Dense(100, activation='relu'),
      layers.Dense(55, activation='relu'),
    ])
    self.decoder = tf.keras.Sequential([
      layers.Dense(100, activation='relu'),
      # 121 is input data shape
      layers.Dense(X.shape[1], activation='sigmoid')
    ])
  
  def call(self, X):
    encoded = self.encoder(X)
    decoded = self.decoder(encoded)
    return decoded

model = AnomalyDetector()

optimizer = tf.keras.optimizers.Adam(learning_rate=0.005)
model.compile(optimizer=optimizer, loss=losses.MeanSquaredError())

model_results = model.fit(normal, normal,
  epochs=300,
  batch_size=64,
  shuffle=True
)

min(model_results.history['loss'])

history_loss = model_results.history['loss']
plt.plot(np.arange(len(history_loss)), history_loss)
plt.show()

mae_normal = losses.mae(normal, model.predict(normal)).numpy()
mae_abnormal = losses.mae(abnormal, model.predict(abnormal)).numpy()

r2_normal = r2_score(normal, model.predict(normal))
r2_abnormal = r2_score(abnormal, model.predict(abnormal))

r2_normal, r2_abnormal

mae_normal.mean(), mae_normal.var()

mae_normal.std()

mae_abnormal.mean(), mae_abnormal.var()

# dataclass
# class GaussianDistribution(object):
#   mu: float
#   sigma: float

#   def pdf(self, x):
#     return np.exp(-1/2 * ((x - self.mu) / self.sigma) ** 2) / np.sqrt(2 * np.pi * self.sigma ** 2)

# normal_gaussian = GaussianDistribution(mu=mae_normal.mean(), sigma=mae_normal.std())
# abnormal_gaussian = GaussianDistribution(mu=mae_abnormal.mean(), sigma=mae_abnormal.std())
normal_gaussian = scipy.stats.norm(loc=mae_normal.mean(), scale=mae_normal.std())
abnormal_gaussian = scipy.stats.norm(loc=mae_abnormal.mean(), scale=mae_abnormal.std())

abnormal_gaussian

def predict_class(x):
  if x.shape[0] == X.shape[1]:
    x = x.reshape(-1, X.shape[1])
  reconstruction_loss = losses.mae(x, model.predict(x)).numpy()
  normal_pdf = normal_gaussian.pdf(reconstruction_loss)
  abnormal_pdf = abnormal_gaussian.pdf(reconstruction_loss)
  return np.where(normal_pdf > abnormal_pdf, 1, 0)

index = 2
predict_class(X[index]), y[index]

class_predicted = predict_class(X)
cfx_matrix = confusion_matrix(y, class_predicted)
cfx_matrix

clf_report = classification_report(y, class_predicted, target_names=['abnormal', 'normal'])
print(clf_report)

precision, recall, fscore, _ = precision_recall_fscore_support(y, class_predicted, pos_label=1, average='binary')
print('Precision:', precision)
print('Recall:', recall)
print('F1', fscore)

fig, ax = plt.subplots(figsize=(10, 7))
sns.heatmap(cfx_matrix, annot=True, fmt='.0f')
ax.set_ylabel('True class')
ax.set_xlabel('Predicted class')
plt.show()

fig, ax = plt.subplots(figsize=(20, 5))
sns.histplot(data=mae_normal, kde=True, label='Normal', ax=ax)
sns.histplot(data=mae_abnormal, kde=True, label='Abnormal', ax=ax)
ax.set_title('Normal and Abnormal reconstruction error')
ax.grid(True, alpha=0.5, ls='-.')
ax.legend(loc='best')
fig.tight_layout()
plt.show()

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(22, 5))
sns.histplot(data=mae_normal, kde=True, ax=ax[0])
sns.histplot(data=mae_abnormal, kde=True, ax=ax[1])
ax[0].set_title('Normal reconstruction error')
ax[1].set_title('Abnormal reconstruction error')
ax[0].grid(True, alpha=0.5, ls='-.')
ax[1].grid(True, alpha=0.5, ls='-.')
fig.tight_layout()
plt.show()

X_test = test.iloc[:, :-1].values
y_test = test.iloc[:, -1].values
X_test.shape
# y_test_predicted = predict_class(X_test)