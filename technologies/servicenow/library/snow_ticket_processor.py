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
DOCUMENTATION = '''
      module: snow_ticket_processor
        author: Andrew Gold <agold@redhat.com>
        version_added: "0.1"
        short_description: Bucket and process SNOW tickets
        description:
            - Bucket duplicate Service Now tickets.
            - Mark most recent ticket in each bucket as active.
            - Mark other tickets as cancelled. 
            - Cancel active tickets created within a change control window
            - Enable roles for all active tickets
        options:
          tickets: 
            description: List of SNOW tickets from snow_query_tickets module.
            required: true
        notes:
          - Change control window functionality is just a place holder
          - A note might be added here
'''

EXAMPLES = '''
# Retrieve the newly created test tickets
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

# Aggregate and winnow tickets
- name: Process tickets
  snow_ticket_processor:
    tickets: "{{ qt_result.meta }}"
  when: qt_result is defined
  register: post_process

# Trace execution
- name: Output processing results
  debug:
    msg: "{{ post_process }}"

'''
from ansible.module_utils.basic import *
from random import randint
from operator import itemgetter

import json

try:
  from __main__ import display
except ImportError:
  from ansible.utils.display import Display
  display = Display()

class ThisModule(object):
  '''Categorize and sort inbound tickets'''
  _module = None
  _fields = None
  _active = [ ]
  _cancel = [ ]
  _roles  = [ ]

  def __init__(self):
    '''The constructor'''
    self._set_fields()
    self._module = AnsibleModule(
      argument_spec=self._fields,
      supports_check_mode=True
    )

  def _set_fields(self):
    '''Configure module input arguments'''
    self._fields = {
      "tickets" : { "required": True, "type": "list" },
    }

  def split_related_tickets(self, tickets):
    '''Identify related tickets'''
    buckets = { }
    for ticket in tickets:
      # A unique event is a combination of these three fields 
      key = ticket['server'] + ticket['serviceName'] + ticket['remediation']

      bucket = None
      if key in buckets:
        bucket = buckets[key]
        bucket.append(ticket)
      else:
        bucket = [ticket]
        buckets[key] = bucket

    return buckets.values()

  def change_control_validation(self, tickets):
    '''Cancel tickets as spurious when a change control window is open'''
    # Test each ticket against the change control window
    # Valid tickets go into the active bin
    # Invalid tickets go into the cancelled bin

    # Simulate real change lookup by randomly cancelling 1:3 tickets

    #for t in tickets:
    #  r = randint(0,2)
    #  if 0 == r:
     #   self._cancel.append(t)
     # else:
     #   self._active = tickets
    self._active = tickets
    
  def time_sort_tickets(self, ticket_lists):
    '''Sort related tickets by timestamp'''

    retval = [ ]
    # sort each list of dict by embedded timestamp
    for tl in ticket_lists:
      s = sorted(tl, key=itemgetter('openTime'))
      retval.append(s)

    # Make most recent first
    # The most recent ticket Will be marked active below
    # This becomes important if we want to use persistent storage later
    # for cross job run de-duplication 

    retval.reverse()

    return retval

  def enable_roles(self):
    '''Enable all roles for which there are open tickets'''
    roles = {}
    for a in self._active:
      key = a['remediation'].replace(' ', '_')+ "_role_enabled"
      roles[key] = 1

    self._roles = list( roles.keys() )

  def work(self):
    '''Main application logic'''
    tickets = self._module.params['tickets']
    # find related tickets
    buckets = self.split_related_tickets(tickets)
    # sort related tickets by timestamp
    time_sort = self.time_sort_tickets(buckets)

    # All non-current duplicates should be cancelled
    active = []
    #f = open("tickets_obj.json", "w")
    #f.write(json.dumps(tickets))
    #f.close()
    for ts in time_sort:
      active.append(ts[0])
      if len(ts) > 1:
        self._cancel.append(ts[1:])

    # test remaining tickets against change control window
    self.change_control_validation(active)
    self.enable_roles()

    return json.dumps({ 
        'active': self._active, 
        'cancel': self._cancel,
        'roles' : self._roles,
      })

  def run(self):
    '''Application entry point'''
    ret_val = self.work()
    self._module.exit_json(changed=False, meta=ret_val)

if __name__ == '__main__':
    ThisModule().run()
