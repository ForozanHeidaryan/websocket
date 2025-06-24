import os
import re

import joblib
import numpy as np
import pandas as pd
from django.conf import settings
from hazm import word_tokenize, Normalizer, stopwords_list, Stemmer
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.preprocessing import LabelEncoder

from ai.models import Training

class TrainModel:

  def __init__(self):
    self.df = Training.objects.all()
    self.__model_path = os.path.join(settings.MEDIA_ROOT, "models")

    self.stopwords = set(stopwords_list())
    self.stemmer = Stemmer()
    self.normalizer = Normalizer()

  def execute(self):
    encoder1 = LabelEncoder()
    self.df['Category'] = encoder1.fit_transform(self.df['Category'])
    joblib.dump(encoder1, self.__model_path + 'encoder1.joblib')

    encoder2 = LabelEncoder()
    self.df['Sarfasl'] = encoder2.fit_transform(self.df['Sarfasl'])
    joblib.dump(encoder2, 'encoder2.joblib')

    encoder3 = LabelEncoder()
    self.df['Grouh'] = encoder3.fit_transform(self.df['Grouh'])
    joblib.dump(encoder3, 'encoder3.joblib')

    self.df['Title'] = self.df['Title'].apply(self.__remove_numbers)

    self.df['Title'] = self.df['Title'].apply(self.__remove_spaces)

    texts = self.df['Title'].values
    preprocessed_texts = self.__preprocess_texts(texts)

    preprocessed_texts = self.__create_matrix_from_texts(preprocessed_texts, len(texts))

    preprocessed_texts = np.where(np.array(preprocessed_texts) == None, '',
                                  np.array(preprocessed_texts))

    cleaned_data = self.__remove_extra_data(preprocessed_texts)

    df2 = self.__create_combined_dataframe(cleaned_data, self.df)

    df2 = self.__join_lists_to_string(df2, 'Title')

    vectorizer = CountVectorizer()
    vec_title = vectorizer.fit_transform(df2.Title)
    joblib.dump(vec_title, 'vec_title.joblib')

    y1 = df2['Category']
    y2 = df2['Sarfasl']
    y3 = df2['Grouh']

    RF_modely1 = RandomForestClassifier()
    RF_modely1.fit(vec_title, y1)

    RF_modely2 = RandomForestClassifier()
    RF_modely2.fit(vec_title, y2)

    RF_modely3 = RandomForestClassifier()
    RF_modely3.fit(vec_title, y3)

    joblib.dump(RF_modely1, self.__model_path + 'RF_model_y1.joblib')
    joblib.dump(RF_modely2, 'RF_model_y2.joblib')
    joblib.dump(RF_modely3, 'RF_model_y3.joblib')
    joblib.dump(vectorizer, 'vectorizer.joblib')

  def __remove_numbers(self ,text):
      return re.sub(r'\d+', '0,1,2,3,4,5,6,7,8,9', text)

  def __remove_spaces(self , string):
      return string.strip()

  def __preprocess_text(self, text):
      if isinstance(text, list):
         text = "".join(text)
      normalized_text = self.normalizer.normalize(text)
      tokens = word_tokenize(normalized_text)
      filtered_tokens = [token for token in tokens if token not in self.stopwords]
      stemmed_tokens = [self.stemmer.stem(token) for token in filtered_tokens]
      return stemmed_tokens

  def __preprocess_texts(self, texts):
      preprocessed_texts = [self.__preprocess_text(text) for text in texts]
      return preprocessed_texts

  def __create_matrix_from_texts(self, texts, max_len):
    result = np.empty((len(texts), max_len), dtype=object)
    for i, text in enumerate(texts):
      processed_text = self.__preprocess_text(text)
      result[i, :len(processed_text)] = processed_text
    return result

  def __remove_extra_data(self, data):
    return [[word for word in row if word] for row in data]

  def __create_combined_dataframe(self ,column, data):
      X = pd.Series(column)
      w = data['Category']
      d = data['Sarfasl']
      p = data['Grouh']
      data_ = pd.concat([X, w, d, p], axis=1)
      data_.columns = ['Title', 'Category', 'Sarfasl', 'Grouh']
      return data_

  def __join_lists_to_string(self, df, column_name):
      df[column_name] = [' '.join(row) for row in df[column_name]]
      return df
