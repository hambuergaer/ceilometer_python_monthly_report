#!/usr/bin/env python
#####################################################################################
# Scriptname	: ceilometer_monthly_report.py
# Scriptauthor	: Frank Reimer
# Creation date	: 2015-08-10
#####################################################################################
#
# Description:
#
# This script should run monthly to report Openstack Ceilometer
# statistics for every instance running for a tenant (project)
#
# Requirements:
# - Make sure that your admin user is member of each project with admin rights.
# - Make sure the path where you want to save your CSV file still exists.
#
#####################################################################################

import os, sys, ceilometerclient.client, json, argparse, datetime
from keystoneclient.v2_0 import client as kclient
from novaclient import client as nclient

csv_resource_fields = "PROJECT_ID;PROJECT_NAME;RESOURCE_ID;RESOURCE_NAME;RESOURCE_STATUS;DURATION (in sec.);VCPUS_AVG;MEMORY_AVG (in MB);ROOT_DISK_AVG (in GB);EPHEMERAL_DISK_AVG (in GB)"
csv_resource_staistics = []
tenants = []

def get_keystone_creds(os_auth_url,os_username,os_password,os_tenant_name):
	keystone_credentials = {}
	keystone_credentials['username'] = os_username
	keystone_credentials['password'] = os_password
	keystone_credentials['auth_url'] = os_auth_url
	keystone_credentials['tenant_name'] = os_tenant_name
	return keystone_credentials

def get_nova_creds(os_auth_url,os_username,os_password,os_tenant_name):
	nova_credentials = {}
	nova_credentials['username'] = os_username
	nova_credentials['api_key'] = os_password
	nova_credentials['auth_url'] = os_auth_url
	nova_credentials['project_id'] = os_tenant_name
	return nova_credentials

# Get tenants (projects) from keystone
def get_keystone_tenants():
	keystone = kclient.Client(**get_keystone_creds(args.os_auth_url,args.os_username,args.os_password,args.os_tenant_name))
	for tenant in keystone.tenants.list():
		tenant_parsed = json.loads(json.dumps(tenant.to_dict()))
		tenant_output = json.loads(json.dumps(tenant_parsed, indent=4, sort_keys = True))
		#print "Tenant ID: " + tenant_output['id'] + ", Name: " + tenant_output['name']
		tenant_output_together = str(tenant_output['id']+":"+tenant_output['name'])
		tenants.append(tenant_output_together)

# Create the timestamp field for a query to get appropriate statistics between the start of this script and the beginning of the according month.
def get_current_date_and_time():
	get_date_and_time = datetime.datetime.now()
	current_date_and_time = get_date_and_time.strftime('%Y-%m-%dT%H:%M')
	return current_date_and_time

def get_beginning_of_current_month():
	get_first_day_of_month = datetime.datetime.now()
	first_day_of_month = get_first_day_of_month.strftime('%Y-%m-01T00:00')
	return first_day_of_month


# Get statistics per instance
def get_statistics_per_instance():
	# First lets go through all tenants:
	get_data_end = get_current_date_and_time()
	get_data_start = get_beginning_of_current_month()
	get_keystone_tenants()
	for tenant in tenants:
		os_tenant_name=tenant.split(":")[1]
		os_tenant_id=tenant.split(":")[0]
		# Now we get a list with all resources running for this tenant (project) except of project "services":
		if not os_tenant_name == "services":
			# Get instance id and name:
			ceilometer_creds = get_keystone_creds(args.os_auth_url,args.os_username,args.os_password,os_tenant_name)
			cclient = ceilometerclient.client.get_client('2',**ceilometer_creds)
			query_resource_detail = [{'field': 'project', 'op': 'eq', 'value': os_tenant_id},{'field': 'source', 'op': 'eq', 'value': 'openstack'}]
			for resource in cclient.resources.list(q=query_resource_detail):
				resources_parsed = json.loads(json.dumps(resource.to_dict()))
				resources_output = json.loads(json.dumps(resources_parsed, indent=4, sort_keys = True))
				my_id = resources_output['resource_id']
				if not resources_output['resource_id'].startswith('instance-') and not resources_output['resource_id'].endswith('-vda') and resources_output['user_id']:
					resource_display_name = ''
					
					# Now getting resource details
					query_instance_details = [{'field': 'resource', 'op': 'eq', 'value': my_id}]
					resource_details = cclient.resources.get(my_id)
					resource_details_parsed = json.loads(json.dumps(resource_details.to_dict()))
					resource_details_output = json.loads(json.dumps(resource_details_parsed, indent=4, sort_keys = True))

					if 'OS-EXT-AZ:availability_zone' or 'availability_zone' in resource_details_output['metadata']:
						if 'display_name' in  resource_details_output['metadata']:
							resource_display_name = resource_details_output['metadata']['display_name']
						if 'status' in resource_details_output['metadata']:
							resource_status = resource_details_output['metadata']['status']
						if 'state' in resource_details_output['metadata']:
							resource_status = resource_details_output['metadata']['state']
						
						# No we will get some statistics for an instance.
						query_statistics = [{'field': 'resource', 'op': 'eq', 'value': my_id},{'field': 'timestamp', 'op': 'gt', 'value': get_data_start},{'field': 'timestamp', 'op': 'lt', 'value': get_data_end}]
						# For vcpus
						vcpu_average = ''
						vcpus = cclient.statistics.list(meter_name='vcpus', q=query_statistics)
						for vcpu in vcpus:
							vcpu_parsed = json.loads(json.dumps(vcpu.to_dict()))
							vcpu_output = json.loads(json.dumps(vcpu_parsed, indent=4, sort_keys = True))
							vcpu_average = str(vcpu_output['avg']).split(".")[0]
						
						# For memory
						memory_average = ''
						memory_size = cclient.statistics.list(meter_name='memory', q=query_statistics)
						for memory in memory_size:
							memory_parsed = json.loads(json.dumps(memory.to_dict()))
							memory_output = json.loads(json.dumps(memory_parsed, indent=4, sort_keys = True))
							memory_average = str(memory_output['avg'])
						
						# For disk.root.size
						disk_root_average = ''
						root_disk_size = cclient.statistics.list(meter_name='disk.root.size', q=query_statistics)
						for rsize in root_disk_size:
							rsize_parsed = json.loads(json.dumps(rsize.to_dict()))
							rsize_output = json.loads(json.dumps(rsize_parsed, indent=4, sort_keys = True))
							disk_root_average = str(rsize_output['avg'])
						
						# For disk.ephemeral.size
						disk_ephemeral_average = ''
						ephemeral_disk_size = cclient.statistics.list(meter_name='disk.ephemeral.size', q=query_statistics)
						for esize in ephemeral_disk_size:
							esize_parsed = json.loads(json.dumps(esize.to_dict()))
							esize_output = json.loads(json.dumps(esize_parsed, indent=4, sort_keys = True))
							disk_ephemeral_average = str(esize_output['avg'])
							
						# For instance duration
						instance_duration = ''
						duration = cclient.statistics.list(meter_name='instance', q=query_statistics)
						for seconds in duration:
							duration_parsed = json.loads(json.dumps(seconds.to_dict()))
							duration_output = json.loads(json.dumps(duration_parsed, indent=4, sort_keys = True))
							instance_duration = str(duration_output['duration'])
						
						# Append entries to csv_resource_staistics list
						collected_resource_data = resources_output['project_id'] + ";" + os_tenant_name + ";" + resources_output['resource_id'] + ";" + resource_display_name + ";" + resource_status + ";" + instance_duration + ";" + vcpu_average + ";" + memory_average + ";" + disk_root_average + ";" + disk_ephemeral_average
						csv_resource_staistics.append(collected_resource_data)
					else:
						print "System seems not be a virtiual machine."

# Write statistics to csv file
def write_statistics_to_csv(filename):
	csv_file = filename
	if not os.path.exists(csv_file):
		my_file = file(csv_file, 'w')
	else:
		my_file = file(csv_file, 'w')
	
	write_file = open(csv_file, 'a')
	write_file.write(csv_resource_fields)	
	for data in csv_resource_staistics:
		write_file.write("\n"+data)
	write_file.close()

############# MAIN #############
parser = argparse.ArgumentParser(
        description='Dump ceilometer data to a csv file.')
parser.add_argument('--os-auth_url', metavar='URL',
                        default=os.environ.get('OS_AUTH_URL',
                                       'http://localhost:5000/v2.0'),
                        type=str, help='Keystone Authentication URL')
parser.add_argument('--os-username',
                        default=os.environ.get('OS_USERNAME', None),
                        type=str, help='Username for Keystone')
parser.add_argument('--os-password', default=os.environ.get("OS_PASSWORD"),
                        type=str, help='Password for Keystone')
parser.add_argument('--os-tenant_name', default=os.environ.get("OS_TENANT_NAME"),
                        type=str, help='Tenant name for Keystone')
parser.add_argument('--filename', metavar='FILE', type=str,
                        help='name of the output csv file')
args = parser.parse_args()

get_statistics_per_instance()
write_statistics_to_csv(args.filename)
