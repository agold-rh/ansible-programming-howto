# python 3 headers, required if submitting to Ansible
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {  'metadata_version': '0.1',
                      'status': ['preview'],
                      'supported_by': 'agold@redhat.com'}
DOCUMENTATION = """
      lookup: pglook
        author: Andrew Gold <agold@redhat.com>
        version_added: "0.1"
        short_description: Store JSON data in postgresql database
        description:
            - Use postgresql to persist JSON data across playbook runs
        options:
          _terms: key=value option arguments only.
            description: Database connection parameters.
          dbname: 
            description: The name of the database
            required: true
            default: 'persist'
            env:
              - name: ANSIBLE_PGLOOK_DBNAME
            ini:
              - section: pglook
                key: dbname
          user: 
            description: The name of the database user account
            required: true
            default: 'persist'
            env:
              - section: pglook
            ini:
              - section: pglook
                key: user
          host: 
            description: The name of the database host
            required: true
            default: '127.0.0.1'
            env:
              - name: ANSIBLE_PGLOOK_HOST
            ini:
              - section: pglook
                key: host
          password: 
            description: The database user password
            required: true
            env:
              - name: ANSIBLE_PGLOOK_PASSWORD
          keyname: 
            description: >
              The unique key to your data. Each key points to a different data set.
              Subject to db configuration limits, unlimited keys are available.

            required: true
            env:
              - name: ANSIBLE_PGLOOK_KEYNAME
            ini:
              - section: pglook
                key: keyname
          action: 
            description: >
              The non-read action specifier. 
              Currently the only valid value is 'WRITE'. 
              When WRITE is specified and the 'content' option is used, the value of 'content'
              will be written to the database.

            required: false
            env:
              - name: ANSIBLE_PGLOOK_ACTION
          content: 
            description: >
            Content to be written to the database.
            Must be used with the 'action' option (see above).

            required: false
            env:
              - name: ANSIBLE_PGLOOK_CONTENT
        notes:
          - XXX
          - XXX
"""
from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.lookup import LookupBase

try:
  from __main__ import display
except ImportError:
  from ansible.utils.display import Display
  display = Display()

import psycopg2
import json
import re

class LookupModule(LookupBase):
  args = None
  conn = None

  def process_args(self, kwargs):
    '''Process command input'''

    required = [
      'password',
      'keyname'
    ]

    optional = [
      'dbname',
      'user',
      'host',
      'reader',
      'writer',
      'action',
      'content'
    ]

    args = {
      'dbname' : 'persist',
      'user' : 'persist',
      'host' : '127.0.0.1',
      'reader' : 'tower_reader',
      'writer' : 'tower_writer'
    }

    restricted = [
      'reader',
      'writer'
    ]

    for r in required:
      if not r in kwargs:
        return False, "Found Missing a required argument: ({0})".format(r)
      else:
        args[r] = kwargs[r]

    for o in optional:
      if o in kwargs:
        args[o] = kwargs[o]

    self.args = args

    # Unexpected arguments
    unknown = set(kwargs) - set(args)
    if len(unknown) > 0:
        return False, "Found invalid key(s) in input ({0})".format(unknown)

    # alpha numeric, underscore only
    pat = re.compile("\w+")
    for r in restricted:
      if not pat.match(args[r]):
        return False, "Malformed reader or writer ({0})".format(args[r])

    return True, ''

  def connection_string(self, args):
    '''Build DB connection string'''

    args = self.args

    return "dbname='{0}' user='{1}' host='{2}' password='{3}'".format(
      args['dbname'],
      args['user'],
      args['host'],
      args['password']
    )

  def read(self):
    '''Read existing data from db'''
    args = self.args
    cur = self.conn.cursor()
    keyname = args['keyname']
    reader = self.args['reader']
    statement = "SELECT * FROM {0}(%(keyname)s) AS jdata".format(reader)
    cur.execute(statement, { 'keyname': keyname })
    jdata = cur.fetchone()
    cur.close()

    return list(jdata)

  def write(self):
    '''Update or insert new data'''
    args = self.args
    cur = self.conn.cursor()
    keyname = args['keyname']
    writer = self.args['writer']
    data = json.dumps(args['content'])
    statement =  "SELECT * FROM {0}( %(name)s, %(jdata)s::jsonb )".format(writer)
    cur.execute(statement, { 'name' : keyname, 'jdata' : data })

    q = cur.query
    self.conn.commit()
    cur.close()

    return [ q ]

  def run(self, terms, variables=None, **kwargs):
    '''Main entry point of plugin'''

    success, msg = self.process_args(kwargs)
    if not success:
      raise AnsibleError("postgresql plugin ERROR: {0}".format(msg))

    try:
      self.conn = psycopg2.connect(self.connection_string(self.args))
    except:
      raise AnsibleError("postgresql plugin ERROR: Unable to open db connection")


    # Read when action isn't understood
    if 'action' in self.args and 'WRITE' == self.args['action']:
      return self.write()
    else:
      return self.read()

    self.conn.close()

    return jdata
