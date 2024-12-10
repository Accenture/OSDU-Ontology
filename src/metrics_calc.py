import numpy as np
import networkx as nx
from .kg_rep import *

import typing
from typing import Any, Dict, List, Optional, Tuple


def compute_metrics(class_ontology_dict: dict, prop_ontology_dict: dict) -> dict:
    """Generates a dictionary of metrics
        Keys:
            "ADIT-LN" - the average length of a path from a root ontology node to a leaf node
            "Average number of shortest paths" - the average number of shortest paths between nodes
            "Number of classes" - the total number of classes/nodes in the ontology
            "Number of inheritance relationships" - the total number of superclass edges in the ontology
            "Number of property relationships" - the total number of property edges in the ontology
            "Number of leaf classes" - number of classes that are not inherited by any other class
            "Relationship richness" - non-inheritance edges out of all edges
            "Inheritance richness" - number of inheritance relationships / number of classes
            "Attribute richness" - number of non-inheritance properties / number of classes
            "Average number of shortest paths": how many nodes each node is connected to, on average, in the
            "Average shortest path length": the length of a given shortest path between nodes, on average
            "Diameter of inheritance graph": the length of the shortest path between the most distanced nodes
            "Average number of shortest paths, full graph": avg_num_shortest_paths_full,
            "Average shortest path length, full graph": avg_shortest_path_full,
            "Diameter of full graph": diameter_ont_g,

    Args:
        class_ontology_dict (dict): Complete dictionary mapping OSDU class names to ClassRep objects.
        prop_ontology_dict (dict): Complete dictionary mapping explored OSDU property names to PropertyRep objects

    Returns:
        metrics_dict: dictionary mapping metric key to calculated metric value for the OSDU ontology
    """
    # Construct ontology inheritance graph
    inheritance_g = extract_inheritance_graph(class_ontology_dict, prop_ontology_dict)

    # Construct ontology property (non-inheritance) graph
    property_g = extract_property_graph(class_ontology_dict, prop_ontology_dict)

    # Construct full graph
    ont_graph = nx.compose(inheritance_g, property_g)

    # Calculate ADIT-LN
    adit_ln, nol = calc_adit_ln_metrics(
        class_ontology_dict, prop_ontology_dict, inheritance_g
    )

    # Calculate Richness metrics
    rel_richness = calc_relationship_richness(property_g, inheritance_g)
    inheritance_richness = calc_inheritance_richness(inheritance_g)
    attribute_richness = calc_attribute_richness(property_g)

    # Calculate shortest paths metrics in both inheritance structure and full ontology graph
    avg_num_shortest_paths, avg_shortest_path, diameter_inheritance_g = (
        calc_shortest_path_metrics(inheritance_g)
    )
    avg_num_shortest_paths_full, avg_shortest_path_full, diameter_ont_g = (
        calc_shortest_path_metrics(ont_graph)
    )

    return {
        "Number of classes": calc_num_nodes(inheritance_g),
        "Average number of shortest paths": avg_num_shortest_paths,
        "Average shortest path length": avg_shortest_path,
        "Diameter of inheritance graph": diameter_inheritance_g,
        "Average number of shortest paths, full graph": avg_num_shortest_paths_full,
        "Average shortest path length, full graph": avg_shortest_path_full,
        "Diameter of full graph": diameter_ont_g,
        "Number of inheritance relationships": calc_num_inheritance_edges(
            inheritance_g
        ),
        "Number of property relationships": calc_num_noninheritance_edges(property_g),
        "Number of leaf classes": nol,
        "ADIT-LN": adit_ln,
        "Relationship richness": rel_richness,
        "Inheritance richness": inheritance_richness,
        "Attribute richness": attribute_richness,
    }


def extract_inheritance_graph(
    class_ontology_dict: dict, prop_ontology_dict: dict
) -> nx.MultiDiGraph:
    # Build a directed graph - TODO: verify that it is acyclic?
    inheritance_g = nx.MultiDiGraph()

    inheritance_g.add_nodes_from(list(class_ontology_dict.keys()))

    for class_key, class_rep in class_ontology_dict.items():
        for superclass_key in class_rep.superclass_list:
            superclass_name = extract_classname_from_filename(superclass_key)
            inheritance_g.add_edge(superclass_name, class_key)

    return inheritance_g


def extract_property_graph(
    class_ontology_dict: dict, prop_ontology_dict: dict
) -> nx.MultiDiGraph:
    property_g = nx.MultiDiGraph()

    property_g.add_nodes_from(list(class_ontology_dict.keys()))

    # For each property, add an edge between each of the domain classes and the range class
    for prop_key, prop_rep in prop_ontology_dict.items():
        for range_name in prop_rep.range:
            property_g.add_node(range_name)
            e_bunch = zip(
                prop_rep.domain,
                [range_name] * len(prop_rep.domain),
                [prop_rep.name] * len(prop_rep.domain),
            )
            property_g.add_edges_from(e_bunch)

    return property_g


def calc_adit_ln_metrics(
    class_ontology_dict: dict, prop_ontology_dict: dict, inheritance_g: nx.MultiDiGraph
) -> tuple[float, int]:
    """Calculate the average length of a path from a root ontology node to a leaf node (ADIT-LN),
        and the number of classes that are not inherited by any other class (number of leaf classes, NOL).
        Uses the inheritance graph of an ontology.
    Args:
        inheritance_g (nx.MultiDiGraph): Inheritance graph of the ontology, with edges pointing from superclass source to subclass target
    Returns:
        float: value for ADIT-LN
        int: value for NOL
    """
    leaf_class_list = list(class_ontology_dict.keys())
    root_class_list = []

    for class_key, class_rep in class_ontology_dict.items():
        if (len(class_rep.superclass_list) == 1) and class_rep.superclass_list[
            0
        ] == "owl:Thing":
            root_class_list.append(class_key)
        else:
            for superclass_key in class_rep.superclass_list:
                superclass_name = superclass_key

                if (superclass_name not in literals_dict) and (
                    superclass_name in leaf_class_list
                ):
                    leaf_class_list.remove(superclass_name)

    noc = len(root_class_list)
    nol = len(leaf_class_list)

    num_paths_matrix = np.zeros((noc, nol)) + 1e-10
    path_lengths_matrix = np.zeros((noc, nol))

    for i, root_class in enumerate(root_class_list):
        for j, leaf_class in enumerate(leaf_class_list):
            if nx.has_path(inheritance_g, source=root_class, target=leaf_class):
                paths_gen = nx.all_simple_paths(
                    inheritance_g, source=root_class, target=leaf_class
                )
                comp_paths = list(paths_gen)
                paths = [path for path in comp_paths if len(path) != 1]

                num_paths = len(paths)
                num_paths_matrix[i, j] = num_paths if num_paths != 0 else 1e-10

                path_lengths = [len(path) for path in paths] if paths != [] else [0]
                path_lengths_matrix[i, j] = sum(path_lengths)
    num_paths = np.sum(num_paths_matrix)
    adit_ln = np.sum(path_lengths_matrix) / (num_paths + 1e-8)
    return adit_ln, nol


def calc_shortest_path_metrics(ont_graph: nx.MultiDiGraph) -> tuple[float, float, int]:
    """Calculates shortest-paths-based topology metrics for a given graph.
        Includes
            Average number of shortest paths in the graph (avg_num_shortest_paths),
            Average length of a given shortest path in the graph (avg_shortest_path),
            Diameter of the graph, or shortest path length between the most distanced nodes in the graph (diameter)
    Args:
        ont_graph (nx.MultiDiGraph):
    Returns:
        float: value for avg_num_shortest_paths
        float: value for avg_shortest_path
        int: value for diameter
    """
    s_paths = dict(nx.shortest_path(ont_graph))
    num_s_paths = sum([len(list(s_paths[key].values())) for key in s_paths.keys()])

    shortest_path_lengths = [
        [len(list(path)) for path in s_paths[key].values()] for key in s_paths.keys()
    ]
    diameter = np.max([np.max(path_list) for path_list in shortest_path_lengths])

    return (
        num_s_paths / calc_num_nodes(ont_graph),
        np.sum([np.sum(path) for path in shortest_path_lengths]) / num_s_paths,
        diameter,
    )


def calc_num_nodes(ont_graph: nx.MultiDiGraph) -> float:
    return ont_graph.number_of_nodes()


def calc_num_inheritance_edges(ont_graph: nx.MultiDiGraph) -> float:
    return ont_graph.number_of_edges()


def calc_num_noninheritance_edges(prop_graph: nx.MultiDiGraph) -> float:
    return prop_graph.number_of_edges()


def calc_relationship_richness(
    prop_graph: nx.MultiDiGraph, ont_graph: nx.MultiDiGraph
) -> float:
    p = calc_num_noninheritance_edges(prop_graph)
    h = calc_num_inheritance_edges(ont_graph)
    return p / (h + p + 1e-10)


def calc_inheritance_richness(ont_graph: nx.MultiDiGraph) -> float:
    return calc_num_inheritance_edges(ont_graph) / calc_num_nodes(ont_graph)


def calc_attribute_richness(prop_graph: nx.MultiDiGraph) -> float:
    return calc_num_noninheritance_edges(prop_graph) / calc_num_nodes(prop_graph)
