from elasticsearch_connector import elasticsearch_connector
import utils
from logger import log

logger = log.getLogger()

class file_download_logger():

    # This function logs the event in elastic search using index name download_logs index
    def log_file_download_event(log_data):
        config = utils.config_parser()
        file_download_index = config.get('elasticsearch', 'download_logs_index_name')
        elastic_obj = elasticsearch_connector.get_instance()
        result = elastic_obj.insert_document(file_download_index, "pptx", None, log_data)
        return result

    #  This function extracts doc_id and download count from "download_logs" index and modify download count of all downloaded documents in indexed documents
    def update_download_count_for_all_docs():
        json_data = file_download_logger.get_aggregated_download_count_for_all_downloaded_docs()
        if json_data == []:
            logger.exception("Error to fetch the data from download logs index.")
            return False

        update_failed_list=[]

        for item in json_data:
            update_query = {
                "script" : {
                    "source": "ctx._source.num_downloads = params.num_downloads",
                    "lang": "painless",
                    "params" : {
                        "num_downloads": item["doc_count"]
                    }
                }
            }
            if file_download_logger.update_download_count_for_document(item['key'], update_query):
                logger.info("Updated download count for %s" %(item['key']))
            else:
                update_failed_list.append(item['key'])
                logger.exception("Updating download count is failed for ", item['key'])

        if update_failed_list:
            logger.error("Update download count is failed for %s:" % (update_failed_list))
            return False
        else:
            return True

    # This function gives get the details of aggregated_download_logs when doc_id is present in logs
    def get_aggregated_download_logs(doc_id):
        config = utils.config_parser()
        index_name = config.get('elasticsearch', 'aggregated_download_logs_index_name')
        search_query = {
            "query": {
                "match": {
                    "num_of_downloads.buckets.key": {
                        "query": doc_id
                    }
                }
            }
        }
        es_connector = elasticsearch_connector.get_instance()
        response = es_connector.generic_search_query(index_name, search_query)
        return response

    def update_download_count_for_document(doc_id, update_query):
        config = utils.config_parser()
        corpus_index_name = config.get('elasticsearch', 'corpus_index_name')
        doc_type = config.get('elasticsearch', 'doc_type')
        es_obj = elasticsearch_connector.get_instance()
        try:
            es_obj.update_document(corpus_index_name, doc_type, doc_id, update_query)
            return True
        except:
            logger.exception("Updating download count is failed for %s " % (doc_id))
            return False

    def update_download_count_for_document_by_1(doc_id):
        query = {
            "script":
                {
                    "source": "ctx._source.num_downloads += params.num_downloads",
                    "lang": "painless",
                    "params":
                        {
                            "num_downloads": 1
                        }
                }
        }
        file_download_logger.update_download_count_for_document(doc_id, query)

    # Get the current download count for document. This value is used while indexing document
    def get_download_count_for_document(doc_id):
        config = utils.config_parser()
        index_name = config.get('elasticsearch', 'download_logs_index_name')
        es_obj = elasticsearch_connector.get_instance()
        search_query = {
                        "aggs":
                            {
                            "user_download_aggregation":
                                {
                                    "filter": {"term": {"doc_id": doc_id}},
                                    "aggs":
                                        {
                                            "num_of_downloads": {"terms": {"field": "doc_id.keyword"}}
                                        }
                                }
                            }
                        }
        try:
            json_data = es_obj.generic_search_query(index_name, search_query)
            buckets = json_data['aggregations']["user_download_aggregation"]["num_of_downloads"]["buckets"]
            if buckets:
                return buckets[0]["doc_count"]
            else:
                return 0
        except:
            return 0

    # This function gives aggregated value for doc_id and its download count from download_logs index
    def get_aggregated_download_count_for_all_downloaded_docs():
        config = utils.config_parser()
        index_name= config.get('elasticsearch','download_logs_index_name')
        es_obj = elasticsearch_connector.get_instance()
        aggs_query = {
                        "aggs":
                        {
                             "num_of_downloads":
                            {
                                "terms":
                                     {
                                         "field": "doc_id.keyword",
                                         "size": 10000
                                     }
                            }
                        }
                       }
        try:
            json_data = es_obj.generic_search_query(index_name, aggs_query)
            return json_data['aggregations']['num_of_downloads']['buckets']
        except Exception as e:
            logger.error("Failed to get aggregated download count for all downloaded documents")
            return []

    # Extract download count for each document from download_logs index and update that download count in indexed_documents
    def reset_download_count_for_all_documents(self):
        documents_list = file_download_logger.get_aggregated_download_count_for_all_downloaded_docs()
        for doc in documents_list:
            print(doc['key'])
            print(doc['doc_count'])
            print(doc)

        # Reset/add property for all documents in an index

    def reset_download_count_for_all_indexed_docs(property_name, property_value):
        config = utils.config_parser()
        index_name = config.get("elasticsearch", "corpus_index_name")
        doc_type = config.get("elasticsearch", "doc_type")
        reset_query = {
            "script": {
                "source": "ctx._source." + property_name + "= " + property_value,
                "lang": "painless"
            },
            "query": {
                "match_all": {}
            }
        }
        es_obj = elasticsearch_connector.get_instance()
        return es_obj.update_index_by_query(index_name, doc_type, reset_query)

    if __name__ == '__main__':
        update_download_count_for_all_docs()
