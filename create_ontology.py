import argparse
import os
from src.json_utils import *
from src.ttl_utils import assemble_ttl
from src.kg_rep import *
from src.str_utils import *
from src.metrics_calc import *
import numpy as np
from pathlib import Path

# Define globals
""" 
CLASS_ONTOLOGY_DICT (dict): Dictionary mapping explored OSDU class names to ClassRep objects.
PROP_ONTOLOGY_DICT (dict): Dictionary mapping explored OSDU property names to PropertyRep objects.
URL_TO_CLASSNAME_DICT (dict): Dictionary mapping explored filename keys to OSDU class names.
"""
CLASS_ONTOLOGY_DICT = {}
PROP_ONTOLOGY_DICT = {}
URL_TO_CLASSNAME_DICT = {}
ARRAY_PROPERTIES_DICT = {}


def __main__():
    curr_path = os.path.dirname(os.path.abspath(__file__))

    parser = argparse.ArgumentParser(
        description="Specify schema directory and mode",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-s",
        "--src",
        help="Source location for schema files",
        default="osdu-ontology-generator/osdu_full_schema/",
    )
    parser.add_argument(
        "-d",
        "--dest",
        required=False,
        default=curr_path + "/",
        help="Destination location for output ttl",
    )
    parser.add_argument(
        "-o",
        "--ontology-name",
        required=False,
        default="osdu",
        help="Key descriptor for ontology name",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        required=False,
        action="store_true",
        default=True,
        help="increase verbosity",
    )
    parser.add_argument(
        "-m", "--report_metrics", required=False, default=False, action="store_true"
    )

    args = parser.parse_args()

    # Load dictionary of schemas via local storage, with updated versions
    schema_dict = load_schemas(args.src)

    # Dictionary to contain classes and predicates
    global CLASS_ONTOLOGY_DICT, PROP_ONTOLOGY_DICT, URL_TO_CLASSNAME_DICT, ARRAY_PROPERTIES_DICT
    CLASS_ONTOLOGY_DICT = {}
    PROP_ONTOLOGY_DICT = {}

    # Dictionaries for backwards definition of hierarchy
    URL_TO_CLASSNAME_DICT = {}

    # For each schema file, create and populate a class and its properties
    for key, schema in schema_dict.items():
        if "AbstractPersistableReference" in key:
            continue

        add_class_from_schema_dict(key, schema, args.verbose)

    # Add System class requirements
    add_array_property_restriction("System", "kind", min_card=1)
    add_array_property_restriction("System", "acl", min_card=1)
    add_array_property_restriction("System", "legal", min_card=1)

    # Assemble ttl file using ontology dictionary
    assemble_ttl(
        CLASS_ONTOLOGY_DICT,
        PROP_ONTOLOGY_DICT,
        URL_TO_CLASSNAME_DICT,
        ARRAY_PROPERTIES_DICT,
        dest_filepath=args.dest,
        write_file=(not args.report_metrics),
    )

    # Report metrics if desired
    if args.report_metrics:
        metrics_dict = compute_metrics(CLASS_ONTOLOGY_DICT, PROP_ONTOLOGY_DICT)
        for key, metric in metrics_dict.items():
            print(key + ":", metric)


def add_class_from_schema_dict(key: str, schema: dict, verbose: bool = False):
    """Explores a JSON dictionary-represented file in the full set of JSON schemas, to
        create representations the class described by the file, and related properties and classes.
        Populates dictionaries of classes and properties based on exploration.

    Args:
        key (str): Filename of schema in JSON schema dictionary.
        schema (dict): JSON schema dictionary, as returned by json_utils.load_schemas.
        verbose (bool, optional): Whether to report detailed errors. Defaults to False.

    """
    global CLASS_ONTOLOGY_DICT, PROP_ONTOLOGY_DICT, URL_TO_CLASSNAME_DICT, ARRAY_PROPERTIES_DICT

    # Define name of class, extracted from the filename
    class_name = re.search("([A-z]+)\.\d\.\d\.\d\.json", key)
    class_name = key if class_name is None else class_name

    class_name = class_name.groups()[0] if type(class_name) != str else class_name
    title = schema["title"] if "title" in schema else class_name

    # if "FeatureCollection" in class_name:
    #     print("happened")
    # Create link in url to classname dict, for backwards collection of hierarchy
    URL_TO_CLASSNAME_DICT[key] = class_name

    superclasses = []
    subclasses = []
    comments = []

    # Add inheritance of one of MasterData, ReferenceData, WorkProductComponent, or Dataset
    if re.search("/manifest/", key) is not None:
        # Do not add classes in the manifest folder
        return
    elif re.search("/reference-data/", key) is not None:
        superclasses.append("ReferenceData")
    elif re.search("/work-product-component/", key) is not None:
        superclasses.append("WorkProductComponent")
    elif re.search("/master-data/", key) is not None:
        superclasses.append("MasterData")
    elif re.search("/dataset/", key) is not None:
        superclasses.append("Dataset")
    else:
        superclasses.append("owl:Thing")

    # Add comment if existing in file
    if "description" in schema:
        comments.append(schema["description"])

    # Add AbstractSystemProperties as superclass if the right metadata properties are in the schema
    if (
        ("properties" in schema)
        and ("id" in schema["properties"])
        and ("kind" in schema["properties"])
        and ("legal" in schema["properties"])
        and ("meta" in schema["properties"])
        and ("version" in schema["properties"])
        and ("tags" in schema["properties"])
        and (class_name != "AbstractSystemProperties")
    ):
        superclasses.append("AbstractSystemProperties")

    properties_list = []
    # Add property / edge, method depending on different types of schema structure
    if ("properties" in schema) and ("data" in schema["properties"]):

        properties_list = schema["properties"]["data"]["allOf"]

        for property_dict in properties_list:
            if "$ref" in property_dict:
                # "$ref" tag treated as pointing to superclasses to be inherited
                superclasses.append(property_dict["$ref"])

            if "properties" in property_dict:
                subprop_dicts = property_dict["properties"]
                for subprop, subprop_dict in subprop_dicts.items():
                    add_property_from_schema_dict(subprop, subprop_dict, class_name)

    elif "properties" in schema:
        properties_dict = schema["properties"]
        for subprop, subprop_dict in properties_dict.items():
            add_property_from_schema_dict(subprop, subprop_dict, class_name)

    elif "allOf" in schema:
        properties_list = schema["allOf"]

        for property_dict in properties_list:
            # "$ref" tag treated as pointing to superclasses to be inherited
            if "$ref" in property_dict:
                superclasses.append(property_dict["$ref"])
            else:
                add_class_from_schema_dict(
                    process_name(property_dict["title"]), property_dict
                )
                superclasses.append(process_name(property_dict["title"]))

    elif "oneOf" in schema:
        properties_list = schema["oneOf"]

        for property_dict in properties_list:
            if "$ref" in property_dict:
                # Class with oneOf tag should be the superclass for the $ref objects
                subclasses.append(property_dict["$ref"])
            elif "title" in property_dict:
                # Parse through sub-dictionary to create a new class
                add_class_from_schema_dict(property_dict["title"], property_dict)

                subclasses.append(process_name(property_dict["title"]))
    else:
        if verbose:
            print("No properties data: ", key)

    # Find which properties may be required
    if "required" in schema:
        for prop in schema["required"]:
            if (lower_process_name(prop) not in ["kind", "legal", "acl"]) or (
                "AbstractSystemProperties" not in superclasses
            ):
                add_array_property_restriction(
                    class_name, lower_process_name(prop), min_card=1
                )

    # Find superclasses based on "x-osdu-inheriting-from-kind" tag
    if "x-osdu-inheriting-from-kind" in schema:
        for superclass_dict in schema["x-osdu-inheriting-from-kind"]:
            superclasses.append(extract_classname_from_kind(superclass_dict["kind"]))

    CLASS_ONTOLOGY_DICT = add_class_from_parameters(
        class_name,
        superclasses,
        CLASS_ONTOLOGY_DICT,
        comments,
        pref_label=title,
        subclass_list=subclasses,
    )

    return


def add_property_from_schema_dict(
    property_name: str, property_dict: dict, class_name: str, verbose: bool = False
) -> (dict, dict, dict):
    """Explores a property dictionary in a JSON schema file, to
        identify properties corresponding to a higher-level class.
        Populates dictionaries of classes and properties based on exploration.

    Args:
        property_name (str): Extracted OSDU name for the property
        property_dict (dict): Dictionary representing a property in the JSON schema file
        class_name (str): Extracted OSDU name for the higher-level class
        class_ontology_dict (dict): Dictionary mapping explored OSDU class names to ClassRep objects.
        prop_ontology_dict (dict): Dictionary mapping explored OSDU property names to PropertyRep objects.
        url_to_classname_dict (dict): Dictionary mapping explored filename keys to OSDU class names.
        verbose (bool, optional): Whether to report detailed errors. Defaults to False.

    Returns:
        class_ontology_dict: Updated dictionary mapping OSDU class names to ClassRep objects.
        prop_ontology_dict: Updated dictionary mapping explored OSDU property names to PropertyRep objects
        url_to_classname_dict: Updated dictionary mapping explored filename keys to OSDU class names.
    """
    global CLASS_ONTOLOGY_DICT, PROP_ONTOLOGY_DICT, URL_TO_CLASSNAME_DICT, ARRAY_PROPERTIES_DICT

    if "oneOf" in property_dict:
        for option_dict in property_dict["oneOf"]:
            if "type" in option_dict:
                range_name = "object"
                prop_type = PropType.Object
                if len(list(option_dict.keys())) == 1:
                    if option_dict["type"] != "null":
                        range_name = option_dict["type"]
                        prop_type = (
                            PropType.Object
                            if option_dict["type"] == "object"
                            else PropType.Datatype
                        )
                elif "title" in option_dict:
                    add_class_from_schema_dict(
                        process_name(option_dict["title"]), option_dict
                    )

                    range_name = process_name(option_dict["title"])

                PROP_ONTOLOGY_DICT = add_property_from_parameters(
                    domain_name=class_name,
                    property_name=property_name,
                    range_name=range_name,
                    ontology_dict=PROP_ONTOLOGY_DICT,
                    property_type=prop_type,
                    replace_range=False,
                )
            else:
                print("No type key in oneOf instance:", option_dict)

    elif (
        ("x-osdu-relationship" in property_dict)
        and (property_name[-2:] == "ID")
        and (property_dict["x-osdu-relationship"] != [])
        and ("EntityType" in property_dict["x-osdu-relationship"][0])
    ):
        # If the current class as the ID of a certain class associated with it,
        # create a new property "hasClass", with the new class name derived from subprop name minus the ID,
        # with domain current class, and range as class described in x-osdu-relationship.
        # Additional property of the ID itself also gets associated with the current class.
        # Pattern gets added to this ID property.
        try:
            PROP_ONTOLOGY_DICT = add_property_from_parameters(
                property_name="has"
                + upper_split_camelcase(
                    property_dict["x-osdu-relationship"][0]["EntityType"]
                ),
                domain_name=class_name,
                range_name=property_dict["x-osdu-relationship"][0]["EntityType"],
                ontology_dict=PROP_ONTOLOGY_DICT,
                property_type=PropType.Object,
            )
        except Exception:
            if verbose:
                print("\nMissing entity type:", property_name, class_name)

        CLASS_ONTOLOGY_DICT = add_class_from_parameters(
            class_name=property_dict["x-osdu-relationship"][0]["EntityType"],
            superclass_list=["owl:Thing"],
            ontology_dict=CLASS_ONTOLOGY_DICT,
            comments=[],
        )

        # Also create a DatatypeProperty with the ID as a string, to keep a record of the ID
        PROP_ONTOLOGY_DICT = add_property_from_parameters(
            property_name,
            domain_name=class_name,
            range_name="string",
            ontology_dict=PROP_ONTOLOGY_DICT,
            comment=(
                property_dict["description"] if "description" in property_dict else ""
            ),
            pattern=property_dict["pattern"] if "pattern" in property_dict else "",
        )

    elif "$ref" in property_dict:
        PROP_ONTOLOGY_DICT = add_property_from_parameters(
            property_name="has" + upper_split_camelcase(property_name),
            domain_name=class_name,
            range_name=property_dict["$ref"],
            ontology_dict=PROP_ONTOLOGY_DICT,
            property_type=PropType.Object,
        )

    elif "properties" in property_dict:
        # Create new property hasClass
        # with domain current class
        # and range as class described by subprop
        PROP_ONTOLOGY_DICT = add_property_from_parameters(
            property_name="has"
            + upper_split_camelcase(re.sub("\ ", "", property_name)),
            domain_name=class_name,
            range_name=property_name,
            ontology_dict=PROP_ONTOLOGY_DICT,
            property_type=PropType.Object,
        )

        # Call recursive class creation on subprop_dict
        add_class_from_schema_dict(re.sub("\ ", "", property_name), property_dict)
    else:
        # Create new Datatype property
        range_name = ""
        pattern = property_dict["pattern"] if "pattern" in property_dict else ""

        # If property can contain an array of information, create a property to represent instances in the array
        # Class instances in the knowledge graph can simply specify multiple
        if ("type" in property_dict) and (
            (property_dict["type"] == "array") or ("items" in property_dict)
        ):
            if "minItems" in property_dict:
                if property_dict["items"]["type"] == "object":
                    add_array_property_restriction(
                        class_name,
                        property_name,
                        min_card=property_dict["minItems"],
                        on_class=property_dict["items"]["title"],
                    )
                elif property_dict["items"]["type"] != "array":
                    add_array_property_restriction(
                        class_name,
                        property_name,
                        min_card=property_dict["minItems"],
                        on_class=property_dict["items"]["type"],
                    )
                else:
                    # The current property is an array, that contains multiple arrays
                    # Therefore, current property should point to an Array class
                    # Then pass the items dictionary

                    # Create a prefix+Array class for this property to point to
                    new_class_name = (
                        class_name + upper_split_camelcase(property_name) + "Array"
                    )
                    CLASS_ONTOLOGY_DICT = add_class_from_parameters(
                        class_name=new_class_name,
                        superclass_list=["Array"],
                        ontology_dict=CLASS_ONTOLOGY_DICT,
                    )

                    # Create the property pointing to this array
                    PROP_ONTOLOGY_DICT = add_property_from_parameters(
                        property_name=property_name,
                        domain_name=class_name,
                        range_name=new_class_name,
                        ontology_dict=PROP_ONTOLOGY_DICT,
                        replace_range=False,
                    )

                    # Handle the cardinality
                    add_array_property_restriction(
                        class_name,
                        property_name,
                        min_card=property_dict["minItems"],
                        on_class=new_class_name,
                    )

                    # Call property creation again with prefix+Array class as the domain
                    add_property_from_schema_dict(
                        property_name="items",
                        property_dict=property_dict["items"],
                        class_name=new_class_name,
                    )

                    return

            if "$ref" in property_dict["items"]:
                PROP_ONTOLOGY_DICT = add_property_from_parameters(
                    property_name=property_name,
                    domain_name=class_name,
                    range_name=property_dict["items"]["$ref"],
                    ontology_dict=PROP_ONTOLOGY_DICT,
                    property_type=PropType.Object,
                )
                return
            elif "properties" in property_dict["items"]:
                new_class_name = (
                    property_dict["items"]["title"]
                    if "title" in property_dict["items"]
                    else property_name
                )
                new_class_name = upper_split_camelcase(strip_whitespace(new_class_name))

                PROP_ONTOLOGY_DICT = add_property_from_parameters(
                    property_name="has"
                    + upper_split_camelcase(strip_whitespace(property_name)),
                    domain_name=class_name,
                    range_name=new_class_name,
                    ontology_dict=PROP_ONTOLOGY_DICT,
                    property_type=PropType.Object,
                )

                # Call recursive class creation on subprop_dict
                add_class_from_schema_dict(new_class_name, property_dict["items"])
                return

            elif "allOf" in property_dict["items"]:
                # Create the property, have the item it has be an object, and
                # Make sure the object inherits all the classes described in the allOf list
                new_class_name = (
                    property_dict["items"]["title"]
                    if "title" in property_dict["items"]
                    else property_name
                )
                new_class_name = process_name(new_class_name)
                superclasses = []
                for superclass_dict in property_dict["items"]["allOf"]:
                    if "$ref" in superclass_dict:
                        # "$ref" tag treated as pointing to superclasses to be inherited
                        superclasses.append(superclass_dict["$ref"])
                    else:
                        add_class_from_schema_dict(
                            process_name(superclass_dict["title"]), superclass_dict
                        )
                        superclasses.append(process_name(superclass_dict["title"]))
                CLASS_ONTOLOGY_DICT = add_class_from_parameters(
                    new_class_name, superclasses, CLASS_ONTOLOGY_DICT
                )
                PROP_ONTOLOGY_DICT = add_property_from_parameters(
                    property_name="has" + upper_split_camelcase(property_name),
                    domain_name=class_name,
                    range_name=new_class_name,
                    ontology_dict=PROP_ONTOLOGY_DICT,
                )
                return

            elif "oneOf" in property_dict["items"]:
                # Create a property specific to this class
                #  to make sure subclasses from other versions of this property
                #  don't get presented as an option
                # Construct all classes in this list, and have them inherit the class of this property's domains
                new_class_name = (
                    property_dict["items"]["title"]
                    if "title" in property_dict["items"]
                    else property_name
                )
                new_class_name = process_name(new_class_name)
                CLASS_ONTOLOGY_DICT = add_class_from_parameters(
                    new_class_name, ["owl:Thing"], CLASS_ONTOLOGY_DICT
                )
                PROP_ONTOLOGY_DICT = add_property_from_parameters(
                    property_name, class_name, new_class_name, PROP_ONTOLOGY_DICT
                )
                for new_class_dict in property_dict["items"]["oneOf"]:
                    if "$ref" in new_class_dict:
                        # "$ref" tag treated as pointing to superclasses to be inherited
                        if process_name(new_class_dict["$ref"]) in CLASS_ONTOLOGY_DICT:
                            CLASS_ONTOLOGY_DICT[
                                process_name(new_class_dict["$ref"])
                            ].add_superclass(new_class_name)
                        else:
                            CLASS_ONTOLOGY_DICT = add_class_from_parameters(
                                process_name(new_class_dict["$ref"]),
                                [new_class_name],
                                CLASS_ONTOLOGY_DICT,
                            )
                    #    superclasses.append( superclass_dict["$ref"])
                    else:
                        add_class_from_schema_dict(
                            process_name(new_class_dict["title"]), new_class_dict
                        )
                        CLASS_ONTOLOGY_DICT[
                            process_name(new_class_dict["title"])
                        ].add_superclass(new_class_name)

                return
            elif property_dict["items"]["type"] == "array":
                # Create a prefix+Array class for this property to point to
                new_class_name = (
                    class_name + upper_split_camelcase(property_name) + "Array"
                )
                CLASS_ONTOLOGY_DICT = add_class_from_parameters(
                    class_name=new_class_name,
                    superclass_list=["Array"],
                    ontology_dict=CLASS_ONTOLOGY_DICT,
                )

                # Create the property pointing to this array
                PROP_ONTOLOGY_DICT = add_property_from_parameters(
                    property_name=property_name,
                    domain_name=class_name,
                    range_name=new_class_name,
                    ontology_dict=PROP_ONTOLOGY_DICT,
                    replace_range=False,
                )
                # Call property creation again with prefix+Array class as the domain
                add_property_from_schema_dict(
                    property_name="items",
                    property_dict=property_dict["items"],
                    class_name=new_class_name,
                )

                return

            else:
                range_name = property_dict["items"]["type"]
                pattern = (
                    property_dict["items"]["pattern"]
                    if "pattern" in property_dict["items"]
                    else ""
                )
        elif "type" in property_dict:
            range_name = property_dict["type"]

        PROP_ONTOLOGY_DICT = add_property_from_parameters(
            property_name=property_name,
            domain_name=class_name,
            range_name=range_name,
            ontology_dict=PROP_ONTOLOGY_DICT,
            property_type=PropType.Datatype,
            comment=(
                property_dict["description"] if "description" in property_dict else ""
            ),
            pattern=pattern,
        )


def add_array_property_restriction(
    class_name: str, property_name: str, on_class: str = "", min_card: int = 1
):
    global ARRAY_PROPERTIES_DICT
    array_prop = {"prop_name": process_prop_name(property_name), "min_card": min_card}
    if on_class != "":
        array_prop["on_class"] = process_range(on_class)
    if class_name not in ARRAY_PROPERTIES_DICT:
        ARRAY_PROPERTIES_DICT[class_name] = [array_prop]
    else:
        ARRAY_PROPERTIES_DICT[class_name].append(array_prop)


if __name__ == "__main__":
    __main__()
