from pymongo import MongoClient
from sshtunnel import SSHTunnelForwarder

# Подключаемся через SSH-туннель
tunnel = SSHTunnelForwarder(
    ('78.36.44.126', 57381),
    ssh_username='server',
    ssh_password='tppo',
    remote_bind_address=('127.0.0.1', 27017)
)

tunnel.start()

# Подключаемся к MongoDB через локальный порт туннеля
client = MongoClient('127.0.0.1', tunnel.local_bind_port)

# Получаем список баз данных
print("Databases:", client.list_database_names())

# Например, выбираем базу данных 'test'
db = client['test']

# Получаем список коллекций в этой базе данных
print("Collections in 'test':", db.list_collection_names())

# Закрываем соединение
client.close()
tunnel.stop()
