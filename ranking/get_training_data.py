from utils import elastic_connection
import pandas as pd
from utils import expert_feedback_index_name

es = elastic_connection()


def get_data():
    res = es.search(index=expert_feedback_index_name, size=20)
    data_df = []

    for doc in res['hits']['hits']:
        list = []
        source = doc['_source']
        list.append(source["doc_id"])
        list.append(source["search_query"])
        list.append(source["grade"])
        data_df.append(list)

    dataframe = pd.DataFrame(data_df, columns=['doc_id', 'search_query', 'grade'])
    return dataframe
