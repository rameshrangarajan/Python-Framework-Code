from elasticsearch_connector import elasticsearch_connector
import utils
from logger import log

logger = log.getLogger()


class autosuggest_feedback_logger():
    # This function adds like/dislike feedback entry in elastic search using index name provided in config
    def log_autosuggest_feedback_event(log_data):
        config = utils.config_parser()
        autosuggest_feedback_index = config.get('elasticsearch', 'autosuggest_feedback_index_name')
        elastic_obj = elasticsearch_connector.get_instance()
        result = elastic_obj.insert_document(autosuggest_feedback_index, "pptx", None, log_data)
        return result
