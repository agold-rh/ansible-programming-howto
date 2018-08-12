###pglook  
A lookup plugin that provides fact persistence across playbook executions.


This example is probably too complex for a first lookup_plugin attempt, and I'll try to add something a little simpler as soon as time permits.


###Overview
This plugin is very Tower centric.
The following were some design considerations.
*No data is persisted on the local file system. This was important because the plugin was intended to be invoked from a Tower instance rather than from the Ansible Core command line.
*The 3rd party data persistence resources used are those used by Ansible Tower itself and no addition to the Tower venv is required. That is, Tower uses PostgreSQL for data storage and also uses the Python “psycopg2” library to interact with PostgreSQL.
*This plugin might also have been implemented as one of the other plugin types or as a module.  The process of implementation exposed the convenience of the lookup plugin idiom. 
*If we regard convenience as important, we might also regard the numerous input fields as clunky and inelegant. Bear in mind that most of the input parameters can also be stored in ansible.cfg as defaults, or else set as environmental variables in the Tower environment. This greatly streamlines the plugin usage.


###Files
*example.yml is a tasks file that demonstrates usage of the plugin.
*pg_howto.txt explains how to set up the PostgreSQL database for this plugin. It is very terse and expects a certain comfort with PostgreSQL. I’ll try to add more comprehensive instructions as time permits.
*pg_look.py is the plugin implementation itself.
*tower_reader.sql is (very) simple stored procedure used to read persistent data.
*tower_writer.sql is a (very) simple stored procedure used to write persistent data.  

###Quirks
*The way that Ansible modules and plugins add ansible.cfg and environment variable support is … interesting. Essentially it boils down to setting the “DOCUMENTATION” string with embedded YAML. The interesting part is this: if there is ANY whitespace flaw or error in the embedded YAML string, the configuration processing fails and there is no useful feedback; it just doesn’t work. If you have difficulty getting the configuration processing to work correctly, try the following.
*Check out the Ansible development branch from github
*Look at ansible/examples/DOCUMENTATION.yml
*Paste it into your plugin file without any whitespace errors. I use vim and just “:r DOCUMENTATION.yml” it in. Carefully replace the boilerplate words with your own value. Note that DOCUMENTATION.yml is not comprehensive. In the source tree look at the other plugins of the type you are creating for examples of other valid fields.

