** **About Ontology Validator** **
This project contains a Python script to calculate structural metrics for an ontology. The script evaluates key aspects of the ontology's structure, including the number of classes, relationships, graph diameter, and various "richness" metrics related to inheritance, attributes, and relationships. These metrics provide valuable insights into the complexity and interconnectivity of the ontology.
The script outputs the following metrics:

Number of classes: Total number of classes in the ontology.
Average number of shortest paths: The average number of shortest paths between classes.
Average shortest path length: The average length of the shortest paths between all pairs of classes.
Diameter of inheritance graph: The longest path in the inheritance graph.
Average number of shortest paths (full graph): The average number of shortest paths in the full graph.
Average shortest path length (full graph): The average shortest path length in the full graph.
Diameter of full graph: The longest path in the full graph.
Number of inheritance relationships: The number of relationships representing inheritance between classes.
Number of property relationships: The number of property relationships in the ontology.
Number of leaf classes: The number of classes that do not have any subclasses.
ADIT-LN: The average depth of the inheritance tree of all leaf nodes.
Relationship richness: Ratio between non-inheritance and inheritance relationships.
Inheritance richness: The average number of number of subclasses per class.
Attribute richness: The average number of non-inheritance properties per class (datatype and objecttype properties)
** **Running the Ontology Validator** **
python calculate_metrics_for_ttl.py -p "local/path/to/ontology.ttl" -o "desired/local/path/to/output.json
