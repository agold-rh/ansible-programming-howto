#!/usr/bin/env python
''' Library to fascilitate the retrieval of dynamic inventory data.
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
import sys
import json
import argparse

EXIT_SUCCESS = 0
EXIT_FAILURE = 1

class Host(object):
  '''Partial model of inventory host information'''
  def __init__(self, name):
    '''The constructor'''
    self._name = name
    self.vars = {}

  @property 
  def name(self):
    return self._name

  @name.setter
  def name(self, value):
    self._name = value

  def set_var(self, key, value):
    '''Set a host var'''
    self.vars[key] = value

  def data(self):
    '''Return the host data as a dict'''
    data = { 
      self._name : self.vars
    }

    return data

class Group(object):
  '''Partial model of inventory group information'''
  def __init__(self, name):
    '''The constructor'''
    self._name = name
    self.hosts = set() 
    self.children = set()
    self.vars = {}

  @property 
  def name(self):
    return self._name

  @name.setter
  def name(self, value):
    self._name = value

  def set_var(self, key, value):
    '''Set a group_var'''
    self.vars[key] = value

  def add_child_group(self, child):
    '''Add a child group. Child is a Group object'''
    self.children.add(child)

  def add_children_groups(self, children):
    '''Add a set of child groups. children is a set of Group objects'''
    cset = set(children)
    self.children = self.children.union(cset)

  def add_host(self, host):
    '''Add a Host object to this group'''
    self.hosts.add(host)

  def add_hosts(self, hosts):
    '''Add a list of Host objects to the group'''
    hset = set(hosts)
    self.hosts = self.hosts.union(hset)

  def merge(self, rhs):
    '''Merge rhs into self'''
    self.name = rhs.name
    for h in rhs.hosts:
      self.hosts.add(h)
    for c in rhs.children:
      self.children.add(c)
    for k in rhs.vars.keys():
      if k in self.vars:
        if self.vars[k] != rhs.vars[k]:
          raise Exception("Conflicting vars in group ({0}) merge({1})".format(self.name, k))
      else:
        self.vars[k] = rhs.vars[k]

  def hosts_names(self):
    '''Return a list of the names of the hosts in this group
    This does not return child group data
    '''
    hosts = []
    for h in self.hosts:
        hosts.append(h.name)

    hosts.sort()
    return hosts

  def children_names(self):
    '''Return a list of the child group names
    This does not return child group data
    '''
    children = []
    for c in self.children:
        children.append(c.name)

    children.sort()
    return children

#  def hosts_data(self):
#    '''Return a dict with the host names as keys and the corresponding hostvars as a nested dict
#    This does not return child group data
#    '''
#    data = { }
#    for h in self.hosts:
#      data[h.name] = h.data()[h.name]
#    return data

  def as_data(self):
    '''Return the group data as a dict'''
    hosts = list(self.hosts)
    hosts.sort()

    children = list(self.children)
    children.sort()

    data = { 
      'hosts': self.hosts_names(),
      'vars': self.vars,
      'children': self.children_names()
    }

    return data

class Application(object):
  '''This application'''

  def __init__(self, dataSourceList):
    '''The constructor'''

    self.args = None
    self.dataSourceList = dataSourceList
    self.init_data()
    self.process_input()

  def init_data(self):
    '''Non-constructor initialization'''

    all_group = Group('all')
    un_group = Group('ungrouped')

    #  Data will be added to this basic structure
    self.everything = {
      'all': all_group,
      'ungrouped': un_group
    }

  def process_input(self):
    '''Process the command line instructions'''
    if self.args:
      return

    description = 'Get dynamic Ansible inventory data'
    parser = argparse.ArgumentParser(description=description)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--host')
    group.add_argument('--list', action='store_true')

    self.args = parser.parse_args()

  def merge_groups(self, groups):
    ''' Add new groups to the self.everything data structure
    '''
    # For each group
    for group in groups:
      if '_meta' == group.name:
        raise Exception("You may not create a group named '_meta'")
      if group.name in self.everything:
        self.everything[group.name].merge(group)
      else:
        # Otherwise, create the group
        self.everything[group.name] = group

  def set_all_and_meta(self):
    ''' Set the hosts field of group all. Set the hostvars field of _meta. Check for hostvar conflicts.
    '''
    hosts = set()
    hostvars = {}

    group_names = self.everything.keys()
    for group_name in group_names:
      group = self.everything[group_name]
      for h in group.hosts:
        hosts.add(h)
        if h.name in hostvars:
          for var_key in h.vars:
            if var_key in hostvars[h.name]:
              # The same variable for a host has been set in more than one group
              # raise if the values differ
              if hostvars[h.name][var_key] != h.vars[var_key]:
                raise Exception("Host var conflict in group ({0}) host ({1}) var ({2})".format(group.name, h.name, var_key))
            else:
              hostvars[h.name][var_key] = h.vars[var_key]
        else:
          hostvars[h.name] = h.vars

    all_group = self.everything['all']
    # Looks like an overwrite, but is really a merge (all is one of the processed groups)
    all_group.hosts = hosts

    meta = {
      'hostvars': hostvars
    }
    self.everything['_meta'] = meta

  def prepare_for_json(self):
    '''json cannot process set objects'''
    data = { }

    # Meta has no set data
    data['_meta'] = self.everything['_meta']

    group_names = self.everything.keys()

    # Meta has already been captured above
    group_names.remove('_meta')

    # Convert set data to lists
    for group_name in group_names:
      data[group_name] = self.everything[group_name].as_data()

    # All cannot be a child of itself
    group_names.remove('all')

    data['all']['children'] = group_names

    return data

  def run(self):
    '''Main application entry point'''
    self.init_data()
    for dsl in self.dataSourceList:
      self.merge_groups(dsl.get_groups())

    self.set_all_and_meta()
    data = self.prepare_for_json()

    if self.args.host:
      hv = self.everything['_meta']['hostvars']
      if self.args.host in hv:
        # output the hostvars for the host
        print(json.dumps(hv[self.args.host], indent=4))
      else:
        # Theoretically impossible when run by Tower :)
        raise Exception("Request for hostvars of unknown host ({0})".format(self.args.host))
    else:
      # --list IS the default behavior
      print(json.dumps(data, indent=4))

    return EXIT_SUCCESS

if '__main__' == __name__:
  sys.exit(0)
