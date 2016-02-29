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
module: fastly_service
short_description: Create and destroy Fastly CDN services
description:
    - Create and destroying Fastly services - (Requires the fantastic fastly-python module (https://github.com/zebrafishlabs/fastly-python)
version_added: "2.1"
author: "Neil Saunders (@njsaunders)"
options:
  api_key:
    required: true
    default: null
    description:
      - Your Fastly API key
  name:
    required: true
    default: null
    description:
      - The name of your service
  domains:
    required: false
    default: null
    description:
      - A list of domains that you wish to use to this service to serve
  backends:
    required: false
    default: null
    description:
      - A list of backends to
  state:
    required: false
    default: present
    description:
      - Create or delete a Fastly service
    choices: ['present', 'absent']
'''

EXAMPLES = '''

# Create an Fastly service with a backend specificying all options (Defaults shown)
- fastly_service:
    name: "my-service"
    backends:
        - name: ELB
          address: myelb.us-east-1.amazon.com
          use_ssl: False,
          port: 80,
          connect_timeout: 1000,
          first_byte_timeout: 15000,
          between_bytes_timeout: 10000,
          error_threshold: 0,
          max_conn: 20,
          weight: 100,
          auto_loadbalance: False,
          shield: None,
          request_condition: None,
          healthcheck:None,
         comment: "My default backend"
    domains: ['uk.beamly.com', 'beamly.com']
    state: present

# Create an Fastly service with minimal backend options
- fastly_service:
    name: "my-service"
    backends:
        - name: ELB
          address: myelb.us-east-1.amazon.com
    domains: ['uk.beamly.com', 'beamly.com']
    state: present

# Delete an Fastly service
- fastly_service:
    name: "my-service"
    state: absent
'''

# TODO: Disabled the RETURN as it was breaking docs building. Someone needs to
# fix this
RETURN = '''# '''

try:
    import fastly
    from fastly import FastlyError
    HAS_FASTLY = True
except ImportError:
    HAS_FASTLY = False

def main():

    module = AnsibleModule(argument_spec=dict(
        name={'required': True, 'type': 'str'},
        api_key={'required': True, 'type': 'str'},
        domains={'required': False, 'type':'list'},
        backends={'required': False, 'type':'list'},
        state={'default':'present', 'required': False, 'choices': ['present', 'absent']},
    ),
    supports_check_mode=False)

    if not HAS_FASTLY:
        module.fail_json(msg='python-fastly is required.')

    # Authenticate
    try:
        fastly_client = fastly.connect(api_key=module.params['api_key'])
    except FastlyError, e:
        module.fail_json(msg="Couldn't authenticate with Fastly: "+str(e))

    # Does this service already exist?
    exists = False
    try:
        service = fastly_client.get_service_by_name(module.params['name'])
        exists = True
    except FastlyError, e:
        pass


    # If we're trying to delete a none existant service or create an already existing service just return changed: false
    if (module.params['state'] == 'absent' and not exists):
        module.exit_json(changed=False)

    if module.params['state'] == 'absent':
        try:
            results = fastly_client.delete_service(service.id)
        except FastlyError, e:
            module.fail_json(msg="Exception deleting service '"+module.params['name']+"': "+str(e))

    elif module.params['state'] == 'present':
        try:
            # Create the service
            if not exists:
                customer = fastly_client.get_current_customer()
                service = fastly_client.create_service(customer_id=customer.id, name=module.params['name'])

            service_version = fastly_client.create_service_version(service.id)
        except FastlyError, e:
            module.fail_json(msg="Exception creating fastly service '"+module.params['name']+"': "+str(e))

        try:
            # Create domains
            for domain_name in module.params['domains']:
                fastly_client.create_domain(service.id, service_version.number, domain_name)
        except FastlyError, e:
            module.fail_json(msg="Exception creating fastly domains for service '"+module.params['name']+"': "+str(e))

        try:
            # Create the backends
            for backend in module.params['backends']:
                service_backend = backend
                service_backend['service_id'] = service.id
                service_backend['version_number'] = service_version.number
                fastly_client.create_backend(**service_backend)
        except FastlyError, e:
            module.fail_json(msg="Exception creating fastly backends for service '"+module.params['name']+"': "+str(e) + str(service_backend))

        try:
             # Activate the version
            fastly_client.activate_version(service.id, service_version.number)
        except FastlyError, e:
            module.fail_json(msg="Exception activating version '"+str(service.number)+"' of service '" + module.params['name'] + "': "+str(e) + str(service_backend))


    service = fastly_client.get_service_by_name(module.params['name'])
    results = service.__dict__['_data']
    results['changed'] = True
    module.exit_json(**results)

# import module snippets
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()