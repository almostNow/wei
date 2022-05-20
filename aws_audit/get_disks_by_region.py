#!/usr/bin/env python3

import boto3
import argparse
import xlsxwriter
from datetime import date

''' get_args()
Get the parameters passed into the script.
Expects the region to be passed as a parameter.

Ex.
$ python3 ./get_disks_by_region.py -r us-east-2
'''
def get_args():
    parser = argparse.ArgumentParser(description="Create Excel file of disk infomation by AWS region.",
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-r", "--region", help="The AWS region, like 'us-east-2'")
    args = parser.parse_args()
    return vars(args)

''' get_instances(boto3.resource)

Returns an array of dictionaries with info for each instance.
based on the AWS EC2 resource.

Parameters:
    - AWS EC2 boto3 resource object

Ex.
[ { 'inst_name' : 'dev-node', 'inst_id' : 'i-077b211c2586da66f', 'inst_type' : 't2.micro' } ]
'''
def get_instances(ec2):
    instances_array = []
    instances = ec2.instances.all()
    for instance in instances:
        if instance.tags[0]['Key'] == 'Name':
            instances_array.append({  
                'inst_name' : instance.tags[0]['Value'],
                'inst_id'   : instance.id, 
                'inst_type' : instance.instance_type
            })
    return instances_array

''' get_volumes_dict(boto3.resource)

Returns a Dictionary of instance volume information.

Parameters:
    - An AWS ec2 boto3 resource object

Ex.
{
  'i-05671b813158f5c33' : {
        'device'     : '/dev/sda1',
        'iops'       : 100,
        'size'       : 10, <- GiB
        'state'      : 'in-use',
        'vol_id'     : 'vol-0273a3ddf98eb0ac7',
        'volume_type': 'gp2'
    },
    'i-077b211c2586da66f' : {...}
}
'''
def get_volumes_dict(ec2):
    volumes = ec2.volumes.all()
    volumes_dict = {}
    for v in volumes:
        for a in v.attachments:
            volumes_dict.update({ a['InstanceId'] : {
                'vol_id' : v.id, 
                'volume_type' : v.volume_type, 
                'device' : a['Device'], 
                'size': v.size, 
                'iops' : v.iops, 
                'state' : v.state
            }})
    return volumes_dict

''' prepare_data( { [], {} } )
Create the data structure for Excel file creation.

Parameters:
    - A dictionary containing:
        * An array of instance information
        * A Dictionary of volume information per instance

Returns an array.
'''
def prepare_data(in_dict):
    final_array = []
    for instance in in_dict['inst']:
        final_array.append({**in_dict['vol'][instance['inst_id']], **instance})
    return final_array

''' create_excel_file('String', [])
Create the Excel spread sheet file.
Parameters:
    - An AWS region name string, like 'us-east-2'
    - An array of dictionaries of disk information for each instance

The file created name format is:
aws_region-disk-info-YYYY-MM-DD.xlsx

Ex.
us-east-2-disk-info-2022-05-19.xlsx
'''
def create_excel_file(aws_region, disk_info):
    
    colomn_names = [
        'Instance Name',
        'Instance ID',
        'Instance Type',
        'Volume ID',
        'Volume Type',
        'Device',
        'Volume Size (GiB)',
        'IOPS',
        'Volume State'
    ]
    
    xlsx_file = aws_region + '-disk-info-' + str(date.today()) + '.xlsx'
    workbook = xlsxwriter.Workbook(xlsx_file)
    worksheet = workbook.add_worksheet()
    
    worksheet.set_column(0, 8, 20)
    cell_format = workbook.add_format({'bold': True, 'italic': True})
        
    # print header
    for col_num, col_name in enumerate(colomn_names):
        worksheet.write_string(0, col_num, col_name, cell_format)

    align_left = workbook.add_format()
    align_left.set_align('left')

    for row_num, disk_data in enumerate(disk_info, start=1):
        worksheet.write_string(row_num, 0, disk_data['inst_name'])
        worksheet.write_string(row_num, 1, disk_data['inst_id'])
        worksheet.write_string(row_num, 2, disk_data['inst_type'])
        worksheet.write_string(row_num, 3, disk_data['vol_id'])
        worksheet.write_string(row_num, 4, disk_data['volume_type'])
        worksheet.write_string(row_num, 5, disk_data['device'])
        worksheet.write_number(row_num, 6, disk_data['size'], align_left)
        worksheet.write_number(row_num, 7, disk_data['iops'], align_left)
        worksheet.write_string(row_num, 8, disk_data['state'])    
    
    workbook.close()

### MAIN ###

# Get the arguments passed into the script.
config = get_args()

AWS_REGION = config['region']

# Instantiate the AWS EC2 resource object for the given region.
ec2 = boto3.resource('ec2', region_name=AWS_REGION)

# Fetch an array of dictionaries containing EC2 instance information.
inst_array = get_instances(ec2)

# Obtain a dictionary of disk info per EC2 instance in the ec2 object.
vol_dict = get_volumes_dict(ec2)

# Get the proper data structure for Excel file creation.
disk_info_array = prepare_data({ 'inst' : inst_array, 'vol' : vol_dict })

# Create the Excel spreadsheet file.
create_excel_file(AWS_REGION, disk_info_array)

exit(0)