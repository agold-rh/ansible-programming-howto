#/usr/bin/env python
'''
This sample has a ServiceNow installation and the pysnow 
library as a dependency. It is included as 
a real-world example of making a network request to an external
data source and then using di_tools to output the data in a 
format consumable by ansible / tower.

NOTE: the most interesting part of this script is the injection of
secret data (passwords, etc.) via environment variables to avoid
the inclusion of sensitive data in the code repository. As of this 
writing, I don't believe there is any way to inject secrets into
an inventory script other than this, except for the use of a system 
secrets file. There appear to be several PRs open to enable the use
of vaulted data in inventory scripts, so the situation will probably
change very shortly.

Data sources for dynamic Ansible inventories.
The only requirement of a new data source is that it must
implement the get_groups() method. get_groups() must return 
a list of di_tools.Group objects. The SnowAccess class below
is a more elaborate example, but the only **requirement** is
that get_groups() be implemented correctly.
Groups may NOT be named "all".
The "ungrouped" hosts must not be in any other group.
'''
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

import os
import sys
import di_tools
import pysnow

class SnowAccess(object):
  '''
  Get ServiceNow host data.
  You may create a group named "ungrouped"
  You may NOT create a group named "all"
  '''
  # Connection details
  url = None
  url_env = 'SNOW_URL'

  username = None
  username_env = 'SNOW_USERNAME'

  password = None
  password_env = 'SNOW_PASSWORD'

  # Consider moving this to an env variable
  api_path = '/table/cmdb_ci_server'

  # Where we keep the retrieved data
  all_records = [ ]

  def __init__(self):
    '''The constructor'''

    # No reasonable defaults exist, so we must raise

    self.url = os.getenv(self.url_env)
    if not self.url:
      raise Exception("The environment must set SNOW_URL")

    self.username = os.getenv(self.username_env)
    if not self.username:
      raise Exception("The environment must set SNOW_USERNAME")

    self.password = os.getenv(self.password_env)
    if not self.password:
      raise Exception("The environment must set SNOW_PASSWORD")

    self.run()

  def run(self):
    '''Main logic routine'''
    host = self.url
    user = self.username
    pwd = self.password
    api = self.api_path

    # Create ServiceNow client object
    c = pysnow.Client(host=host, user=user, password=pwd)
    c.parameters.display_value = True
    c.parameters.exclude_reference_link  = True
    cmdb = c.resource(api_path=api)

    # Query
    qb = (
        pysnow.QueryBuilder()
        .field('subcategory').contains('Windows Server')
        .AND()
        .field('u_status').equals('Deployed')
        .AND()
        .field('host_name').order_ascending()
    )

    try:
        response = cmdb.get(query=qb)
    except pysnow.exceptions.ResponseError as e:
        sys.stderr.write(str(e))
        sys.exit(EXIT_FAILURE)

    # Map SNOW record to something more convenient
    results = [ ]
    for record_raw in response.all():
      record_refined = {
        "u_ci_id":record_raw['u_ci_id'], 
        "classification":record_raw['classification'], 
        "sys_class_name":record_raw['sys_class_name'], 
        "u_technicalinfraapproval":record_raw['u_technicalinfraapproval'], 
        "u_ccbapprover":record_raw['u_ccbapprover'], 
        "host_name":record_raw['host_name'], 
        "sys_domain":record_raw['sys_domain'], 
        "category":record_raw['category'], 
        "sys_class_name":record_raw['sys_class_name'], 
        "fqdn":record_raw['fqdn'], 
        "ip_address":record_raw['ip_address'], 
        "os":record_raw['os'], 
        "name":record_raw['name'], 
        "company":record_raw['company']
      }

    self.all_records = results

  def get_groups(self):
    '''
    Raw SNOW data is retrieved in run()
    Raw SNOW data is converted into a more convenient format in run()
    Use the data in self.all_records (convenient format) to create 
    Tower inventory groups as shown in the example (wintel) below.
    '''
    groups = [ ]

    # Optional
    # ug = di_tools.Group("ungrouped")
    # Group set_var() could be done here
    # Add hosts that do not belong to any group other than "all"

    # The group created by this data source
    wg = di_tools.Group("wintel")
    wg.set_var("ansible_port", 5986)
    wg.set_var("ansible_connection", "winrm")
    wg.set_var("ansible_winrm_transport", "ntlm")
    wg.set_var("ansible_winrm_server_cert_validation", "ignore")

    # Add hosts to wintel group
    for r in self.all_records:
      n = r["name"]
      h = di_tools.Host(n)
      # If hostvars existed, we'd perform one or more h.set_var() here
      wg.add_host(h)

    groups.append(wg)

    # Other groups could be created here and appended to the groups list as
    # demonstrated above

    return groups

if "__main__" == __name__:
  sys.exit(0)
