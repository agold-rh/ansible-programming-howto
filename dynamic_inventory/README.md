https://docs.ansible.com/ansible/latest/dev_guide/developing_inventory.html

Dynamic inventory script tool kit and examples.

Take a look at dynamic-example.py to start, then look at simple_data_source.py.
For something more real-world, look at more_interesting_data_source.py.

To run a dynamic inventory script create a project level directory and 
put the script (dynamic-example.py) and the supporting library (di_tools.py)
in that directory. There are other ways of dealing with python library locations
but the simplest is to just keep di_tools.py in the same directory as your
new script; this works on both core and tower.

Pass the path to your script via the "-i" switch from the core command line
or configure a dynamic inventory source from within tower. See the
more_interesting_data_sources.py file for an example of injecting secrets 
into your script.

