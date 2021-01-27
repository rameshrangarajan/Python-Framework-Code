from corpus_indexer import corpus_indexer
from keywords_extractor import keywords_extractor
from logger import log
logger = log.getLogger()

class index_keyword_updater():

    def update():
        indexed_doc_result = corpus_indexer.index_all()
        logger.info("Index all Done")
        extract_keywords = keywords_extractor()
        insertkeywords = extract_keywords.refresh_autosuggest_keywords_list()
        logger.info("Keyword Extractor Done")