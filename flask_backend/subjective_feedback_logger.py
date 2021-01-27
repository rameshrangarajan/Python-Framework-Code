from elasticsearch_connector import elasticsearch_connector
import utils
from logger import log

logger = log.getLogger()


class subjective_feedback_logger():
    # This function adds subjective feedback to elasticsearch using index name provided in config
    def log_subjective_feedback(payload_data):

        config = utils.config_parser()
        subjective_feedback_index = config.get('elasticsearch', 'subjective_feedback_index')
        elastic_obj = elasticsearch_connector.get_instance()
        response = elastic_obj.insert_document(subjective_feedback_index, "pptx", None, payload_data)
        return response