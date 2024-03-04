# OSDU Ontology 
This is an open source ontology for the subsurface energy data based on [3rd release of the schema files and standards ](https://community.opengroup.org/osdu/platform/data-flow/data-loading/open-test-data/-/tree/master/rc--3.0.0/3-schema) specified by the [Open Subsurface Data Universe](https://osduforum.org/) community.
Please see the [documentation](./docs) for more information about OSDU and how the ontology is designed.

# License
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
The OSDU Ontology is licensed under the Apache License 2.0 - see [License](./License).

# Ontology Files
Load the [.ttl](./ttl/OSDU.ttl) in your favorite ontology editor, e.g. [Protege](https://protege.stanford.edu/products.php#desktop-protege).

# Ontology Generator
A tool to convert the OSDU data loading schema to an OWL3-based ontology, in .ttl format.

# Dependecies
Python3, with libraries numpy and regex.

# Installation
~~~
git clone https://github.com/Accenture/OSDU-Ontology.git
~~~

# Usage
Download the latest OSDU schema from [this location.] (https://community.opengroup.org/osdu/platform/data-flow/data-loading/open-test-data/-/tree/master/rc--3.0.0/3-schema)

From a terminal in the osdu-ontology-generator folder:
~~~
python3 -m create_ontology --src path_to_full_schema/
~~~

To run metric calculation (with reporting in terminal):
~~~
python3 -m create_ontology --src path_to_full_schema/ --report_metrics
~~~
