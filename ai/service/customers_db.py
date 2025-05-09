import pyodbc

from ai.models import Customers, CustomerData


class CustomersDBService:
    def __init__(self, customer_id:int):
        self.__customer = Customers.objects.get(id=customer_id)
        self.__engine = 'django.db.backends.mysql'

    def execute(self):
        self.__update_customer_data()

    def __update_customer_data(self):
        names = self.__fetch_data_from_sqlserver()
        customer_data_objs = [CustomerData(customer=self.__customer, name=name) for name in names]

        CustomerData.objects.filter(customer=self.__customer).delete()
        CustomerData.objects.bulk_create(customer_data_objs)

    def __fetch_data_from_sqlserver(self):
        query_str = f"SELECT name FROM Induct.Balance WHERE LevelNumber = {self.__customer.level_number} AND ProjectRef = {self.__customer.project_id}"

        try:
            conn = self.__get_sqlserver_connection()
            cursor = conn.cursor()
            cursor.execute(query_str)
            rows = cursor.fetchall()
            conn.close()
        except Exception as e:
            return []
        return [row[0] for row in rows]  # Extract name column

    def __get_sqlserver_connection(self):
        conn_str = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={self.__customer.host};"
            f"DATABASE={self.__customer.database_name};"
            f"UID={self.__customer.user};"
            f"PWD={self.__customer.get_password()};"
            "TrustServerCertificate=yes;"  # Add this line
            "Encrypt=yes;"  # Make sure encryption is enabled
        )
        return pyodbc.connect(conn_str)