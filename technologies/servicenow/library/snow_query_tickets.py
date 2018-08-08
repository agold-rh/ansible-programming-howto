# python 3 headers, required if submitting to Ansible
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {  'metadata_version': '0.1',
                      'status': ['preview'],
                      'supported_by': 'agold@redhat.com'}
DOCUMENTATION = """
      module: snow_query_tickets
        author: Andrew Gold <agold@redhat.com>
        version_added: "0.1"
        short_description: Query ServiceNow tickets
        description:
            - Retreive interesting SNOW tickets for processing
        options:
          minutes: 
            description: Retrieve tickets more recent than now - minutes
            required: true
            default: 1440
            ini:
              - section: snow_query_tickets
                key: minutes
          group: 
            description: Retrieve tickets belonging to this group
            required: true
            default: 'ANSIBLE'
            ini:
              - section: snow_query_tickets
                key: group
          host: 
            description: The SNOW host to which we connect
            required: true
            default: 'ANSIBLE'
            ini:
              - section: snow_query_tickets
                key: host
          user: 
            description: The SNOW user as which we connect
            required: true
            ini:
              - section: snow_query_tickets
                key: user
          password: 
            description: The SNOW connection user password 
            required: true
            ini:
              - section: snow_query_tickets
                key: password
        notes:
          - A note might be added here
"""

EXAMPLES = '''
- name: Execute snow_query_tickets
  snow_query_tickets:
    minutes: 1440
    group: "ANSIBLE"
    host:  "{{ snow_host }}"
    user: "{{ snow_user }}"
    password: "{{ snow_password }}"
  no_log: false
  register: qt_result

- name: Debug output
  debug: 
    msg: "{{ qt_result }}"
'''

from ansible.module_utils.basic import *
import pysnow
import json
import re
from datetime import datetime, timedelta
from collections import defaultdict

class ThisModule(object):
  '''Retrieve ServiceNow trouble ticket information'''
  _module = None
  _fields = None

  def __init__(self):
    '''The constructor'''
    self._set_fields()
    self._module = AnsibleModule(
      argument_spec=self._fields,
      supports_check_mode=True
    )

  def _set_fields(self):
    '''Configure input arguments'''
    self._fields = {
      "minutes" : { "required": True, "type": "int" },
      "group" : { "required": True, "type": "str" },
      "host" : { "required": True, "type": "str" },
      "user" : { "required": True, "type": "str" },
      "password" : { "required": True, "type": "str" },
    }

  def parse_description(self, desc):
    '''Determine the type of remediation based on ticket description'''

    description_details = {
      'service_name':'', 
      'remediation':'', 
      'escalation_group':''
    }
        
    #Windows ntservices incidents
    win_service_regex = re.compile('ntservices')
    win_service_match = win_service_regex.search(desc)

    #For demo tickets
    demo_regex = re.compile('~EscalationGroup=')
    demo_match = demo_regex.search(desc)

    if win_service_match:
        description_details['remediation'] = 'demo_service_restart'
        description_details['escalation_group'] = 'Wintel Support'

        #Extract the serviceName out of the description
        service_regex = re.compile('(?<=ntservices:).+(?= -)')
        service_match = service_regex.search(desc)
        if service_match:
            description_details['service_name'] = service_match.group()
        else:
            description_details['service_name'] = ''
    elif demo_match:
        description_details['service_name'] = 'demoService'
        
        #Set remediation value
        remediation_regex = re.compile('(?<=Remediation=).+?(?=~)')
        remediation_match = remediation_regex.search(desc)
        if remediation_match:
            description_details['remediation'] = remediation_match.group()
        else:
            description_details['remediation'] = ''

        #Set escalation_group
        escalation_regex = re.compile('(?<=EscalationGroup=).+?(?=~)')
        escalation_match = escalation_regex.search(desc)
        if escalation_match:
            description_details['escalation_group'] = escalation_match.group()
        else:
            description_details['escalation_group'] = ''
    else:
        description_details['remediation'] = ''
        description_details['service_name'] = ''
        description_details['escalation_group'] = ''

    return description_details

  def work(self):
    '''Main application logic'''
    #Query 2 months back. ANSIBLE test ticket was created on 5-18
    minutes = self._module.params['minutes']
    snow_group = self._module.params['group']
    host = self._module.params['host']
    user = self._module.params['user']
    password = self._module.params['password']
    
    now = datetime.today()
    minutes_delta = now - timedelta(minutes=minutes)
    
    # Create ServiceNow client object
    c = pysnow.Client(host=host, user=user, password=password)
    c.parameters.display_value = True
    c.parameters.exclude_reference_link  = True
    
    # Query
    qb = (
        pysnow.QueryBuilder()
        .field('sys_created_on').between(minutes_delta, now)
        .AND()
        .field('assignment_group').starts_with(snow_group)
        .AND()
        .field('state').equals('true')
    )

    incident = c.resource(api_path='/table/incident')
  
    try:
        response = incident.get(query=qb)
    except pysnow.exceptions.ResponseError as e:
       self._module.fail_json(msg="Query failure: ({0})".format(e))
  
    data = defaultdict(list)
  
    # Iterate over the matching records and print out number
    for record in response.all():
        ticket_details = self.parse_description(record['description'])

        data['results'].append({"number":record['number'], "sys_id":record['sys_id'], "openTime":record['opened_at'], "assignmentGroup":record['assignment_group'],\
          "shortDesc":record['short_description'], "desc":record['description'], "server":record['u_host_name'],\
          "serviceName":ticket_details['service_name'], "escalationGroup":ticket_details['escalation_group'], "remediation":ticket_details['remediation'], \
          "incident_state":record['incident_state'], "state":record['state'], "active":record['active'], "assigned_to":record['assigned_to'], \
          "cmdb_ci":record['cmdb_ci'], "u_host_name":record['u_host_name'], \
        })
  
    return json.dumps(data['results'])

  def run(self):
    '''Application entry point'''
    ret_val = self.work()
    self._module.exit_json(changed=False, meta=ret_val)

if __name__ == '__main__':
    ThisModule().run()
