#/usr/bin/env python
'''Data sources for dynamic Ansible inventories.
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

class NoHosts(object):
  '''What happens when no hosts are returned?'''
  def get_groups(self):
    '''Mandatory interface element'''
    group_all = di_tools.Group("all")
    group_all.set_var("GLOBAL", 42)
    return [ group_all ]

class Static(object):
  '''Example using static data
  Play around with these values and see how they change your script output
  '''
  def get_groups(self):
    '''Mandatory interface element'''
    host1 = di_tools.Host("host1")
    host1.set_var("k1", "v1")
    host1.set_var("k2", "v2")
    host1.set_var("k3", "v3")
    
    host2 = di_tools.Host("host2")
    host2.set_var("k1", "v1")
    host2.set_var("k2", "v2")
    host2.set_var("k3", "v3")

    host3 = di_tools.Host("host3")
    host3.set_var("k1", "v1")
    host3.set_var("k2", "v2")
    host3.set_var("k3", "v3")

    group_all = di_tools.Group("all")
    group_all.set_var("GLOBAL", 42)

    group1 = di_tools.Group("group1")
    group1.add_hosts([host1, host2, host3])

    group2 = di_tools.Group("group2")
    group2.add_host(host3)

    group3 = di_tools.Group("group3")
    group3.set_var("g3var", 24)
    host_duplicate = di_tools.Host("host1")
    host_duplicate.set_var("k2", "v2")
    group3.add_host(host_duplicate)

    group3.add_child_group(group2)

    ungrouped = di_tools.Group("ungrouped")
    host_new = di_tools.Host("new_host")
    ungrouped.add_host(host_new)

    return [ group_all, group1, group2, group3, ungrouped ]


if "__main__" == __name__:
  sys.exit(0)
