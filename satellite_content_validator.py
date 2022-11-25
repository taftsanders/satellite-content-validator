import requests
import json
import getpass
from requests.auth import HTTPBasicAuth
import pprint


PULP_CA_CERT = '/etc/pki/katello/certs/katello-server-ca.crt'
PULP_CERT = '/etc/pki/katello/certs/pulp-client.crt'
PULP_KEY = '/etc/pki/katello/private/pulp-client.key'
SATELLITE = 'https://bombsat612.d.sysmgmt.cee.redhat.com'

def get_username():
    username = input('Enter Satellite WebUI Username: ')
    return username

def get_password():
    password = getpass.getpass()
    return password

def call_pulp_api(endpoint):
    req = requests.Session()
    req.cert = (PULP_CERT,PULP_KEY)
    resp = req.get(SATELLITE+endpoint)
    return resp

def call_katello_api(endpoint):
    user = get_username()
    pw = get_password()
    resp = requests.get(SATELLITE+endpoint, auth = HTTPBasicAuth(user, pw))
    return resp

def get_rpm_count(repo_version_endpoint):
    resp = call_pulp_api(repo_version_endpoint).json()
    packages = resp['content_summary']['present']['rpm.package']['count']

def parse_katello_repos(katello_api_resp):
    katello_repos = []
    resp = katello_api_resp.json()
    for repo in resp['results']:
        formatted_output = {}
        formatted_output['name'] = repo['name']
        formatted_output['url'] = repo['full_path']
        formatted_output['version_href'] = repo['version_href']
        formatted_output['content_counts'] = repo['content_counts']
        katello_repos.append(formatted_output)
    return katello_repos

def check_satellite_rpm():
    # perform 'rpm -qa satellite' to see if this is a satellite
    print('need to code this')
    return True

def main():
    if check_satellite_rpm():
        katello_repositories = call_katello_api('/katello/api/repositories/')
        katello_repos = parse_katello_repos(katello_repositories)
        print('What Katello Understands')
        print('===========================')
        for repo in katello_repos:
            print('Name: %s' % repo['name'])
            print('URL: %s' % repo['url'])
            print('Pulp Version: %s' % repo['version_href'])
            print('Content Count: %s' % json.dumps(repo['content_counts'], indent=4))
    else:
        print("Satellite RPM not detected using 'rpm -qa satellite'.")
        print("Please run this on the Satellite server")
        
    

if __name__ == "__main__":
    main()
