import os
import re
import warnings

import joblib
import numpy as np
import pandas as pd
import pyodbc
from django.conf import settings
from hazm import *
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import LabelEncoder

from ai.models import Customers

warnings.filterwarnings('ignore')


class TextClassifier:
    def __init__(self,customer_id, server, database, username, password, level_number, project_id):
        self.__server = server
        self.__database = database
        self.__username = username
        self.__password = password
        self.__prj = project_id
        self.__lev = level_number

        self.conn = None
        self.stopwords = set(stopwords_list())
        self.stemmer = Stemmer()
        self.normalizer = Normalizer()
        self.vectorizer = CountVectorizer()

        self.__model_path = os.path.join(settings.MEDIA_ROOT, "models")
        self.__customer = Customers.objects.get(pk=customer_id)

    def connect(self):
        try:
            conn_string = (
                f"DRIVER={{SQL Server}};"
                f"SERVER={self.__server};"
                f"DATABASE={self.__database};"
                f"UID={self.__username};"
                f"PWD={self.__password};"
            )
            self.conn = pyodbc.connect(conn_string)
            print("Connected* to the database.")
        except pyodbc.Error as ex:
            print(f"Error connecting to the database: {ex}")



    def close_connection(self):
        if self.conn:
            self.conn.close()
            print("Database connection closed.")

    @staticmethod
    def remove_numbers(text):
        return re.sub(r'\d+', '0,1,2,3,4,5,6,7,8,9', text)

    @staticmethod
    def remove_spaces(string):
        return string.strip()


    @staticmethod
    def remove_extra_data(data):
        return [[word for word in row if word] for row in data]

    @staticmethod
    def create_combined_dataframe(column, data):
        x = pd.Series(column)
        w = data['Category']
        d = data['Sarfasl']
        p = data['Grouh']
        data_ = pd.concat([x, w, d, p], axis=1)
        data_.columns = ['Title', 'Category', 'Sarfasl', 'Grouh']
        return data_

    @staticmethod
    def join_lists_to_string(df, column_name):
        df[column_name] = [' '.join(row) for row in df[column_name]]
        return df

    @staticmethod
    def extract_target_variables(df, target_columns):
        return [df[col] for col in target_columns]

    @staticmethod
    def train_model(x, y):
        model = RandomForestClassifier()
        model.fit(x, y)
        return model

    def train_data(self):
        df = self.execute_query("SELECT * FROM vs_train1")
        self.close_connection()

        encoder1 = LabelEncoder()
        df['Category'] = encoder1.fit_transform(df['Category'])
        joblib.dump(encoder1, self.__model_path + 'encoder1.joblib')

        encoder2 = LabelEncoder()
        df['Sarfasl'] = encoder2.fit_transform(df['Sarfasl'])
        joblib.dump(encoder2, self.__model_path + 'encoder2.joblib')

        encoder3 = LabelEncoder()
        df['Grouh'] = encoder3.fit_transform(df['Grouh'])
        joblib.dump(encoder3, self.__model_path + 'encoder3.joblib')

        df['Title'] = df['Title'].apply(self.remove_numbers)

        df['Title'] = df['Title'].apply(self.remove_spaces)

        texts = df['Title'].values
        preprocessed_texts = self.preprocess_texts(texts)

        preprocessed_texts = self.create_matrix_from_texts(preprocessed_texts)

        preprocessed_texts = np.where(np.array(preprocessed_texts) == None, '',
                                      np.array(preprocessed_texts))

        cleaned_data = self.remove_extra_data(preprocessed_texts)

        df2 = self.create_combined_dataframe(cleaned_data, df)

        df2 = self.join_lists_to_string(df2, 'Title')

        vectorizer = CountVectorizer()
        vec_title = vectorizer.fit_transform(df2.Title)
        joblib.dump(vec_title, self.__model_path + 'vec_title.joblib')

        y1 = df2['Category']
        y2 = df2['Sarfasl']
        y3 = df2['Grouh']

        rf_modely1 = RandomForestClassifier()
        rf_modely1.fit(vec_title, y1)

        rf_modely2 = RandomForestClassifier()
        rf_modely2.fit(vec_title, y2)

        rf_modely3 = RandomForestClassifier()
        rf_modely3.fit(vec_title, y3)

        joblib.dump(rf_modely1, self.__model_path + 'RF_model_y1.joblib')
        joblib.dump(rf_modely2, self.__model_path + 'RF_model_y2.joblib')
        joblib.dump(rf_modely3, self.__model_path + 'RF_model_y3.joblib')
        joblib.dump(vectorizer, self.__model_path + 'vectorizer.joblib')

    def predict_read_data(self):
        query_str = f"SELECT name FROM  Induct.Balance where LevelNumber ={self.__lev}  and ProjectRef  = {self.__prj}"
        data = self.execute_query(query_str)

        x_predict_2 = data['name']

        data['name'] = data['name'].apply(self.remove_numbers)

        data['name'] = data['name'].apply(self.remove_spaces)

        texts = data['name'].values
        preprocessed_texts = self.preprocess_texts(texts)

        preprocessed_texts = self.create_matrix_from_texts(preprocessed_texts)

        preprocessed_texts = np.where(np.array(preprocessed_texts) == None, '',
                                      np.array(preprocessed_texts))

        cleaned_data1 = self.remove_extra_data(preprocessed_texts)

        cleaned_data1 = pd.Series(cleaned_data1)

        x_predict = pd.DataFrame({'name': cleaned_data1})
        x_predict = self.join_lists_to_string(x_predict, 'name')

        loaded_vectorizer = self.get_joblib_file('vectorizer.joblib')
        vec_predict = loaded_vectorizer.transform(x_predict.name)

        rf_modely_1 = self.get_joblib_file("RF_model_y1.joblib")
        rf_modely_1 = rf_modely_1.predict(vec_predict)
        encoder1 = self.get_joblib_file("encoder1.joblib")
        turning = encoder1.inverse_transform(rf_modely_1)

        rf_modely_2 = self.get_joblib_file("RF_model_y2.joblib")
        rf_modely_2 = rf_modely_2.predict(vec_predict)
        encoder2 = self.get_joblib_file("encoder2.joblib")
        sarfasl = encoder2.inverse_transform(rf_modely_2)

        rf_modely_3 = self.get_joblib_file("RF_model_y3.joblib")
        rf_modely_3 = rf_modely_3.predict(vec_predict)
        encoder3 = self.get_joblib_file("encoder3.joblib")
        account_group = encoder3.inverse_transform(rf_modely_3)

        vec_train = self.get_joblib_file('vec_title.joblib')
        similarity = cosine_similarity(vec_predict, vec_train)
        similarity = np.max(similarity, axis=1)
        turning_predictions = pd.DataFrame(
            {
                'turning': turning,
                'sarfasl': sarfasl,
                'account_group': account_group,
                'similarity': similarity,
                'title': x_predict_2
            }
        )

        self.insert_data(turning_predictions)
        self.close_connection()

    def get_joblib_file(self, file_name):
        return joblib.load(os.path.join(self.__model_path, file_name))

