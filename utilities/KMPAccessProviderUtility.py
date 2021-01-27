import pandas as pd
df = pd.read_excel('admin.xlsx', sheet_name=0)
import requests
from requests.auth import HTTPBasicAuth
from elasticsearch import Elasticsearch

host= "35.234.222.60"
port= "12987"
es_user= "knox_user"
es_passw= "1q2w#E$R"
# es = Elasticsearch([url])
es = Elasticsearch([{'host': host, 'port': port}], http_auth=(es_user, es_passw), 
  scheme="https",ca_certs=False,verify_certs=False)

for index, row in df.iterrows():
    body = {}
    body['role'] = row['role']
    body['email'] = row['email']
    resp = es.index(index='kmp_users',doc_type='_doc', id=row['username'], body=body, refresh='wait_for', request_timeout=30)
    print(resp)

