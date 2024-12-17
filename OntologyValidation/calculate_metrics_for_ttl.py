from src.metrics_calc import compute_metrics
from src.kg_rep import ClassRep, PropertyRep
from rdflib import Graph, BNode
import argparse
import json
import numpy as np

class_query = """
SELECT DISTINCT ?a
WHERE {
    ?a a owl:Class .
    FILTER NOT EXISTS { 
        ?a a owl:Restriction .
    }
}"""
class_superclass_query = """
SELECT DISTINCT ?b
WHERE {
    ?name rdfs:subClassOf ?b .
    FILTER NOT EXISTS { 
        ?b a owl:Restriction .
    }
}
"""
class_comment_query = """
SELECT DISTINCT ?b
WHERE {
    ?name rdfs:comment ?b
}
"""
class_label_query = """
SELECT DISTINCT ?b
WHERE {
    ?name skos:prefLabel ?b
}
"""

objprop_query = """
SELECT DISTINCT ?a
WHERE {
    ?a a owl:ObjectProperty .
}"""

dprop_query = """
SELECT DISTINCT ?a
WHERE {
    ?a a owl:DatatypeProperty .
}"""

prop_domain_query = """
SELECT DISTINCT ?b
WHERE {{
    ?name a {proptype} .
    ?name rdfs:domain ?b
}}
"""
prop_domain_union_query = """
SELECT DISTINCT ?c
WHERE {{
    ?name a {proptype} .
    ?name rdfs:domain/(owl:unionOf/rdf:rest*/rdf:first)* ?c .
}}
"""
prop_comment_query = """
SELECT DISTINCT ?b
WHERE {{
    ?name a {proptype} .
    ?name rdfs:comment ?b
}}
"""
prop_range_query = """
SELECT DISTINCT ?b
WHERE {{
    ?name a {proptype} .
    ?name rdfs:range ?b
}}

"""
prop_range_union_query = """
SELECT DISTINCT ?c
WHERE {{
    ?name a {proptype} .
    ?name rdfs:range/(owl:unionOf/rdf:rest*/rdf:first)* ?c .
}}
"""
prop_pattern_query = """
SELECT DISTINCT ?b
WHERE {{
    ?name a {proptype} .
    ?name rdfs:pattern ?b
}}
"""


def get_class_reps_from_graph(g):
    class_dict = {}
    qres = g.query(class_query)
    for row in qres:
        if not isinstance(row.a, BNode):
            name = str(row.a)
            superclass_list = [
                str(row.b)
                for row in g.query(class_superclass_query, initBindings={"name": row.a})
            ]
            superclass_list = [s for s in superclass_list if (s != name)]
            comment_list = [
                str(row.b)
                for row in g.query(class_comment_query, initBindings={"name": row.a})
            ]

            label = "; ".join(
                [
                    str(row.b)
                    for row in g.query(class_label_query, initBindings={"name": row.a})
                ]
            )

            c = ClassRep(
                name=name,
                superclass_list=superclass_list,
                comments=comment_list,
                pref_label=label,
                process_name_flag=False,
            )
            class_dict[name] = c
    return class_dict


def get_prop_reps_from_graph(g):
    obj_qres = g.query(objprop_query)

    data_qres = g.query(dprop_query)
    prop_type_dict = {obj.a: "owl:ObjectProperty" for obj in obj_qres}
    prop_type_dict.update({data.a: "owl:DatatypeProperty" for data in data_qres})

    prop_dict = {}
    for name, type in prop_type_dict.items():
        domain_list = [
            row.b
            for row in g.query(
                prop_domain_query.format(proptype=type), initBindings={"name": name}
            )
        ]
        domain_union_list = [
            row.c
            for row in g.query(
                prop_domain_union_query.format(proptype=type),
                initBindings={"name": name},
            )
        ]
        if len(domain_union_list) > 0:
            domain_list = [
                domain for domain in domain_union_list if not isinstance(domain, BNode)
            ]

        range_list = [
            row.b
            for row in g.query(
                prop_range_query.format(proptype=type), initBindings={"name": name}
            )
        ]
        range_union_list = [
            row.c
            for row in g.query(
                prop_range_union_query.format(proptype=type),
                initBindings={"name": name},
            )
        ]
        if len(range_union_list) > 0:
            range_list = [
                range for range in range_union_list if not isinstance(range, BNode)
            ]

        comment_list = [
            row.b
            for row in g.query(
                prop_comment_query.format(proptype=type), initBindings={"name": name}
            )
        ]
        patterns = [
            row.b
            for row in g.query(
                prop_pattern_query.format(proptype=type), initBindings={"name": name}
            )
        ]
        p = PropertyRep(
            name=str(name),
            prop_type=type,
            domain_name_list=[str(d) for d in domain_list],
            range_name="",
            range_list=[str(r) for r in range_list],
            comments=comment_list,
            pattern="" if len(patterns) == 0 else patterns[0],
            process_name_flag=False,
        )
        prop_dict[str(name)] = p

    return prop_dict


def convert_ttl_to_kg_rep(ttl_path):
    g = Graph()
    g.parse(ttl_path)
    class_dict = get_class_reps_from_graph(g)
    prop_dict = get_prop_reps_from_graph(g)
    return compute_metrics(class_dict, prop_dict)


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        "--ttl_path",
        type=str,
        help="Path to a .ttl ontology, or other RDFLib-supported ontology file",
    )
    parser.add_argument(
        "-o",
        "--output_path",
        default="metrics_out.json",
        type=str,
        help="Path for the output json file containing metrics ",
    )
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = get_args()
    metrics = convert_ttl_to_kg_rep(args.ttl_path)
    print("\nMetrics:\n", metrics)
    with open(args.output_path, "w") as f:
        json.dump(metrics, f, default=int)
