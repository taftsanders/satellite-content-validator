import requests
import json
import getpass
from requests.auth import HTTPBasicAuth
import rpm
import socket
import os
import tarfile
import time
import shutil

TAR_FILE_NAME = ''

class API_Collector:
    CA_CERT = '/etc/pki/katello/certs/katello-server-ca.crt'
    PULP_CERT = '/etc/pki/katello/certs/pulp-client.crt'
    PULP_KEY = '/etc/pki/katello/private/pulp-client.key'
    SATELLITE = ''
    ORG_ID = []
    LCE_ID = {}
    CAPSULE_ID = []
    CV_ID = []
    CVV_ID = []
    KATELLO_PUBLICATION = []
    PULP_PUBLICATION = []
    PULP_REPOS = []
    SAVE_LOC = '/tmp/'
    FULL_SAVE_LOC = ''
    REQ_LIMIT = 999999

    # Create hostname file
    def create_hostname_file(self):
        self.write_to_file('hostname',self.SATELLITE)

    # Create file location save directory
    def create_folder(self):
        timedate = time.strftime("%Y%m%d-%H%M%S")
        self.FULL_SAVE_LOC = self.SAVE_LOC+'content-collector-'+timedate
        os.mkdir(self.FULL_SAVE_LOC,0o777)

    # File write function
    def write_to_file(self,filename,resp):
        with open(self.FULL_SAVE_LOC+'/'+filename, 'w') as the_file:
            the_file.write(resp)

    # Compress folder function
    def tar_folder(self):
        #timedate = time.strftime("%Y%m%d-%H%M%S")
        with tarfile.open(self.FULL_SAVE_LOC+'.tar.gz', "w:gz") as tar:
            tar.add(self.FULL_SAVE_LOC)
        shutil.rmtree(self.FULL_SAVE_LOC)
        global TAR_FILE_NAME
        TAR_FILE_NAME = self.FULL_SAVE_LOC+'.tar.gz'

    # Get user username        
    def get_username(self):
        username = input('Enter Satellite WebUI Username: ')
        return username

    # Get user password
    def get_password(self):
        password = getpass.getpass()
        return password

    # Call functions to get username and password
    def get_credentials(self):
        creds = {}
        creds['user'] = self.get_username()
        creds['pw'] = self.get_password()
        return creds

    # Get the hostname of the server where executed
    def get_hostname(self):
        self.SATELLITE = socket.gethostname()

    # Pulp API call function
    def call_pulp_api(self,endpoint,hostname=None):
        if hostname:
            resp = requests.get('https://'+hostname+endpoint+'?limit='+str(self.REQ_LIMIT), verify=self.CA_CERT, cert=(self.PULP_CERT, self.PULP_KEY))
            filename = '%s-%s' % (hostname,endpoint.replace('/','-'))
        else:
            resp = requests.get('https://'+self.SATELLITE+endpoint+'?limit='+str(self.REQ_LIMIT), verify=self.CA_CERT, cert=(self.PULP_CERT, self.PULP_KEY))
            filename = '%s-%s' % (self.SATELLITE,endpoint.replace('/','-').rstrip('-'))
        self.write_to_file(filename,resp.text)
        return resp

    # Katello API call function
    def call_katello_api(self,endpoint,creds):
        resp = requests.get('https://'+self.SATELLITE+endpoint+'?per_page='+str(self.REQ_LIMIT), verify=self.CA_CERT, auth = HTTPBasicAuth(creds['user'], creds['pw']))
        filename = '%s-%s' % (self.SATELLITE,endpoint.replace('/','-'))
        self.write_to_file(filename,resp.text)
        return resp

    # Get all organizations
    def get_organization_id(self,creds):
        resp = self.call_katello_api('/katello/api/organizations', creds).json()['results']
        global ORG_ID
        ORG_ID = []
        for org in resp:
            ORG_ID.append(org['id'])
        return ORG_ID
    
    # Get all Lifecycle environments
    def get_lce_environments(self,creds):
        resp = self.call_katello_api('/katello/api/environments', creds).json()['results']
        global LCE_ID
        LCE_ID = []
        for env in resp:
            LCE_ID.append(env['id'])
        return LCE_ID

    # Get all repositories by lifecycles
    def get_repo_by_lce(self,creds):
        for org in ORG_ID:
            for lce in LCE_ID:
                resp = self.call_katello_api('/katello/api/organizations/'+str(org)+'/environments/'+str(lce)+'/repositories', creds).json()['results']
                for repo in resp:
                    self.KATELLO_PUBLICATION.append(repo['publication_href'])

    # Get all repositories
    def get_repositories(self,creds):
        resp = self.call_katello_api('/katello/api/repositories',creds).json()['results']

    # Get all Capsules
    def get_capsule_ids(self,creds):
        resp = self.call_katello_api('/katello/api/capsules',creds).json()['results']
        for id in resp:
            self.CAPSULE_ID.append(id['id'])
        
    # Get all lifecycle environments by Capsule
    def get_capsule_lce(self,creds):
        for cap in self.CAPSULE_ID:
            resp = self.call_katello_api('/katello/api/capsules/'+str(cap)+'/content/lifecycle_environments',creds).json()

    # Get all content views
    def get_content_views(self,creds):
        resp = self.call_katello_api('/katello/api/content_views',creds).json()['results']
        for cv in resp:
            if cv['label'] != "Default_Organization_View":
                self.CV_ID.append(cv['id'])

    # Get content view details per content view
    def get_content_view_detail(self,creds):
        for cv in self.CV_ID:
            resp = self.call_katello_api('/katello/api/content_views/'+str(cv),creds).json()

    # Get all content view versions
    def get_content_view_versions(self,creds):
        resp = self.call_katello_api('/katello/api/content_view_versions',creds).json()['results']
        for cvv in resp:
            self.CVV_ID.append(cvv['id'])

    # Get content view version details for each content view version
    def get_cvv_details(self,creds):
        for version_id in self.CVV_ID:
            resp = self.call_katello_api('/katello/api/content_view_versions/'+str(version_id),creds).json()

    # Get all pulp distributions
    def get_pulp_distributions(self):
        resp = self.call_pulp_api('/pulp/api/v3/distributions/rpm/rpm/').json()['results']
        for dist in resp:
            self.PULP_PUBLICATION.append(dist['publication'])

    # Get all pulp publications from collected distributions
    def get_pulp_publications(self):
        for pub in self.PULP_PUBLICATION:
            resp = self.call_pulp_api(str(pub)).json()
            self.PULP_REPOS.append(resp['repository_version'])

    # Get all pulp repositories from collected publications
    def get_pulp_repoversion(self):
        for repo in self.PULP_REPOS:
            self.call_pulp_api(str(repo)).json()

def main():
    collector = API_Collector()
    creds = collector.get_credentials()
    collector.get_hostname()
    collector.create_folder()
    collector.create_hostname_file()
    collector.get_organization_id(creds)
    collector.get_lce_environments(creds)
    collector.get_repo_by_lce(creds)
    collector.get_repositories(creds)
    collector.get_capsule_ids(creds)
    collector.get_capsule_lce(creds)
    collector.get_content_views(creds)
    collector.get_content_view_detail(creds)
    collector.get_content_view_versions(creds)
    collector.get_cvv_details(creds)
    collector.get_pulp_distributions()
    collector.get_pulp_publications()
    collector.get_pulp_repoversion()
    collector.tar_folder()

if __name__ == "__main__":
    main()
    print('Contents saved as '+TAR_FILE_NAME )