import json
import rpm
import os
import tarfile
import glob

FILE_LOC = '/home/rdu/tasander/git/satellite-content-validator/.certs/content-collector-20230108-140500.tar.gz'
SAVE_LOC = '/tmp'
ALL_FILES = []
HOSTNAME = ''

def decompress_file():
    api_files = tarfile.open(FILE_LOC)
    api_files.extractall(SAVE_LOC)
    api_files.close()
    os.chdir(glob.glob(SAVE_LOC+'/tmp/content-collector-*/')[0])
    global ALL_FILES
    ALL_FILES = os.listdir()
    read_hostname_file()

def read_hostname_file():
    global HOSTNAME
    with open('hostname', 'r') as the_file:
        HOSTNAME = the_file.read()

def parse_katello_environments():
    katello_environments = []
    for file in glob.glob(HOSTNAME+'--katello-api-organizations-*-environments-*-repositories'):
        with open(file,'r') as the_file:
            for repo in json.load(the_file)['results']:
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

def parse_pulp_repos():
    version_href_list = []
    for file in glob.glob(HOSTNAME+'--pulp-api-v3-repositories-rpm-rpm-*-version-*'):
        with open(file,'r') as the_file:
            repo=json.load(the_file)
            id = {}
            id['pulp_href'] = repo['repository']
            id['version'] = repo['number']
            id['content_summary'] = repo['content_summary']
            version_href_list.append(id)
    return version_href_list
        
def print_rpm_pulp_repo(pulp_repo_resp):
    print('Pulp Repositories')
    print('This is what is seen from pulp api endpoint /pulp/api/v3/distributions/rpm/rpm/<REPOUUID>/versions/<VERSION#>')
    print('===========================')
    for repo in pulp_repo_resp:
        print('**********************************')
        print('Name: %s' % repo['pulp_href'])
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
                    print('RPM Package Group: %s' % value.get('rpm.packagegroup')['count'])
                except (KeyError,AttributeError,TypeError):
                    print('RPM Package Group: 0')
        print('**********************************')
        print('\n')

def parse_katello_repos():
    katello_repos = []
    with open(HOSTNAME+'--katello-api-repositories','r') as the_file:
        for repo in json.load(the_file)['results']:
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

def print_katello_repo():
    print('Katello Repositories')
    print('This is what is seen from katello api endpoint /katello/api/repositories/')
    print('===========================')
    katello_repos = parse_katello_repos()
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

def parse_katello_contentviews():
    katello_cv= []
    with open(HOSTNAME+'--katello-api-content_view_versions','r') as the_file:
        for cvv in json.load(the_file)['results']:
            formatted_output = {}
            formatted_output['name'] = cvv['name']
            for env in cvv['environments']:
                lifecycle = []
                lifecycle.append(env['label'])
            formatted_output['lifecycle'] = lifecycle
            formatted_output['rpm_count'] = cvv['rpm_count']
            formatted_output['erratum_count'] = cvv['erratum_count']
            formatted_output['srpm_count'] = cvv['srpm_count']
            formatted_output['module_stream_count'] = cvv['module_stream_count']
            try:
                formatted_output['last_event'] = cvv['last_event']['action'] + ' : ' + cvv['last_event']['task']['result']
            except (AttributeError,TypeError):
                formatted_output['last_event'] = 'None'
            katello_cv.append(formatted_output)
    return katello_cv

def print_katello_cv():
    print('Katello Content Views (including CCVs)')
    print('This is what is seen from katello api endpoint /katello/api/content_view_versions')
    print('======================================')
    katello_cv = parse_katello_contentviews()
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

def get_capsule_ids():
    cap_ids = []
    with open(HOSTNAME+'--katello-api-capsules','r') as the_file:
        for capsule in json.load(the_file)['results']:
            cap = {}
            # Satellite id is always 1, removing from parsing
            if capsule['id'] != 1:
                cap['id'] = capsule['id']
                cap['name'] = capsule['name']
                cap_ids.append(cap)
    return cap_ids

def parse_capsule_env(capsule_env,orgs):
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
                for file in glob.glob(HOSTNAME+'--katello-api-content_views-*'):
                    with open(file,'r') as the_file:
                        for contentview in json.load(the_file)['versions']:
                            if lce['id'] in contentview['environment_ids']:
                                with open(HOSTNAME+'--katello-api-content_view_versions-'+str(contentview['id'])) as the_file:
                                    cv_ver_resp = json.load(the_file)
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

def get_capsule_lce():
    cap_id = get_capsule_ids()
    all_capsules = []
    for cap in cap_id:
        orgs = set()
        for file in glob.glob(HOSTNAME+'--katello-api-capsules-*-content-lifecycle_environments'):
            # Satellite is always id=1 and "This request may only be performed on a Capsule that has the Pulpcore feature with mirror=true."
            if file != HOSTNAME+'--katello-api-capsules-1-content-lifecycle_environments':
                with open(file,'r') as the_file:
                    capsule_env = json.load(the_file)['results']
                    for env in capsule_env:
                        orgs.add(env['organization_id'])
                        capsule = {}
                        capsule['name'] = cap['name']
                        capsule['lce'] = parse_capsule_env(capsule_env,orgs)
                        all_capsules.append(capsule)
    return all_capsules


def print_capsule_katello_repo():
    capsules = get_capsule_lce()
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

def get_capsule_pulp_repos(katello_lce_resp):
    all_capsules = get_capsule_ids()
    capsule_names = []
    for capsule in all_capsules:
        # Satellite is id=1, this is for parsing non-Satellite Capsules
        if capsule['id'] != 1:
            capsule_names.append(capsule['name'])
    for capsule in capsule_names:
        capsule_repos = []
        with open(HOSTNAME+'--pulp-api-v3-distributions-rpm-rpm', 'r') as the_file:
            for dist in json.load(the_file)['results']:
                for repo in katello_lce_resp:
                    if dist['publication'] == repo['pulp_publication_href']:
                        formatted_output = {}
                        formatted_output['name'] = repo['name']
                        formatted_output['katello_backend_id'] = repo['backend_identifier']
                        publication = HOSTNAME+'-'+dist['publication'].replace('/','-').rstrip('-')
                        with open(publication, 'r') as pub_file:
                            publication_file = json.load(pub_file)
                            repository_version = HOSTNAME+'-'+publication_file['repository_version'].replace('/','-').rstrip('-')
                        with open(repository_version, 'r') as repov_file:
                            repo_version = json.load(repov_file)
                            formatted_output['content_summary'] = repo_version['content_summary']['present']
                            capsule_repos.append(formatted_output)
    return capsule_repos

def print_capsule_pulp_repo(katello_lce_resp):
    capsule_pulp_repos = get_capsule_pulp_repos(katello_lce_resp)
    print('Pulp Repositories')
    print('This is what is seen from pulp api endpoint /pulp/api/v3/distributions/rpm/rpm/<REPOUUID>/versions/<VERSION#>')
    print('===========================')
    for repo in capsule_pulp_repos:
        print('**********************************')
        print('Name: %s' %repo['name'])
        print('Backend ID: %s' %repo['katello_backend_id'])
        # repos can not be synced and have '{}' as the content summary
        if repo.get('content_summary'):
            # repos can possibly not have advisories, package, packagegroup
            if repo['content_summary'].get('rpm.advisory'):
                print('RPM Advisory: %s' %repo['content_summary']['rpm.advisory']['count'])
            if repo['content_summary'].get('rpm.package'):
                print('RPM Package: %s' %repo['content_summary']['rpm.package']['count'])
            if repo['content_summary'].get('rpm.packagegroup'):
                print('RPM Package Group: %s' %repo['content_summary']['rpm.packagegroup']['count'])
        else:
            print('RPM Advisory: {}')
            print('RPM Package: {}')
            print('RPM Package Group: {}')
        print('**********************************')
        print('\n')

def print_all_repositories():
    print('Parsing Katello Repository Information From Satellite')
    print('\n\n')
    print_katello_repo()
    print('Katello Repository Information Parsed')

    print('Parsing Katello Content View Version Infromation From Satellite')
    print('\n\n')
    print_katello_cv()
    print('Katello Content View Version Information Parsed')

    katello_lce_resp = parse_katello_environments()
    print('Parsing Katello Life Cycle Environment Repositories From Satellite')
    print('\n\n')
    print_katello_environments(katello_lce_resp)
    print('Katello Life Cycle Environment Repositories Parsed')

    pulp_repo_resp = parse_pulp_repos()
    print('Parsing Pulp Repository Information From Satellite')
    print('\n\n')
    print_rpm_pulp_repo(pulp_repo_resp)
    print('Pulp Repository Information Parsed')

    print('Parsing Capsule Content From Katello/Satellite')
    print('\n\n')
    print_capsule_katello_repo()
    print('Capsule Content From Katello/Satellite Parsed')

    print('Parsing Capsule Content From Capsule\'s Pulp')
    print('\n\n')
    print_capsule_pulp_repo(katello_lce_resp)
    print('Capsule Content From Capsule\'s Pulp Parsed')


def main():
    try:
        decompress_file()
    except FileExistsError as e:
        print(e)
    print_all_repositories()
        

if __name__ == "__main__":
    main()
