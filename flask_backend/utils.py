import configparser
import re

config_parser_dict = {}

class config_parser():

    def __init__(self):
        if not config_parser_dict:
            self.get_config_file_data()

    # This method will read the config file and will write data to a dictionary
    def get_config_file_data(self):
        """ Read config.txt file and store configuration data to a dictionary
                Args:
                   NA
                Return:
                   dictionary of data from config file
        """
        config = configparser.ConfigParser()
        import os
        global config_parser_dict

        config.read_file(open(r'config.txt'))
        config_parser_dict = {s: dict(config.items(s)) for s in config.sections()}

        try:
            config_parser_dict['elasticsearch']['es_dump_auth'] = os.environ['es_dump_auth_header']
            config_parser_dict['elasticsearch']['passw'] = os.environ['es_password']
            config_parser_dict['egnyte']['api_key'] = os.environ['egnyte_api_key']
            config_parser_dict['egnyte']['username'] = os.environ['egnyte_username']
            config_parser_dict['egnyte']['password'] = os.environ['egnyte_password']
            config_parser_dict['scheduler']['schedule_time'] = os.environ['ingest_schedule_time']
            config_parser_dict['redis']['password'] = os.environ['redis_password']
            config_parser_dict['OAuth']['callback_uri'] = os.environ['oauth_callback_uri']
            config_parser_dict['OAuth']['token_url'] = os.environ['oauth_token_url']
            config_parser_dict['OAuth']['client_id'] = os.environ['oauth_client_id']
            config_parser_dict['OAuth']['authorize_url'] = os.environ['oauth_authorize_url']
            config_parser_dict['OAuth']['resource'] = os.environ['oauth_resource']
            config_parser_dict['OAuth']['signout_url'] = os.environ['oauth_signout_url']
            config_parser_dict['generic']['user_logs_excluded_users'] = os.environ['exclude_users']
        except:
            print("Environment Variables missing")

    def get(self, section, item):
        global config_parser_dict
        if config_parser_dict:
            return config_parser_dict.get(section, {}).get(item)
        else:
            self.get_config_file_data()
            return config_parser_dict.get(section, {}).get(item)


def clean_text(text):
    text = text.lower()
    text = text.replace("b'", "")
    text = text.replace("'", "")
    text = text.replace('"', "")
    return text


def sorted_nicely(list):
    """ Sort the given iterable in the way that humans expect."""
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(list, key=alphanum_key)


def generate_doc_id(file_relative_path, file_path_separator):
    doc_id = file_relative_path.replace('/', file_path_separator).rsplit('.', 1)[0].replace(' ', '__')
    data = re.sub(r"[#?\/\\]", "__", doc_id)
    return data
