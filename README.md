# ceilometer_python_monthly_report

Description:
------------
Ceilometer monthly report Python script which uses Python Ceilometerclient to create statistics for each OpenStack instance running in a project regardless if it is still avtive, shut off ot deleted. A CSV report can be created on a monthly basis.

About this script:
------------------
- Author: Frank Reimer
- Version: 1.0
- Creation Date: 2015-08-10

Tested with:
------------
This script was developed in a Red Hat Enterprise Linux OpenStack 6 (Juno) environment and was tested with the following Python clients:
- python-novaclient-2.20.0-1.el7ost.noarch
- python-keystoneclient-0.11.1-1.el7ost.noarch
- python-ceilometerclient-1.0.12-1.el7ost.noarch

Prerequisites:
--------------
- Make sure that your admin user is member of each project with admin rights.
- Make sure the path where you want to save your CSV file still exists
- You need to configure the following options in /etc/ceilometer/ceilometer.conf on your Nova compute nodes to get statistics for VCPUS, Memory, Root Disk Size and Ephemeral Disk Size:
	=> instance_usage_audit = true
	=> instance_usage_audit_period = hour
	=> notify_on_state_change = vm_and_task_state
	=> notification_driver=ceilometer.compute.nova_notifier
	=> notification_driver=nova.openstack.common.notifier.rpc_notifier
   Now restart the following services on your Nova compute nodes:
	=> openstack-ceilometer-compute
	=> openstack-nova-compute

Required packages:
------------------
Please make sure that you install the following packages on your controller nodes or wherever you want to start this script to collect appropriate statistics:
- python-nova
- python-novaclient
- python-novaclient-doc
- python-keystoneclient-doc
- python-keystoneclient
- python-keystone
- python-ceilometer
- python-ceilometerclient
- python-ceilometerclient-doc

Usage:
-----
ceilometer_monthly_report.py -h
usage: ceilometer_monthly_report.py [-h] [--os-auth_url URL]
                                    [--os-username OS_USERNAME]
                                    [--os-password OS_PASSWORD]
                                    [--os-tenant_name OS_TENANT_NAME]
                                    [--filename FILE]

Dump ceilometer data to a csv file.

optional arguments:
  -h, --help            show this help message and exit
  --os-auth_url URL     Keystone Authentication URL
  --os-username OS_USERNAME
                        Username for Keystone
  --os-password OS_PASSWORD
                        Password for Keystone
  --os-tenant_name OS_TENANT_NAME
                        Tenant name for Keystone
  --filename FILE       name of the output csv file

In general you can either give the script all needed options like username, password, tenant name and authentication URL at script runtime or simply source an appropriate keystone file with all needed data inside. The script would then use appropriate environment variables. As mentioned above please make sure that the path where you want to save the CSV file still exists.
