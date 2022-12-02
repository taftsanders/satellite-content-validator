# satellite-content-validator
Using the katello and pulp API this script will gather the repositories for all lifecycle environments and all pulp repositories for display.

Example:
```
Checking for presence of satellite RPM...
Satellite RPM found, continuing...
Enter Satellite WebUI Username: admin
Password: 



Katello Repositories
This is what is seen from katello api endpoint /katello/api/repositories/
===========================
**********************************
Name: Red Hat Enterprise Linux 7 Server RPMs x86_64 7Server
URL: https://satellite.example.com/pulp/content/Default_Organization/Library/content/dist/rhel/server/7/7Server/x86_64/os/
Pulp Version: /pulp/api/v3/repositories/rpm/rpm/5327255a-0a72-4032-83f6-8d98d7ed0440/versions/3/
Content Count: {
    "rpm": 33381,
    "erratum": 5072,
    "package_group": 76,
    "srpm": 0,
    "module_stream": 0
}
Last Sync: 2022-11-28 18:04:14 UTC
**********************************


**********************************
Name: Red Hat Enterprise Linux 8 for x86_64 - AppStream RPMs 8
URL: https://satellite.example.com/pulp/content/Default_Organization/Library/content/dist/rhel8/8/x86_64/appstream/os/
Pulp Version: /pulp/api/v3/repositories/rpm/rpm/aad4cc17-6eae-458f-9c66-959452e88933/versions/6/
Content Count: {
    "rpm": 28341,
    "erratum": 2694,
    "package_group": 59,
    "srpm": 0,
    "module_stream": 621
}
Last Sync: 2022-11-28 18:01:21 UTC
**********************************

Katello Repository Information Gathered


Katello Content Views (including CCVs)
This is what is seen from katello api endpoint /katello/api/content_view_versions
======================================
**********************************
Name: test cv 4.0
Lifecycle Environment: ['Development']
RPM Count: 5
Errata: 1
SRPM Count: 0
Module Stream Count: 0
Last Event: promotion : success
**********************************


**********************************
Name: rhel-8-base-cv 3.0
Lifecycle Environment: ['Library']
RPM Count: 12550
Errata: 1539
SRPM Count: 0
Module Stream Count: 0
Last Event: publish : success
**********************************

Katello Content View Version Information Gathered


Katello Environment Repositories
This is what is seen from katello api endpoint /katello/api/organizations/<ORGID>/environments/<ENVID>/repositories
===========================
**********************************
Backend ID: 1-test_cv-Development-f3a33e4c-3364-491c-8454-4e3d3dcb2a37
Repo Name: Red Hat Satellite Maintenance 6.12 for RHEL 8 x86_64 RPMS
Repo Label: satellite-maintenance-6.12-for-rhel-8-x86_64-rpms
URL: https://satellite.example.com/pulp/content/Default_Organization/Development/test_cv/content/dist/layered/rhel8/x86_64/sat-maintenance/6.12/os/
Pulp Verison href: /pulp/api/v3/repositories/rpm/rpm/3cee6347-c1d6-452c-98aa-d05a946ec586/versions/1/
Pulp Publication href: /pulp/api/v3/publications/rpm/rpm/cd006458-514c-446b-8584-2903557ebdb2/
RPMs: 5
Errata: 1
Package Groups: 1
Source RPMs: 0
Module Streams: 0
**********************************


**********************************
Backend ID: 1-test_cv3-Library-5b20685f-941f-4284-971a-2066c0555dc7
Repo Name: Red Hat Enterprise Linux 7 Server RPMs x86_64 7Server
Repo Label: rhel-7-server-rpms
URL: https://satellite.example.com/pulp/content/Default_Organization/Library/test_cv3/content/dist/rhel/server/7/7Server/x86_64/os/
Pulp Verison href: /pulp/api/v3/repositories/rpm/rpm/a4fb4f82-d839-4e74-a49e-361095476f18/versions/0/
Pulp Publication href: /pulp/api/v3/publications/rpm/rpm/436d2399-e0dd-401a-b365-0ec7b2fd71f8/
RPMs: 33316
Errata: 5017
Package Groups: 76
Source RPMs: 0
Module Streams: 0
**********************************
```
