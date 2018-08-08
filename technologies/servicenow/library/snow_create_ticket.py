# python 3 headers, required if submitting to Ansible
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {  'metadata_version': '0.1',
                      'status': ['preview'],
                      'supported_by': 'agold@redhat.com'}
DOCUMENTATION = """
      module: snow_create_ticket
        author: Andrew Gold <agold@redhat.com>
        version_added: "0.1"
        short_description: Create a ServiceNow ticket
        description:
            - Create a valid ServiceNow trouble ticket
        options:
          assigned_to: 
            description: The user to whom the ticket is assigned
            required: true
            default: 'Ansible, User'
            ini:
              - section: snow_create_ticket
                key: assigned_to
          assignment_group: 
            description: The group to whom the ticket is assigned
            required: true
            default: 'ANSIBLE'
            ini:
              - section: snow_create_ticket
                key: assignment_group
          escalation_group: 
            description: The group to whom the ticket is assigned
            required: true
            default: 'SERVICE DESK'
            ini:
              - section: snow_create_ticket
                key: escalation_group
          requestor: 
            description: The user who opened the ticket
            required: true
            default: 'Ansible, User'
            ini:
              - section: snow_create_ticket
                key: requestor
          host: 
            description: The SNOW hostname 
            required: true
            ini:
              - section: snow_create_ticket
                key: host
          user: 
            description: The SNOW user account to which we connect 
            required: true
            ini:
              - section: snow_create_ticket
                key: user
          password: 
            description: The SNOW user account password
            required: true
            ini:
              - section: snow_create_ticket
                key: password
          short_description: 
            description: Ticket summary
            required: true
            default: 'Ansible Created Test Ticket'
            ini:
              - section: snow_create_ticket
                key: short_description
          remediation: 
            description: Role that remediates this ticket 
            required: true
            ini:
              - section: snow_create_ticket
                key: remediation
          server: 
            description: The server or device in trouble
            required: true
            default: 'bad.example.com'
            ini:
              - section: snow_create_ticket
                key: server
          serviceName: 
            description: The service or application in trouble
            required: true
            default: 'example.service'
            ini:
              - section: snow_create_ticket
                key: serviceName
        notes:
          - A note might be added here
"""

EXAMPLES = '''
- name: Create first test ticket
  snow_create_ticket:
    assigned_to: "Ansible, User"
    assignment_group: "{{ assignment_group }}"
    escalation_group: "SERVICE DESK"
    requestor: "Ansible, User"
    host:  "{{ snow_host }}"
    user: "{{ snow_user }}"
    password: "{{ snow_password }}"
    short_description: "first Ansible demo ticket"
    remediation: "complex"
    server: "one.example.com"
    serviceName: "daytime"
  no_log: true
  register: ct_result

- name: Create first ticket output
  debug:
    msg: "{{ ct_result }}"
'''
from ansible.module_utils.basic import *
import pysnow

class ThisModule(object):
  '''Create a ServiceNow trouble ticket'''
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
    '''Configure module input'''
    self._fields = {
      "short_description" : { "required": True, "type": "str" },
      "assignment_group" : { "required": True, "type": "str" },
      "remediation" : { "required": True, "type": "str" },
      "serviceName" : { "required": True, "type": "str" },
      "server" : { "required": True, "type": "str" },
      "host" : { "required": True, "type": "str" },
      "user" : { "required": True, "type": "str" },
      "password" : { "required": True, "type": "str" },
      'requestor': { "required": True, "type": "str" },
      'assigned_to': { "required": True, "type": "str" },
      'escalation_group': { "required": True, "type": "str" },
    }

  def work(self):
    '''Main application logic'''

    # 11 fields
    short_description = self._module.params['short_description']
    assignment_group = self._module.params['assignment_group']
    remediation = self._module.params['remediation']
    serviceName = self._module.params['serviceName']
    server = self._module.params['server']
    host = self._module.params['host']
    user = self._module.params['user']
    password = self._module.params['password']
    requestor = self._module.params['requestor']
    assigned_to = self._module.params['assigned_to']
    escalation_group = self._module.params['escalation_group']

    # Create client object
    # 3 inputs used
    c = pysnow.Client(host=host, user=user, password=password)
    c.parameters.display_value = True
    c.parameters.exclude_reference_link  = True
    incident = c.resource(api_path='/table/incident')

    description_pieces = []

    # 4 composite fields
    description_pieces.append("Server=" + server)
    description_pieces.append("Remediation=" + remediation)
    description_pieces.append("ServiceName=" + serviceName)
    description_pieces.append("EscalationGroup=" + escalation_group)
    description = "~".join(description_pieces)

    
    # "requestor in GUI, caller_id in data model
    caller_id = requestor

    # Set the payload
    # 4 individual fields
    # 1 composite field of 4 inputs
    # 3 individual fields used to create the connection (above)
    # 11 fields total
    new_record = {
        'caller_id': caller_id,
        #'assigned_to': assigned_to,
        'short_description': short_description,
        'description': description,
        'assignment_group': assignment_group
    }

    result = None

    try:
      result = incident.create(payload=new_record)
    except Exception as e:
      self._module.fail_json(msg="Query failure: ({0})".format(e))

    return json.dumps(result.one(), indent=2)


  def run(self):
    '''Application entry point'''
    is_changed = False
    retval = { "notice" : "check_mode so no records created" }
    if not self._module.check_mode:
      retval = self.work()
      is_changed = True

    self._module.exit_json(changed=is_changed, meta=retval)

if __name__ == '__main__':
    ThisModule().run()
