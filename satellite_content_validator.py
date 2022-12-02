import requests
import json
import getpass
from requests.auth import HTTPBasicAuth
import rpm
import socket

DEBUG = True
CA_CERT = './.certs/katello-server-ca.crt'
#CA_CERT = '/etc/pki/katello/certs/katello-server-ca.crt'
PULP_CERT = './.certs/pulp-client.crt'
#PULP_CERT = '/etc/pki/katello/certs/pulp-client.crt'
PULP_KEY = './.certs/pulp-client.key'
#PULP_KEY = '/etc/pki/katello/private/pulp-client.key'
SATELLITE = 'https://bombsat612.d.sysmgmt.cee.redhat.com'
ORG_ID = []
LCE_ID = {}

def get_username():
    username = input('Enter Satellite WebUI Username: ')
    return username

def get_password():
    password = getpass.getpass()
    return password

def get_credentials():
    creds = {}
    creds['user'] = get_username()
    creds['pw'] = get_password()
    return creds

def get_hostname():
    global SATELLITE 
    SATELLITE = socket.gethostname()

def call_pulp_api(endpoint):
    resp = requests.get(SATELLITE+endpoint, verify=CA_CERT, cert=(PULP_CERT, PULP_KEY))
    return resp

def call_katello_api(endpoint,creds):
    resp = requests.get(SATELLITE+endpoint, verify=CA_CERT, auth = HTTPBasicAuth(creds['user'], creds['pw']))
    return resp

def get_organization_id(creds):
    resp = call_katello_api('/katello/api/organizations', creds).json()['results']
    global ORG_ID
    ORG_ID = []
    for org in resp:
        ORG_ID.append(org['id'])
    return ORG_ID

def get_lce_environments(creds):
    resp = call_katello_api('/katello/api/environments', creds).json()['results']
    global LCE_ID
    LCE_ID = []
    for env in resp:
        LCE_ID.append(env['id'])
    # if len(ORG_ID) > 0:
    #     for org in ORG_ID:
    #         lce_resp = call_katello_api('/katello/api/organizations/'+str(org)+'/environments', creds).json()
    #         LCE_ID[org] = []
    #         for env in lce_resp:
    #             LCE_ID[org].append(env['id'])
    return LCE_ID

def parse_katello_environments(creds):
    katello_environments = []
    get_organization_id(creds)
    get_lce_environments(creds)
    for org in ORG_ID:
        for lce in LCE_ID:
            resp = call_katello_api('/katello/api/organizations/'+str(org)+'/environments/'+str(lce)+'/repositories', creds).json()['results']
            for repo in resp:
                katello_env_repo = {}
                katello_env_repo['backend_identifier'] = repo['backend_identifier']
                katello_env_repo['content_label'] = repo['content_label']
                katello_env_repo['name'] = repo['name']
                katello_env_repo['full_path'] = repo['full_path']
                katello_env_repo['pulp_version_href'] = repo['version_href']
                katello_env_repo['pulp_publication_href'] = repo['publication_href']
                katello_env_repo['rpm_count'] = repo['content_counts']['rpm']
                katello_env_repo['errata_count'] = repo['content_counts']['erratum']
                katello_env_repo['package_group'] = repo['content_counts']['package_group']
                katello_env_repo['srpms'] = repo['content_counts']['srpm']
                katello_env_repo['module_streams'] = repo['content_counts']['module_stream']
                katello_environments.append(katello_env_repo)
    return katello_environments

def print_katello_environments(lce_repos):
    print('Katello Environment Repositories')
    print('This is what is seen from katello api endpoint /katello/api/organizations/<ORGID>/environments/<ENVID>/repositories')
    print('===========================')
    for repo in lce_repos:
        print('**********************************')
        print('Backend ID: %s' % repo['backend_identifier'])
        print('Repo Name: %s' % repo['name'])
        print('Repo Label: %s' % repo['content_label'])
        print('URL: %s' % repo['full_path'])
        print('Pulp Verison href: %s' % repo['pulp_version_href'])
        print('Pulp Publication href: %s' % repo['pulp_publication_href'])
        print('RPMs: %s' % repo['rpm_count'])
        print('Errata: %s' % repo['errata_count'])
        print('Package Groups: %s' % repo['package_group'])
        print('Source RPMs: %s' % repo['srpms'])
        print('Module Streams: %s' % repo['module_streams'])
        print('**********************************')
        print('\n')


def parse_pulp_repos(katello_lce_resp):
    version_href_list = []
    for repo in katello_lce_resp:
        id = {}
        version = call_pulp_api(repo['pulp_publication_href']).json()
        resp = call_pulp_api(version['repository_version']).json()['content_summary']['present']
        id[repo['backend_identifier']] = resp
        id['name'] = repo['name']
        version_href_list.append(id)
    return version_href_list
        
def print_pulp_repo(pulp_repo_resp):
    print('Pulp Repositories')
    print('This is what is seen from pulp api endpoint /pulp/api/v3/distributions/rpm/rpm/<REPOUUID>/versions/<VERSION#>')
    print('===========================')
    for repo in pulp_repo_resp:
        print('**********************************')
        print('Name: %s' % repo['name'])
        for key,value in repo.items():
            if key == 'name':
                continue
            else:
                print('Backend ID: %s' % key)
                print('RPM Advisory: %s' % value['rpm.advisory']['count'])
                print('RPM Package: %s' % value['rpm.package']['count'])
                print('RPM Package Group: %s' % value['rpm.packagegroup']['count'])
        print('**********************************')
        print('\n')

def parse_katello_repos(katello_api_resp):
    katello_repos = []
    for repo in katello_api_resp:
        formatted_output = {}
        formatted_output['name'] = repo['name']
        formatted_output['url'] = repo['full_path']
        formatted_output['version_href'] = repo['version_href']
        formatted_output['content_counts'] = repo['content_counts']
        if repo['last_sync']['result'] == 'success':
            formatted_output['last_sync'] = repo['last_sync']['ended_at']
        else:
            formatted_output['last_sync'] = 'Failed'
        katello_repos.append(formatted_output)
    return katello_repos

def print_katello_repo(katello_repositories):
    print('Katello Repositories')
    print('This is what is seen from katello api endpoint /katello/api/repositories/')
    print('===========================')
    katello_repos = parse_katello_repos(katello_repositories)
    for repo in katello_repos:
        print('**********************************')
        print('Name: %s' % repo['name'])
        print('URL: %s' % repo['url'])
        print('Pulp Version: %s' % repo['version_href'])
        print('Content Count: %s' % json.dumps(repo['content_counts'], indent=4))
        print('Last Sync: %s' % repo['last_sync'])
        print('**********************************')
        print('\n')

def parse_katello_contentviews(katello_api_resp):
    katello_cv= []
    for cv in katello_api_resp:
        formatted_output = {}
        formatted_output['name'] = cv['name']
        for env in cv['environments']:
            lifecycle = []
            lifecycle.append(env['label'])
        formatted_output['lifecycle'] = lifecycle
        formatted_output['rpm_count'] = cv['rpm_count']
        formatted_output['erratum_count'] = cv['erratum_count']
        formatted_output['srpm_count'] = cv['srpm_count']
        formatted_output['module_stream_count'] = cv['module_stream_count']
        try:
            formatted_output['last_event'] = cv['last_event']['action'] + ' : ' + cv['last_event']['task']['result']
        except (AttributeError,TypeError):
            formatted_output['last_event'] = 'None'
        katello_cv.append(formatted_output)
    return katello_cv

def print_katello_cv(katello_cv_resp):
    print('Katello Content Views (including CCVs)')
    print('This is what is seen from katello api endpoint /katello/api/content_view_versions')
    print('======================================')
    katello_cv = parse_katello_contentviews(katello_cv_resp)
    for cv in katello_cv:
        print('**********************************')
        print('Name: %s' % cv['name'])
        print('Lifecycle Environment: %s' % cv['lifecycle'])
        print('RPM Count: %s' % cv['rpm_count'])
        print('Errata: %s' % cv['erratum_count'])
        print('SRPM Count: %s' % cv['srpm_count'])
        print('Module Stream Count: %s' % cv['module_stream_count'])
        print('Last Event: %s' % cv['last_event'])
        print('**********************************')
        print('\n')

def check_rpm(rpmName):
    ts = rpm.TransactionSet()
    mi = ts.dbMatch('name',rpmName)
    return True #REMOVE AFTER TESTING
    #return mi

def main():
    print("Checking for presence of satellite RPM...")
    if check_rpm('satellite'):
        print("Satellite RPM found, continuing...")
        creds = get_credentials()
        
        katello_repo_resp = call_katello_api('/katello/api/repositories/',creds).json()['results']
        print('\n\n')
        print_katello_repo(katello_repo_resp)
        print('Katello Repository Information Gathered')

        katello_cv_resp = call_katello_api('/katello/api/content_view_versions',creds).json()['results']
        print('\n\n')
        print_katello_cv(katello_cv_resp)
        print('Katello Content View Version Information Gathered')

        katello_lce_resp = parse_katello_environments(creds)
        print('\n\n')
        print_katello_environments(katello_lce_resp)
        print('Katello Life Cycle Environment Repositories Gathered')

        pulp_repo_resp = parse_pulp_repos(katello_lce_resp)
        print('\n\n')
        print_pulp_repo(pulp_repo_resp)
        print("Pulp Repository Information Gathered")

    else:
        print("Satellite RPM not detected. Try using 'rpm -qa satellite' to verify.")
        print("Please ensure you are running this on the Satellite server")
        
    

if __name__ == "__main__":
    main()
