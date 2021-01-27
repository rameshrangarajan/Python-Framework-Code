import requests
import json
import utils
import jwt

class authorization():

    config = utils.config_parser()
    token_url = config.get('OAuth', 'token_url')
    callback_uri = config.get('OAuth', 'callback_uri')
    client_id = config.get('OAuth', 'client_id')
    authorize_url = config.get('OAuth', 'authorize_url')
    resource = config.get('OAuth', 'resource')

    def getAuthURL(self):
        authorization_redirect_url = self.authorize_url + '?response_type=code&client_id=' + self.client_id + \
                                     '&redirect_uri=' + self.callback_uri + '&resource='+self.resource
        return authorization_redirect_url

    def getAccessToken(self, authorization_code):
        data = {'grant_type': 'authorization_code', 'code': authorization_code, 'redirect_uri': self.callback_uri,
                'client_id': self.client_id}
        access_token_response = requests.post(self.token_url, data=data, verify=False, allow_redirects=False)

        tokens = json.loads(access_token_response.text)
        access_token = tokens['access_token']
        return access_token

    def decode_jwt(self, access_token):
        decoded_token = jwt.decode(access_token, verify=0, algorithm='RS256')
        return decoded_token
