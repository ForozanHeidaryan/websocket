import os
import re

import joblib
import numpy as np
import pandas as pd
from django.conf import settings
from hazm import *
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ai.models import CustomerData, TurningPrediction


class PredictCustomersData:
  def __init__(self):
    self.__customer_data = CustomerData.objects.all()
    self.__model_path = os.path.join(settings.MEDIA_ROOT, "models")

    self.stopwords = set(stopwords_list())
    self.stemmer = Stemmer()
    self.normalizer = Normalizer()
    self.vectorizer = CountVectorizer()

  def execute(self):
    self.__predict_data()

  def __predict_data(self):
    max_len = 0
    preprocessed_texts = []
    names = []
    for customer in self.__customer_data:
      names.append(customer.name)
      customer.name = self.__remove_numbers(customer.name)
      customer.name = self.__remove_spaces(customer.name)
      customer.name = self.__preprocess_text(customer.name)
      preprocessed_texts.append(customer.name)
      max_len = max(len(customer.name), max_len)

    preprocessed_texts = self.__create_matrix_from_texts(preprocessed_texts, max_len)
    preprocessed_texts = np.where(np.array(preprocessed_texts) == None, '', np.array(preprocessed_texts))

    cleaned_data1 = self.__remove_extra_data(preprocessed_texts)

    cleaned_data1 = pd.Series(cleaned_data1)

    x_predict = pd.DataFrame({'name': cleaned_data1})
    x_predict = self.__join_lists_to_string(x_predict, 'name')

    loaded_vectorizer = self.__get_joblib_file('vectorizer.joblib')
    vec_predict = loaded_vectorizer.transform(x_predict.name)

    rf_modely_1 = self.__get_joblib_file("RF_model_y1.joblib")
    rf_modely_1 = rf_modely_1.predict(vec_predict)
    encoder1 = self.__get_joblib_file("encoder1.joblib")
    turning = encoder1.inverse_transform(rf_modely_1)

    rf_modely_2 = self.__get_joblib_file("RF_model_y2.joblib")
    rf_modely_2 = rf_modely_2.predict(vec_predict)
    encoder2 = self.__get_joblib_file("encoder2.joblib")
    sarfasl = encoder2.inverse_transform(rf_modely_2)

    rf_modely_3 = self.__get_joblib_file("RF_model_y3.joblib")
    rf_modely_3 = rf_modely_3.predict(vec_predict)
    encoder3 = self.__get_joblib_file("encoder3.joblib")
    account_group = encoder3.inverse_transform(rf_modely_3)

    vec_train = self.__get_joblib_file('vec_title.joblib')
    similarity = cosine_similarity(vec_predict, vec_train)
    similarity = np.max(similarity, axis=1)
    turning_predictions = pd.DataFrame(
      {
        'turning': turning,
        'sarfasl': sarfasl,
        'account_group': account_group,
        'similarity': similarity,
        'title': names
      }
    )

    self.__insert_data(turning_predictions)

  def __remove_numbers(self, text):
    return re.sub(r'\d+', '0,1,2,3,4,5,6,7,8,9', text)

  def __remove_spaces(self, string):
    return string.strip()

  def __preprocess_text(self, text):
    if isinstance(text, list):
      text = "".join(text)
    normalized_text = self.normalizer.normalize(text)
    tokens = word_tokenize(normalized_text)
    filtered_tokens = [token for token in tokens if token not in self.stopwords]
    stemmed_tokens = [self.stemmer.stem(token) for token in filtered_tokens]
    return stemmed_tokens

  def __remove_extra_data(self, data):
    return [[word for word in row if word] for row in data]

  def __create_matrix_from_texts(self, texts, max_len):
    result = np.empty((len(texts), max_len), dtype=object)
    for i, text in enumerate(texts):
      processed_text = self.__preprocess_text(text)
      result[i, :len(processed_text)] = processed_text
    return result

  def __insert_data(self, turning_predictions):
      TurningPrediction.objects.all().delete()
      objects = [
          TurningPrediction(
              turning=row["turning"],
              sarfasl=row["sarfasl"],
              account_group=row["account_group"],
              similarity=row["similarity"],
              title=row["title"]
          )
          for _, row in turning_predictions.iterrows()
      ]
      TurningPrediction.objects.bulk_create(objects)

  def __get_joblib_file(self, file_name):
      return joblib.load(os.path.join(self.__model_path, file_name))

  def __join_lists_to_string(self, df, column_name):
      df[column_name] = [' '.join(row) for row in df[column_name]]
      return df
