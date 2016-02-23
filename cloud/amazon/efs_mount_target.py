#!/usr/bin/python
#
# This is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This Ansible library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: efs_mount_target
short_description: Manage AWS Elastic Filesystem (EFS) mount targets
description:
    - Create or delete an EFS mount target
version_added: "0.1"
author: "Neil Saunders (@njsaunders)"
options:
  mount_target_id:
    required: false
    default: null
    description:
      - An ID of an existing EFS Mount target (Used for state: absent)
  filesystem_id:
    required: false
    default: null
    description:
      - The ID of an existing Elastic filesystem (Used for state: present)
  subnet_id:
    required: false
    default: null
    description:
      - The subnet ID for which to create the mount target (Used for state: present)
  ip_address:
    required: false
    default: null
    description:
      - The (Optional) IP for which to assign to the mount target - Automatic if omitted (Used for state: present)
  security_group_ids:
    required: false
    default: null
    description:
      - A list of security group ids to apply to the mount target (Used for state: present)
  state:
    required: false
    default: present
    description:
      - Create or delete an EFS mount target
    choices: ['present', 'absent']
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Create an EFS volume
- efs_volume:
    vpc_id: "vpc-12345678"
    tags:
      Name: "my-first-efs-volume"
      environment: "stage"
    subnets: ['subnet-d32632bb', 'subnet-a12832bb', 'subnet-d322e2bb']
    security_groups: ['sg-1234567', 'sg-1234567']

# Delete an EFS volume
- efs_volume:
    volume_id: vol-00112233
    state: absent
'''

# TODO: Disabled the RETURN as it was breaking docs building. Someone needs to
# fix this
RETURN = '''# '''

try:
    import boto
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

class EfsMountTargetManager:
    """Handles EFS Mount Targets"""

    def __init__(self, module):
        self.module = module

        try:
            # self.ecs = boto3.client('ecs')
            region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module)
            if not region:
                module.fail_json(msg="Region must be specified as a parameter, in EC2_REGION or AWS_REGION environment variables or in boto configuration file")
            self.efs = boto3_conn(module, conn_type='client', resource='efs', region=region, endpoint=ec2_url, **aws_connect_kwargs)
        except boto.exception.NoAuthHandlerFound, e:
            self.module.fail_json(msg="Can't authorize connection - "+str(e))

    def delete_efs_mount_target(self, mount_target_id):
        response = self.efs.delete_mount_target(MountTargetId=mount_target_id)
        return response

    def create_mount_target(self, filesystem_id, subnet_id, security_group_ids, ip_address=None):
        response = self.efs.create_mount_target(FileSystemId=filesystem_id, SubnetId=subnet_id, IpAddress=ip_address, SecurityGroups=security_group_ids)
        return response

def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        mount_target_id={'required': False, 'type': 'str'},
        filesystem_id={'required': False, 'type': 'str'},
        subnet_id={'required': False, 'type':'str'},
        ip_address={'required': False, 'type': 'str' },
        security_group_ids={'required': False, 'type': 'list' },
        state={'default':'present', 'required': False, 'choices': ['present', 'absent'] },
    ))

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive = [
                                                 [ 'mount_target_id', 'filesystem_id' ],
                                                 [ 'mount_target_id', 'subnet_id' ],
                                                 [ 'mount_target_id', 'ip_address' ],
                                                 [ 'mount_target_id', 'security_group_ids' ]
                                               ],
                           supports_check_mode=False)

    if not HAS_BOTO:
      module.fail_json(msg='boto is required.')

    if not HAS_BOTO3:
      module.fail_json(msg='boto3 is required.')

    efs_target_manager = EfsMountTargetManager(module)
    if module.params['state'] == 'absent':
        try:
            results = efs_target_manager.delete_efs_mount_target(mount_target_id=module.params['mount_target_id'])
        except Exception, e:
            module.fail_json(msg="Exception finding EFS mount target '"+module.params['name']+"': "+str(e))

    elif module.params['state'] == 'present':
        try:
            results['efs_mount_target'] = efs_target_manager.create_mount_target(filesystem_id=module.params['filesystem_id'], subnet_id=module.params['subnet_id'], security_group_ids=module.params['security_group_ids'])
            results['changed'] = True
        except Exception, e:
            module.fail_json(msg="Exception creating EFS mount target '"+module.params['name']+"': "+str(e))

    module.exit_json(**results)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *d

if __name__ == '__main__':
    main()