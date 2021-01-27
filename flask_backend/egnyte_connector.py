import utils
import requests
import egnyte
from logger import log
from cryptography.fernet import Fernet

logger = log.getLogger()

class egnyte_connector():
    egnyte_connector_obj = None
    egnyte_client = None

    def get_access_token_from_egnyte():
        """ Get access token from egnyte
            Return:
                 access_token on successful connection
        """
        config = utils.config_parser()

        payload = {
            'grant_type': 'password',
            'client_id': config.get('egnyte', 'api_key'),
            'username': config.get('egnyte', 'username'),
            'password': config.get('egnyte', 'password')
        }
        session = requests.session()
        # post call to connect to egnyte. This will return access token for active session
        access_token_endpoint = config.get('egnyte', 'access_token_endpoint')
        token = session.post(access_token_endpoint, data=payload)
        if token.status_code == 200:
            access_token = (token.text.split(':'))[1].split(',')[0].split('"')[1]
            return access_token
        else:
            logger.exception("Exception getting access token from egnyte due to %s" % token.text)

    def get_access_token_from_config():
        config = utils.config_parser()
        access_token = config.get('egnyte', 'access_token')
        return access_token

    def get_access_token_from_es():
        from elasticsearch_connector import elasticsearch_connector
        es_connect = elasticsearch_connector.get_instance()
        key = b'5Hgi9bhDpDtVg69M7wAjiYYCzr9wlwvWCNlJdp5pWf0='
        cipher_suite = Fernet(key)
        access_token = es_connect.get_egnyte_token()
        if access_token:
            access_token = access_token.encode('utf-8')
            decoded_access_token = cipher_suite.decrypt(access_token)
            return decoded_access_token.decode('utf-8')
        else:
            access_token_from_egnyte = egnyte_connector.get_access_token_from_egnyte()
            encoded_text = cipher_suite.encrypt(str.encode(access_token_from_egnyte))
            es_connect.set_egnyte_token(encoded_text)
            return access_token_from_egnyte

    def get_egnyte_client():
        # access_token = egnyte_connector.get_access_token_from_egnyte()
        egnyte_client_obj = egnyte_connector.egnyte_client
        if egnyte_client_obj is not None:
            logger.info('Already connected to Egnyte')
        else:
            access_token = egnyte_connector.get_access_token_from_es()
            # access_token = egnyte_connector.get_access_token_from_config()
            config = utils.config_parser()
            domain = config.get('egnyte', 'domain')
            try:
                client = egnyte.EgnyteClient({"domain": domain, "access_token": access_token})
                logger.info("Successfully connected to Egnyte")
                return client
            except Exception as e:
                logger.info(e)
                return e


def main():
    # access_token = connect_and_get_access_token()
    # print(access_token)
    egnyte_connect = egnyte_connector()
    eg_config = utils.config_parser()
    access_token = eg_config.get('egnyte','access_token')
    # Connect to egnyte using domain and access token
    client = egnyte.EgnyteClient({"domain": "xoriant.egnyte.com", "access_token": access_token})
    # egnyte_connect.get_files_recursively(client, '/Shared/CMMI/Practice/KnowledgeManagementPlatform/TeamDocs/Knowledgebase/General')
    # egnyte_connect.get_file_downloadable_link('/Shared/CMMI/Practice/KnowledgeManagementPlatform/TeamDocs/Knowledgebase/General/Xoriant Introduction - Campus Recruitments V5.pptx')

if __name__ == '__main__':
    main()