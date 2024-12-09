from src.metrics_calc import compute_metrics
from src.kg_rep import ClassRep, PropertyRep
from rdflib import Graph
import argparse
import json

class_query = """
SELECT DISTINCT ?a
WHERE {
    ?a a owl:Class .
}"""
class_superclass_query = """
SELECT DISTINCT ?b
WHERE {
    ?name rdfs:subClassOf ?b
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
        # print(f"{row.a}")
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
        # print(
        #     f"\nname: {name};\nsuperclasses: {superclass_list};\ncomments: {comment_list};\nlabel: {label}"
        # )
        c = ClassRep(
            name=name,
            superclass_list=superclass_list,
            comments=comment_list,
            pref_label=label,
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

        # print(row, type)
        domain_list = [
            row.b
            for row in g.query(
                prop_domain_query.format(proptype=type), initBindings={"name": name}
            )
        ]
        range_list = [
            row.b
            for row in g.query(
                prop_range_query.format(proptype=type), initBindings={"name": name}
            )
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
        # print(
        #     f"\nname: {name};\ndomain_name_list: {domain_list};\nsuperclass_list: {superclass_list};\nrange_name: {range_list}"
        # )
        p = PropertyRep(
            name=str(name),
            prop_type=type,
            domain_name_list=domain_list,
            range_name="" if len(range_list) == 0 else range_list[0],
            comments=comment_list,
            pattern="" if len(patterns) == 0 else patterns[0],
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
