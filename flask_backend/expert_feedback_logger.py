from elasticsearch_connector import elasticsearch_connector
import utils
from logger import log

logger = log.getLogger()


class expert_feedback_logger():
    # This function adds expert feedback on 0 to 4 scale in elastic search using index name provided in config
    def log_expert_feedback(log_data):
        config = utils.config_parser()
        user_feedback_index = config.get('elasticsearch', 'expert_feedback_index_name')
        elastic_obj = elasticsearch_connector.get_instance()
        result = elastic_obj.insert_document(user_feedback_index, "pptx", None, log_data)
        return result
