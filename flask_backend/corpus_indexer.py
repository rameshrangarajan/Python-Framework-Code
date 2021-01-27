# -*- coding: utf-8 -*-
"""
Created on Thu Sep  5 17:56:45 2019

@author: godbole_s
"""
import os
from datetime import datetime
import utils
from elasticsearch_connector import elasticsearch_connector
from ppt_parser import ppt_parser
from egnyte_file_operations import Egnyte_File_Operations
import shutil
from logger import log

logger = log.getLogger()

class corpus_indexer():
    
    def parse_and_index_documents(path, elasticsearch_connector, corpus_index, file_relative_path):
        indexed_doc_result = []
        number_of_indexed_files = 0
        no_of_files_having_indexing_error = 0
        files_having_indexing_error = []
        # Checking if the directory exist and it is not blank
        config = utils.config_parser()
        file_path_separator = config.get('egnyte', 'file_path_separator')
        doc_type = config.get('elasticsearch', 'doc_type')
        if os.path.isdir(path) and os.listdir(path):
            for dirName, subdirList, fileList in os.walk(path):
                # Traversing through the directory to insert all the pptx files in elastic search
                for file in fileList:
                    if file.lower().endswith('.pptx') and not file.startswith('~$'):
                        file_path = dirName + '/' + file
                        file_data = ppt_parser.parse(file_path, file_relative_path)
                        if file_data is not None:
                            doc_id = utils.generate_doc_id(file_data['source_path'], file_path_separator)
                            result = elasticsearch_connector.insert_document(corpus_index, doc_type, doc_id, file_data)
                            indexed_doc_result.append(result)
                            number_of_indexed_files = number_of_indexed_files+1
                        else:
                            no_of_files_having_indexing_error = no_of_files_having_indexing_error+1
                            files_having_indexing_error.append(file_relative_path.get(file_path))
                            logger.error("Failed to index document %s" % file_relative_path.get(file_path))
        else:
            logger.error("Either directory does not exist or directory is blank")
        return number_of_indexed_files, no_of_files_having_indexing_error, files_having_indexing_error

    def download_corpus_documents():
        egnyte = Egnyte_File_Operations.get_instance()
        file_relative_path, file_parsing_details = egnyte.download_all_files()
        return file_relative_path, file_parsing_details

    def download_event_based_corpus_documents():
        egnyte = Egnyte_File_Operations.get_instance()
        file_relative_path, file_parsing_details = egnyte.download_file_based_on_event()
        return file_relative_path, file_parsing_details

    def download_trigger_based_corpus_documents(egnyte_uploaded_files):
        config = utils.config_parser()
        destination_local_path = config.get('generic', 'corpus_download_path')
        egnyte = Egnyte_File_Operations.get_instance()
        file_relative_path, file_parsing_details = egnyte.download_files_based_on_trigger(egnyte_uploaded_files)
        return file_relative_path, file_parsing_details

    # Parse downloaded documents
    def parse_documents(file_relative_path):
        config = utils.config_parser()
        destination_local_path = config.get('generic', 'corpus_download_path')
        try:
            es_connect = elasticsearch_connector.get_instance()
            # es_connect.clear_index()
        except:
            logger.exception("Cannot connect to elastic search")
        config = utils.config_parser()
        corpus_index = config.get('elasticsearch', 'corpus_index_name')
        number_of_indexed_files, no_of_files_having_indexing_error, files_having_indexing_error = \
            corpus_indexer.parse_and_index_documents(destination_local_path, es_connect, corpus_index, file_relative_path)
        corpus_indexer.clear_corpus_download_directory(destination_local_path)
        return number_of_indexed_files, no_of_files_having_indexing_error, files_having_indexing_error

    def index_all():
        file_relative_path, file_parsing_details = corpus_indexer.download_corpus_documents()

        if isinstance(file_relative_path, Exception):
            return file_relative_path
        else:
            number_of_indexed_files, no_of_files_having_indexing_error, files_having_indexing_error = corpus_indexer.parse_documents(file_relative_path)
            logger.info("Total Number of files available on Egnyte: %d" % file_parsing_details['total_files_count'])
            logger.info("Number of files Downloaded for parsing: %d" % file_parsing_details['downloaded_files_count'])
            logger.info("Number of files already parsed: %d" % file_parsing_details['already_indexed_count'])
            logger.info("Number of files Skipped due to other format or size 0: %d" % file_parsing_details['skipped_files_count'])
            logger.info("Number of files newly ingested in ES: %d" % number_of_indexed_files)
            logger.info("Number of files having error in ingestion: %d" % no_of_files_having_indexing_error)
            logger.info("List of files having error in ingestion: {}" .format(', '.join(map(str, files_having_indexing_error))))

    def index_based_on_event():
        file_relative_path, file_parsing_details = corpus_indexer.download_event_based_corpus_documents()

        if isinstance(file_relative_path, Exception):
            return file_relative_path
        else:
            if file_relative_path:
                number_of_indexed_files, no_of_files_having_indexing_error, files_having_indexing_error = corpus_indexer.parse_documents(file_relative_path)
                logger.info("Number of newly added pptx files: %d" % file_parsing_details['new_files'])
                logger.info("Number of files downloaded for parsing: %d" % file_parsing_details['downloaded_files_count'])
                logger.info("Number of files already parsed: %d" % file_parsing_details['already_indexed_count'])
                logger.info("Number of files Skipped due to size 0: %d" % file_parsing_details['skipped_files_count'])
                logger.info("Number of events skipped due to other file format: %d" % file_parsing_details['skipped_events_count'])
                logger.info("Number of files newly ingested in ES: %d" % number_of_indexed_files)
                logger.info("Number of files having error in ingestion: %d" % no_of_files_having_indexing_error)
                logger.info("List of files having error in ingestion: {}".format(', '.join(map(str, files_having_indexing_error))))
            else:
                return False

    def index_based_on_trigger(egnyte_uploaded_files):
        file_relative_path, file_parsing_details = corpus_indexer.download_trigger_based_corpus_documents(egnyte_uploaded_files)

        if isinstance(file_relative_path, Exception):
            return file_relative_path
        else:
            number_of_indexed_files, no_of_files_having_indexing_error, files_having_indexing_error = corpus_indexer.parse_documents(file_relative_path)
            logger.info("Number of files requested for parsing: %d" % file_parsing_details['count_of_files'])
            logger.info("Number of files Downloaded for parsing: %d" % file_parsing_details['downloaded_files_count'])
            logger.info("Number of files already parsed: %d" % file_parsing_details['already_indexed_count'])
            logger.info("Number of files Skipped due to other format or size 0: %d" % file_parsing_details['skipped_files_count'])
            logger.info("Number of files newly ingested in ES: %d" % number_of_indexed_files)
            logger.info("Number of files having error in ingestion: %d" % no_of_files_having_indexing_error)
            logger.info("List of files having error in ingestion: {}".format(', '.join(map(str, files_having_indexing_error))))

    # Delete the corpus download directory once all corpus are indexed.
    def clear_corpus_download_directory(corpus_download_directory):
        if os.path.isdir(corpus_download_directory):
            shutil.rmtree(corpus_download_directory)
        else:
            logger.info('Directory not found at %s'%corpus_download_directory)


def main():
    corpus_indexer.index_based_on_event()

if __name__ == '__main__':
    main()
