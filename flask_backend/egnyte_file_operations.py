import os

import utils
import sys
from egnyte_connector import egnyte_connector
from elasticsearch_connector import elasticsearch_connector
from logger import log
import re
import requests
import pandas as pd

logger = log.getLogger()


class Egnyte_File_Operations():
    egnyte_file_operations_obj = None
    egnyte_client = None

    def __init__(self):
        if Egnyte_File_Operations.egnyte_file_operations_obj is not None:
            raise Exception("This class is a singleton!")
        else:
            self.egnyte_client = egnyte_connector.get_egnyte_client()
            Egnyte_File_Operations.egnyte_file_operations_obj = self
        self.file_relative_path = {}
        self.file_checksum_value = {}
        self.total_files_count = 0
        self.downloaded_files_count = 0
        self.skipped_files_count = 0
        self.already_indexed_count = 0
        self.file_parsing_details = {}

    @staticmethod
    def get_instance():
        if Egnyte_File_Operations.egnyte_file_operations_obj is None:
            Egnyte_File_Operations()
        return Egnyte_File_Operations.egnyte_file_operations_obj

    def download_a_file(self, file_obj):
        client = self.egnyte_client

        config = utils.config_parser()
        corpus_directory_path = config.get('egnyte', 'corpus_path')
        file_path_separator = config.get('egnyte', 'file_path_separator')
        corpus_index_name = config.get('elasticsearch', 'corpus_index_name')
        config_parser_version = config.get('egnyte', 'parser_version')
        destination_local_path = config.get('generic', 'corpus_download_path')

        try:
            if not os.path.exists(destination_local_path):
                os.mkdir(destination_local_path)
        except Exception as e:
            logger.exception(e)

        relative_path = file_obj.path.split(corpus_directory_path)[1]
        doc_id = utils.generate_doc_id(relative_path, file_path_separator)

        es_connect = elasticsearch_connector.get_instance()
        indexed_parameters = es_connect.return_index_parameter(doc_id, corpus_index_name,
                                                               ['checksum', 'parser_version'])

        # Verify if file already indexed having same checksum and also check for parser version
        if indexed_parameters is False or indexed_parameters['checksum'] != file_obj.checksum or indexed_parameters[
            'parser_version'] < int(config_parser_version):
            # Download the file and get/update checksum if it's not present already
            logger.info("Downloading file %s" % file_obj.name)
            file = client.file(file_obj.path)
            file_resource = file.download()
            file_resource.save_to(destination_local_path + '/' + file_obj.name, )
            logger.info("File %s updating index."%file_obj.name)
            key = destination_local_path + '/' + file_obj.name
            self.file_relative_path[key] = relative_path
            checksum_key = key + 'checksum'
            self.file_relative_path[checksum_key] = file_obj.checksum
            parser_key = key + 'parser_version'
            self.file_relative_path[parser_key] = int(config_parser_version)
            self.downloaded_files_count = self.downloaded_files_count+1
        else:
            self.already_indexed_count = self.already_indexed_count+1
            logger.info("File %s already indexed."%file_obj.name)

    def get_files_recursively(self, source_egnyte_path, list_of_files=None):
        """ Get all pptx files from specified egnyte folder
            Args:
                 client: object of a EgnyteClient
                 source_egnyte_path: egnyte folder path
            Return:
                 None
        """
        try:
            client = self.egnyte_client
            if isinstance(client, Exception):
                return client

            folder = client.folder(source_egnyte_path)
            folder.list()

            # Traverse through all the folders and get files
            for folder_obj in folder.folders:
                if folder_obj.is_folder:
                    Egnyte_File_Operations.get_files_recursively(self, folder_obj.path, list_of_files)
            for file_obj in folder.files:
                self.total_files_count = self.total_files_count+1
                if list_of_files is None:
                    # Download all pptx files
                    if file_obj.name.lower().split(".")[-1] == 'pptx' and file_obj.size > 0:
                        Egnyte_File_Operations.download_a_file(self, file_obj)
                    else:
                        self.skipped_files_count = self.skipped_files_count+1
                        logger.info("Skipping file %s as either it is not pptx or has 0 bytes" %(file_obj.name))
                else:
                    # Download only specific files
                    if file_obj.name.lower().split(".")[-1] == 'pptx' and file_obj.path in list_of_files and file_obj.size > 0:
                        logger.info("Downloading file: %s"% file_obj.name)
                        Egnyte_File_Operations.download_a_file(self, file_obj)
                        list_of_files.remove(file_obj.path)
                        if not list_of_files:
                            return self.file_relative_path

        except Exception as e:
            logger.exception(e)
            return e

        return self.file_relative_path

    def store_event_id_in_index(self, latest_parsed_event_id):
        config = utils.config_parser()
        latest_event_index = config.get('elasticsearch', 'app_data_index')
        es_obj = elasticsearch_connector.get_instance()
        update_event_id = {
            "script":
                {
                    "source": "ctx._source.cursor_event_id = params.cursor_event_id",
                    "params":
                        {
                            "cursor_event_id": latest_parsed_event_id
                        }
                }
        }
        es_obj.update_document(latest_event_index, 'pptx', 'cursor_id', update_event_id)

    def get_event_id_from_index(self):
        config = utils.config_parser()
        latest_event_index = config.get('elasticsearch', 'app_data_index')
        es_obj = elasticsearch_connector.get_instance()
        search_query = {
                        "query": {
                            "match":
                                {
                                    "_id": "cursor_id"
                                }
                            }
                        }

        if es_obj.check_if_index_exists(index_name=latest_event_index):
            json_data = es_obj.generic_search_query(latest_event_index, search_query)
            hits = json_data['hits']['hits']

            if not hits:
                es_obj.insert_document(latest_event_index, 'pptx', 'cursor_id', {'cursor_event_id': 0})
                logger.info("App Data Index Created Successfully")
                return False
            else:
                for hit in hits:
                    hit_source = hit.get('_source')
                    if 'cursor_event_id' in hit_source:
                        latest_event_id = hit_source.get('cursor_event_id')
                        return latest_event_id
        else:
            es_obj.insert_document(latest_event_index, 'pptx', 'cursor_id', {'cursor_event_id': 0})
            logger.info("App Data Index Created Successfully")
            return False

    def download_all_files(self):
        # Initialize counters
        self.total_files_count = 0
        self.downloaded_files_count = 0
        self.skipped_files_count = 0
        self.already_indexed_count = 0

        config = utils.config_parser()
        corpus_directory = config.get('egnyte', 'corpus_path')
        relative_file_path = Egnyte_File_Operations.get_files_recursively(self, corpus_directory)

        self.file_parsing_details['total_files_count'] = self.total_files_count
        self.file_parsing_details['downloaded_files_count'] = self.downloaded_files_count
        self.file_parsing_details['already_indexed_count'] = self.already_indexed_count
        self.file_parsing_details['skipped_files_count'] = self.skipped_files_count

        return relative_file_path, self.file_parsing_details

    #extract filename from event
    def download_file_based_on_event(self):
        client = self.egnyte_client
        config = utils.config_parser()
        access_token = egnyte_connector.get_access_token_from_es()
        corpus_directory_path = config.get('egnyte', 'corpus_path')
        self.downloaded_files_count = 0
        self.already_indexed_count = 0
        self.skipped_files_count = 0
        skipped_events_count = 0
        pptx_file_count = 0
        cursor_event_id = self.get_event_id_from_index()
        file_name = ''
        new_files = []
        if not cursor_event_id:
            head = {'Authorization': 'Bearer {}'.format(access_token)}
            resp = requests.get("https://xoriant.egnyte.com/pubapi/v1/events/cursor", headers=head)
            if resp.status_code == 200:
                cursor_event_id = resp.json().get('oldest_event_id')
                latest_event_id = resp.json().get('latest_event_id')
                self.store_event_id_in_index(latest_event_id)
            else:
                return Exception(resp.content)
        try:
            while cursor_event_id != 0:
                list_of_events = client.events.list(cursor_event_id)
                if not list_of_events and new_files == []:
                    logger.info("No new Files added to Egnyte")
                    return False, False

                list_of_events1 = str(list_of_events).split('>,')
                substrings = ["action: 'create'", "'is_folder': False"]

                for i in range(len(list_of_events1)):
                    if all(word in list_of_events1[i] for word in substrings):
                        if re.findall(r"target_path': '(.+?)', 'target_id", list_of_events1[i]):
                            file_name = re.findall(r"target_path': '(.+?)', 'target_id", list_of_events1[i])[0]
                        elif re.findall(r"target_path': \"(.+?)\", 'target_id", list_of_events1[i]):
                            file_name = re.findall(r"target_path': \"(.+?)\", 'target_id", list_of_events1[i])[0]
                        if file_name.lower()[-4:] == 'pptx':
                            pptx_file_count = pptx_file_count+1
                            new_files.append(file_name)
                        else:
                            skipped_events_count = skipped_events_count+1

                if re.findall(r"/events/(.+?) {action:", list_of_events1[len(list_of_events1)-1]):
                    latest_event_id = re.findall(r"/events/(.+?) {action:", list_of_events1[len(list_of_events1)-1])
                    cursor_event_id = latest_event_id
                else:
                    cursor_event_id = 0

            self.store_event_id_in_index(latest_event_id)
            if new_files:
                relative_file_path = Egnyte_File_Operations.get_files_recursively(self, corpus_directory_path, new_files)

                self.file_parsing_details['new_files'] = pptx_file_count
                self.file_parsing_details['downloaded_files_count'] = self.downloaded_files_count
                self.file_parsing_details['already_indexed_count'] = self.already_indexed_count
                self.file_parsing_details['skipped_files_count'] = self.skipped_files_count
                self.file_parsing_details['skipped_events_count'] = skipped_events_count

                return relative_file_path, self.file_parsing_details
            else:
                logger.info("No new Files added to Egnyte")
                return False, False
        except Exception as e:
            return e, False

    def download_files_based_on_trigger(self, egnyte_uploaded_files):
        config = utils.config_parser()
        corpus_directory_path = config.get('egnyte', 'corpus_path')
        list_of_egnyte_files = egnyte_uploaded_files.split(',')
        count_of_files = len(list_of_egnyte_files)
        self.downloaded_files_count = 0
        self.already_indexed_count = 0
        self.skipped_files_count = 0

        for index, file in enumerate(list_of_egnyte_files):
            if corpus_directory_path not in file:
                list_of_egnyte_files[index] = corpus_directory_path + file

        relative_file_path = Egnyte_File_Operations.get_files_recursively(self, corpus_directory_path, list_of_egnyte_files)

        self.file_parsing_details['count_of_files'] = count_of_files
        self.file_parsing_details['downloaded_files_count'] = self.downloaded_files_count
        self.file_parsing_details['already_indexed_count'] = self.already_indexed_count
        self.file_parsing_details['skipped_files_count'] = self.skipped_files_count

        return relative_file_path, self.file_parsing_details

    def get_file_navigation_link(egnyte_file_path):
        """ Get downloadable link for specified file
            Args:
                 egnyte_file_path: egnyte path for a file
            Return:
                 file_download_link: A link to navigate to a file
        """
        file_navigation_link = 'https://xoriant.egnyte.com/navigate/path' + egnyte_file_path
        return file_navigation_link

    def write_file_details_to_csv(self, corpus_directory_path):
        """ Get file names and modification dates from egnyte folder
            Return:
                 Create a CSV file with file name and associated modification date sorted by modification date
        """
        try:
            client = self.egnyte_client
            folder = client.folder(corpus_directory_path)
            folder.list()

            file_data = pd.DataFrame()
            file_name = []
            modified_date = []

            # Traverse through all the folders and get file details
            for folder_obj in folder.folders:
                if folder_obj.is_folder:
                    Egnyte_File_Operations.write_file_details_to_csv(self, folder_obj.path)
            for file_obj in folder.files:
                # Get data only for pptx files
                if file_obj.name.lower().split(".")[-1] == 'pptx':
                    file_name.append(file_obj.name)
                    if file_obj.last_modified:
                        modified_date.append(file_obj.last_modified)
                    else:
                        modified_date.append("None")

            file_data['file_name'] = file_name
            file_data['last_modified'] = pd.to_datetime(modified_date)
            file_data = file_data.sort_values('last_modified', ascending=False)
            file_data.to_csv("file_name_sorted_by_modified_date.csv", mode='a')

        except:
            logger.exception("Error getting files from Egnyte")


if __name__ == '__main__':
    egnyte_FO = Egnyte_File_Operations.get_instance()
    # config = utils.config_parser()
    # corpus_directory_path = config.get('egnyte', 'corpus_path')
    # egnyte_FO.write_file_details_to_csv(corpus_directory_path)
    egnyte_FO.get_event_id_from_index()
    # egnyte_FO.download_file_based_on_event()
    # egnyte_FO.get_event_id_from_index()
