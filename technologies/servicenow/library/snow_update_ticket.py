################################################################################
#   Copyright (C) 2018 Andrew Gold
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
################################################################################

# python 3 headers, required if submitting to Ansible
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {  'metadata_version': '0.1',
                      'status': ['preview'],
                      'supported_by': 'agold@redhat.com'}
DOCUMENTATION = """
      module: snow_update_ticket
        author: Andrew Gold <agold@redhat.com>
        version_added: "0.1"
        short_description: Update a ServiceNow trouble ticket
        description:
            - Update the status of a SNOW ticket
        options:
          host: 
            description: The SNOW host
            required: true
            ini:
              - section: snow_update_ticket
                key: host
          user: 
            description: The SNOW user account
            required: true
            ini:
              - section: snow_update_ticket
                key: user
          password: 
            description: The SNOW user account password
            required: true
            ini:
              - section: snow_update_ticket
                key: password
          incident: 
            description: The SNOW incident ID 
            required: true
            ini:
              - section: snow_update_ticket
                key: incident
          action: 
            description: The type of updated to be performed
            required: true
            choices: ['cancel', 'close', 'comment', 'resolve', 'transfer', 'wip' ]
            default: 'comment'
            ini:
              - section: snow_update_ticket
                key: action
          notes: 
            description: Appended to the ticket 'notes' section
            required: true
            default: 'Ansible updated'
            ini:
              - section: snow_update_ticket
                key: notes
          escalation_group: 
            description: SNOW group to whom this ticket should be escalated
            required: true
            default: 'SERVICE DESK'
            ini:
              - section: snow_update_ticket
                key: escalation_group
        notes:
          - Magic numbers are all from ServiceNow
          - A note might be added here
"""

EXAMPLES = '''
- name: Mark ticket as work in progress
  snow_update_ticket:
    host: "{{ snow_host }}"
    user: "{{ snow_user }}"
    password: "{{ snow_password }}"
    incident: "{{ item.number }}"
    action: wip
    notes: "Ansible remediation in progress"
    escalation_group: "SERVICE DESK"
  no_log: true

- name: Placeholder for actual remediation
  debug:
    msg: Actual remediation is performed here

'''

from ansible.module_utils.basic import *
import pysnow

class ThisModule(object):
  '''Update a ServiceNow trouble ticket'''
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
      "action" : { "required": True, "type": "str" },
      "notes" : { "required": True, "type": "str" },
      "escalation_group" : { "required": True, "type": "str" },

      "incident" : { "required": True, "type": "str" },
      "host" : { "required": True, "type": "str" },
      "user" : { "required": True, "type": "str" },
      "password" : { "required": True, "type": "str" }
    }

  def action_cancel(self):
    '''Cancel a trouble ticket'''
    payload = {}

    payload["state"] = '3'                          # FIXME magic number!
    payload["incident_state"] = '7'                 # FIXME magic number!
    payload["u_state_controller"] = '7' 
    payload["u_sub_status"] = 'Cancelled'           
    payload["close_code"] = 'Cancelled'
    payload["active"] = 'false'
    payload["priority"] = '4'
    payload["close_notes"] = self._module.params['notes']
    
    return payload

  def action_close(self):
    '''Close a trouble ticket'''

    # yes, this is intentional
    payload = {}

    return payload

  def action_comment(self):
    '''Commant/annotate a trouble ticket'''
    payload = {}

    payload["work_notes"] = self._module.params['notes']

    return payload

  def action_resolve(self):
    '''Resolve a trouble ticket'''
    payload = {}

    payload["state"] = '6'                          # FIXME magic number!
    payload["incident_state"] = '6'                 # FIXME magic number!
    payload["u_sub_status"] = 'Permanently Resolved'
    payload["close_notes"] = 'Ansible Automation Resolved'
    payload["close_code"] = 'Others'
    payload["u_others_please_specify"] = 'Ansible Resolved'

    payload["work_notes"] = self._module.params['notes']

    return payload

  def action_transfer(self):
    '''Transfer/escalate a trouble ticket'''
    payload = {}
    payload["state"] = '1'
    payload["incident_state"] = '1'
    payload["assigned_to"] = '' #need to fix unassign
    payload["assignment_group"] = self._module.params['escalation_group']
    payload["work_notes"] = self._module.params['notes']

    return payload

  def action_wip(self):
    '''Annotate a trouble ticket as work in progress'''
    payload = {}
    payload["assigned_to"] = 'Ansible, User'
    payload["state"] = '2'                          # FIXME magic number!
    payload["incident_state"] = '2'                 # FIXME magic number!
    payload["work_notes"] = self._module.params['notes']

    return payload

  def work(self):
    '''Main application logic'''
    host = self._module.params['host']
    user = self._module.params['user']
    password = self._module.params['password']

    # Create client object
    c = pysnow.Client(host=host, user=user, password=password)
    c.parameters.display_value = True
    c.parameters.exclude_reference_link  = True
    c.parameters.add_custom({'sysparm_input_display_value': True})

    incident = c.resource(api_path='/table/incident')

    payload = {}
    action = self._module.params['action']

    if "cancel" == action:
      payload = self.action_cancel()
    elif "close" == action:
      payload = self.action_close()
    elif "comment" == action:
      payload = self.action_comment()
    elif "resolve" == action:
      payload = self.action_resolve()
    elif "transfer" == action:
      payload = self.action_transfer()
    elif "wip" == action:
      payload = self.action_wip()
    else:
      self._module.fail_json(msg="Invalid action field: ({0})".format(action))

    result = None

    try: 
      number = self._module.params['incident']
      result = incident.update(query={'number': number}, payload=payload)
    except Exception as e:
      self._module.fail_json(msg="Query failure: ({0})".format(e))

    return json.dumps(result.one(), indent=2)


  def run(self):
    '''Application entry point'''
    is_changed = False
    retval = { "notice" : "check_mode so no records updated" }
    if not self._module.check_mode:
      retval = self.work()
      is_changed = True

    self._module.exit_json(changed=is_changed, meta=retval)

if __name__ == '__main__':
    ThisModule().run()
