from elasticsearch_connector import elasticsearch_connector
import utils


class search_query_logger:

    def log_search_query(log_data):
        config = utils.config_parser()
        search_query_index = config.get('elasticsearch', 'logs_index_name')
        elastic_obj = elasticsearch_connector.get_instance()
        elastic_obj.insert_document(search_query_index, "pptx", None, log_data)