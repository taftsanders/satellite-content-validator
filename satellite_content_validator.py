import requests
import json
import getpass
from requests.auth import HTTPBasicAuth
import rpm
import socket

DEBUG = True
CA_CERT = '/etc/pki/katello/certs/katello-server-ca.crt'
PULP_CERT = '/etc/pki/katello/certs/pulp-client.crt'
PULP_KEY = '/etc/pki/katello/private/pulp-client.key'
SATELLITE = ''
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

def call_pulp_api(endpoint,hostname=None):
    if hostname:
        resp = requests.get('https://'+hostname+endpoint, verify=CA_CERT, cert=(PULP_CERT, PULP_KEY))
    else:
        resp = requests.get('https://'+SATELLITE+endpoint, verify=CA_CERT, cert=(PULP_CERT, PULP_KEY))
    return resp

def call_katello_api(endpoint,creds):
    resp = requests.get('https://'+SATELLITE+endpoint, verify=CA_CERT, auth = HTTPBasicAuth(creds['user'], creds['pw']))
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
        resp = call_pulp_api(version['repository_version']).json()
        id[repo['backend_identifier']] = resp['content_summary']['present']
        id['name'] = repo['name']
        id['respository_version'] = version['repository_version']
        version_href_list.append(id)
    return version_href_list
        
def print_rpm_pulp_repo(pulp_repo_resp):
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
                try:
                    print('RPM Advisory: %s' % value.get('rpm.advisory').get('count'))
                except (KeyError,AttributeError,TypeError):
                    print('RPM Advisory: 0')
                try:
                    print('RPM Package: %s' % value.get('rpm.package')['count'])
                except (KeyError,AttributeError,TypeError):
                    print('RPM Package: 0')
                try:
                    print('RPM Package Group: %s' % value['rpm.packagegroup']['count'])
                except (KeyError,AttributeError,TypeError):
                    print('RPM Package Group: 0')
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
        if repo['last_sync']:
            formatted_output['last_sync_status'] = repo['last_sync']['state']+' : '+repo['last_sync']['result']
            formatted_output['last_sync_finished_at'] = repo['last_sync']['ended_at']
        elif not repo['last_sync']:
            formatted_output['last_sync_status'] = 'Never Synced'
            formatted_output['last_sync_finished_at'] = 'None'
        katello_repos.append(formatted_output)
    return katello_repos

def print_katello_repo(creds):
    katello_repositories = call_katello_api('/katello/api/repositories/',creds).json()['results']
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
        print('Last Sync Task: %s' % repo['last_sync_status'])
        print('    Finished At: %s' % repo['last_sync_finished_at'])
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

def print_katello_cv(creds):
    katello_cv_resp = call_katello_api('/katello/api/content_view_versions',creds).json()['results']
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
    for package in mi:
        sat_version = '%s-%s-%s' % (package['name'],package['version'],package['release'])
    return sat_version

def get_capsule_ids(creds):
    cap_ids = []
    resp = call_katello_api('/katello/api/capsules',creds).json()['results']
    for capsule in resp:
        cap = {}
        if capsule['id'] != 1:
            cap['id'] = capsule['id']
            cap['name'] = capsule['name']
            cap_ids.append(cap)
    return cap_ids

def parse_capsule_env(capsule_env,orgs,creds):
    lce_by_org = {}
    for orgid in orgs:
        lce_by_org[str(orgid)] = []
        for lce in capsule_env:
            if orgid == lce['organization_id']:
                env = {}
                env['id'] = lce['id']
                env['name'] = lce['name']
                env['label'] = lce['label']
                env['organization'] = lce['organization']['name']
                env['host_count'] = lce['counts']['content_hosts']
                env['cv_count'] = lce['counts']['content_views']
                env['content_views'] = []
                for cv in lce['content_views']:
                    cv_versions = call_katello_api('/katello/api/content_views/'+str(cv['id']),creds).json()['versions']
                    for version_id in cv_versions:
                        if lce['id'] in version_id['environment_ids']:
                            cv_ver_resp = call_katello_api('/katello/api/content_view_versions/'+str(version_id['id']),creds).json()
                            formatted_output = {}
                            formatted_output['name'] = cv_ver_resp['name']
                            for environment in cv_ver_resp['environments']:
                                if environment['id'] == lce['id']:
                                    formatted_output['lifecycle'] = environment['name']
                                    try:
                                        formatted_output['rpm_count'] = cv_ver_resp['rpm_count']
                                    except KeyError:
                                        formatted_output['rpm_count'] = '0'
                                    try:
                                        formatted_output['erratum_count'] = cv_ver_resp['erratum_count']
                                    except KeyError:
                                        formatted_output['erratum_count'] = '0'
                                    try:
                                        formatted_output['srpm_count'] = cv_ver_resp['srpm_count']
                                    except KeyError:
                                        formatted_output['srpm_count'] = '0'
                                    try:
                                        formatted_output['module_stream_count'] = cv_ver_resp['module_stream_count']
                                    except KeyError:
                                        formatted_output['module_stream_count'] = '0'
                                    try:
                                        formatted_output['last_event'] = cv_ver_resp['last_event']['action'] + ' : ' + cv_ver_resp['last_event']['task']['result']
                                    except (KeyError,AttributeError,TypeError):
                                        formatted_output['last_event'] = 'None'
                            env['content_views'].append(formatted_output)
                lce_by_org[str(orgid)].append(env)
    return lce_by_org

def get_capsule_lce(creds):
    cap_id = get_capsule_ids(creds)
    all_capsules = []
    for cap in cap_id:
        orgs = set()
        resp = call_katello_api('/katello/api/capsules/'+str(cap['id'])+'/content/lifecycle_environments',creds).json()['results']
        for env in resp:
            orgs.add(env['organization_id'])
        capsule = {}
        capsule['name'] = cap['name']
        capsule['lce'] = parse_capsule_env(resp,orgs,creds)
        all_capsules.append(capsule)
    return all_capsules


def print_capsule_katello_repo(creds):
    capsules = get_capsule_lce(creds)
    for capsule in capsules:
        print('##########################################')
        print('Capsule Name: %s' % capsule['name'])
        for key,value in capsule['lce'].items():
            for lce in value:
                print('*********************')
                print('- Org Name: %s' % lce['organization'])
                print('  Org ID: %s' % key)
                print('  - LCE ID: %s' % lce['id'])
                print('    LCE Name: %s' % lce['name'])
                print('    LCE Host Count: %s' % lce['host_count'])
                print('    Content Views:')
                for cv in lce['content_views']:
                    print('    - Name: %s' % cv['name'])
                    print('      RPM Count: %s' % cv['rpm_count'])
                    print('      Errata Count: %s' % cv['erratum_count'])
                    print('      SRPM Count: %s' % cv['srpm_count'])
                    print('      Module Stream Count: %s' % cv['module_stream_count'])
                    print('      Last Event: %s ' % cv['last_event'])
                print('*********************')
                print('\n')
        print('##########################################')
        print('\n')

def get_capsule_pulp_repos(creds,katello_lce_resp):
    all_capsules = get_capsule_ids(creds)
    capsule_names = []
    for capsule in all_capsules:
        if capsule['id'] != 1:
            capsule_names.append(capsule['name'])
    for capsule in capsule_names:
        capsule_repos = []
        distribution = call_pulp_api('/pulp/api/v3/distributions/rpm/rpm/',capsule).json()['results']
        for dist in distribution:
            for repo in katello_lce_resp:
                if dist['name'] == repo['backend_identifier']:
                    formatted_output = {}
                    formatted_output['name'] = repo['name']
                    formatted_output['backend_id'] = repo['backend_identifier']
                    publication = call_pulp_api(dist['publication'],capsule).json()
                    repo_version = call_pulp_api(publication['repository_version'],capsule).json()
                    formatted_output['content_summary'] = repo_version['content_summary']['present']
                    capsule_repos.append(formatted_output)
    return capsule_repos

def print_capsule_pulp_repo(creds,katello_lce_resp):
    capsule_pulp_repos = get_capsule_pulp_repos(creds,katello_lce_resp)
    print('Pulp Repositories')
    print('This is what is seen from pulp api endpoint /pulp/api/v3/distributions/rpm/rpm/<REPOUUID>/versions/<VERSION#>')
    print('===========================')
    for repo in capsule_pulp_repos:
        print('**********************************')
        print('Name: %s' %repo['name'])
        print('Backend ID: %s' %repo['backend_id'])
        print('RPM Advisory: %s' %repo.get('content_summary')['rpm.advisory']['count'])
        print('RPM Package: %s' %repo.get('content_summary')['rpm.package']['count'])
        print('RPM Package Group: %s' %repo.get('content_summary')['rpm.packagegroup']['count'])
        print('**********************************')
        print('\n')

def print_all_repositories(creds):
    print('Gathering Katello Repository Information From Satellite')
    print('\n\n')
    print_katello_repo(creds)
    print('Katello Repository Information Gathered From Satellite')

    print('Gathering Katello Content View Version Infromation From Satellite')
    print('\n\n')
    print_katello_cv(creds)
    print('Katello Content View Version Information Gathered From Satellite')

    katello_lce_resp = parse_katello_environments(creds)
    print('Gathering Katello Life Cycle Environment Repositories From Satellite')
    print('\n\n')
    print_katello_environments(katello_lce_resp)
    print('Katello Life Cycle Environment Repositories Gathered From Satellite')

    pulp_repo_resp = parse_pulp_repos(katello_lce_resp)
    print('Gathering Pulp Repository Information From Satellite')
    print('\n\n')
    print_rpm_pulp_repo(pulp_repo_resp)
    print('Pulp Repository Information Gathered From Satellite')

    print('Gathering Capsule Content From Katello/Satellite')
    print('\n\n')
    print_capsule_katello_repo(creds)
    print('Capsule Content From Katello/Satellite Gathered')

    print('Gathering Capsule Content From Capsule\'s Pulp')
    print('\n\n')
    print_capsule_pulp_repo(creds,katello_lce_resp)
    print('Capsule Content From Capsule\'s Pulp Gathered')


def main():
    print("Checking for presence of satellite RPM...")
    if check_rpm('satellite'):
        print("Satellite RPM found, continuing...")
        global SATELLITE
        if not SATELLITE:
            get_hostname()
        creds = get_credentials()
        print_all_repositories(creds)
    else:
        print("Satellite RPM not detected. Try using 'rpm -qa satellite' to verify.")
        print("Please ensure you are running this on the Satellite server")
        

if __name__ == "__main__":
    main()
