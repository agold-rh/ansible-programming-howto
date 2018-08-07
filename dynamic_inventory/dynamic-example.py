#!/usr/bin/env python
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
# README
# To create a new dynamic inventory script, simply create a new data source
# then create a script similar to this one, importing your new data source.
# (see simple_data_sources.py and READ THE COMMENTS) 
# (see more_interesting_data_sources.py and READ THE COMMENTS) 
################################################################################

import sys
import di_tools
import simple_data_sources as sds

if "__main__" == __name__:
  # The application requires a list of data sources
  data_sources = []

  # Instantiate one or more data sources
  # nh = sds.NoHosts()
  st = sds.Static()

  # Add one or more data sources to the input list
  #data_sources.append(nh)
  data_sources.append(st)

  # Instantiate a dynamic inventory application
  # passing in the list of data sources
  a = di_tools.Application(data_sources)

  # Execute the application and return status
  sys.exit(a.run())

