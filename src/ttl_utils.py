import regex as re 
from .kg_rep import *
from .str_utils import *
from .open_ont_config import *
import numpy as np

prefix_lines = \
"""# baseURI: <https://w3id.org/osdu#>
# imports: http://topbraid.org/schema/schema-single-range
# imports: http://www.w3.org/2004/02/skos/core
# imports: http://www.w3.org/2002/07/owl#
# imports: http://www.w3.org/1999/02/22-rdf-syntax-ns#
# imports: http://www.w3.org/XML/1998/namespace
# imports: http://www.w3.org/2001/XMLSchema#
# imports: https://w3id.org/osdu#
# imports: http://www.w3.org/2000/01/rdf-schema#
# imports: http://www.w3.org/2004/02/skos/core#
# imports: http://www.w3.org/2006/time#
# imports: http://xmlns.com/foaf/0.1/
# imports: http://www.w3.org/ns/auth/acl
# imports: https://www.geonames.org/ontology/ontology_v3.3.rdf
# prefix: osdu


@prefix : <https://w3id.org/osdu#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix dc: <http://purl.org/dc/elements/1.1/> .
@prefix xml: <http://www.w3.org/XML/1998/namespace> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix osdu: <https://w3id.org/osdu#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix skos:<http://www.w3.org/2004/02/skos/core#> .
@prefix time:<http://www.w3.org/2006/time#> .
@prefix foaf:<http://xmlns.com/foaf/0.1/> .
@prefix acl:<http://www.w3.org/ns/auth/acl> .
@prefix gn:<https://www.geonames.org/ontology/ontology_v3.3.rdf> .
@base <https://w3id.org/osdu#> .

"""

annotation_lines = \
"""
#################################################################
#    Annotation properties
#################################################################

###  http://purl.org/dc/elements/1.1/creator
dc:creator rdf:type owl:AnnotationProperty .


###  http://purl.org/dc/elements/1.1/title
dc:title rdf:type owl:AnnotationProperty .


###  http://www.w3.org/2001/XMLSchema#pattern
xsd:pattern rdf:type owl:AnnotationProperty .


###  http://www.w3.org/2002/07/owl#minCardinality
owl:minCardinality rdf:type owl:AnnotationProperty .


<https://w3id.org/osdu#> rdf:type owl:Ontology ;
                          <http://purl.org/dc/elements/1.1/creator> "Neda Abolhassani, Ph.D."^^xsd:string ;
                          <http://purl.org/dc/elements/1.1/creator> "Ana Tudor, M.S."^^xsd:string ;
                          <http://purl.org/dc/elements/1.1/title> "OSDU Ontology"^^xsd:string ;
                          owl:imports rdf: ;
                          owl:imports rdfs: ;
                          owl:imports xsd: ;
                          owl:imports owl: ;
                          owl:imports skos: ;
                          owl:imports time: ;
                          owl:imports <http://www.w3.org/XML/1998/namespace> ;
                          owl:imports <http://www.w3.org/ns/auth/acl> ;
                          owl:imports <http://xmlns.com/foaf/0.1/> ;
                          owl:imports foaf: ;
                          owl:imports <https://www.geonames.org/ontology/ontology_v3.3.rdf> ;
                          owl:versionInfo "Version 1.0" ;
.
"""

objectprops_header = \
"""
#################################################################
#    Object Properties
#################################################################
"""

dataprops_header = \
"""
#################################################################
#    Data properties
#################################################################
"""

classes_header = \
"""
#################################################################
#    Classes
#################################################################
"""

def add_prefix(name:str) -> str:
    return "osdu:"+ name

def assemble_ttl(class_ontology_dict:dict, prop_ontology_dict:dict, 
    url_to_classname_dict:dict, array_properties_dict:dict,
    dest_filepath:str, write_file:bool=True) -> None:
    """Use linked graph of ClassRep and PropertyRep objects, 
    as well as dictionary linking filename URLs to class names, 
    to assemble the OWL-based TTL file

    Args:
        class_ontology_dict (dict): Dictionary mapping OSDU class names to ClassRep objects.
        prop_ontology_dict (dict): Dictionary mapping explored OSDU property names to PropertyRep objects.
        url_to_classname_dict (dict): Dictionary mapping explored filename keys to OSDU class names.
        dest_filepath (str): String specifying the filepath to which the ttl file should be output.
    """
    #Add System and ACL classes
    class_ontology_dict, prop_ontology_dict = process_subclasses(class_ontology_dict, prop_ontology_dict)
    class_ontology_dict, prop_ontology_dict = create_ACL(class_ontology_dict, prop_ontology_dict)
    class_ontology_dict, prop_ontology_dict = create_org_classes(class_ontology_dict, prop_ontology_dict)
    class_ontology_dict, prop_ontology_dict = create_System(class_ontology_dict, prop_ontology_dict)
    class_ontology_dict, prop_ontology_dict = remove_links_to_grandparents(class_ontology_dict, prop_ontology_dict)


    #Link open ontologies
    class_ontology_dict, prop_ontology_dict = link_to_open_onts(class_ontology_dict, prop_ontology_dict)

    # Prefixes and base URI for file
    lines = [prefix_lines, annotation_lines, classes_header]

    #Add classes
    classkeys_list = list(class_ontology_dict.keys())
    classnames = [class_ontology_dict[cname].name for cname in classkeys_list]
    class_sort_idxs = np.argsort(classnames)

    for idx in class_sort_idxs:
        class_name = classkeys_list[idx]
        class_rep = class_ontology_dict[class_name]
        lines.append("###  https://w3id.org/osdu#" + class_rep.name)
        lines.append( add_prefix(class_rep.name) +  " rdf:type owl:Class ;")

        if class_rep.pref_label != '':
            lines.append("\tskos:prefLabel \"" + class_rep.pref_label + "\" ;")

        if len(class_rep.comments) > 0:
            for comment in class_rep.comments:
                lines.append( "\trdfs:comment \"" + comment + " \" ;")
        if len(class_rep.superclass_list) > 0:
            for superclass in class_rep.superclass_list:
                lines.append( "\trdfs:subClassOf " + reference_class(superclass, class_ontology_dict) + " ;" )
                
        if class_name in array_properties_dict:
            for rest_prop in array_properties_dict[class_name]:
                """ 
                [ a owl:Restriction ;
                owl:onProperty :works_on;
                owl:maxQualifiedCardinality "3"^^xsd:nonNegativeInteger ;
                owl:onClass :Project
              ] .
                """
                lines.append("\trdfs:subClassOf [\n\t\ta owl:Restriction ;")
                lines.append("\t\towl:onProperty " + add_prefix(rest_prop["prop_name"]) + " ;")
                if "on_class" in rest_prop:
                    lines.append("\t\towl:minQualifiedCardinality \"{}\"^^xsd:nonNegativeInteger ;".format(rest_prop["min_card"]))
                    lines.append("\t\towl:onClass " + reference_class(rest_prop["on_class"], class_ontology_dict) + " ;")
                else:
                    lines.append("\t\towl:minCardinality \"{}\"^^xsd:nonNegativeInteger ;".format(rest_prop["min_card"]))
                lines.append("\t] ;")

        if class_rep.sameas != []:
            for link in class_rep.sameas:
                lines.append("\towl:sameAs " + link + " ;")

        lines.append(".\n")

    # Add properties
    propkeys_list = list(prop_ontology_dict.keys())

    datapropkeys_list = [propkey for propkey in propkeys_list if (prop_ontology_dict[propkey].type == PropType.Datatype) ]
    dataprop_names = [prop_ontology_dict[propkey].name for propkey in datapropkeys_list]
    dataprop_sort_idxs = np.argsort(dataprop_names)

    dataprop_dict = {
        'idxs':dataprop_sort_idxs,
        'keys_list':datapropkeys_list,
        'header':dataprops_header
    }

    objectpropkeys_list = [propkey for propkey in propkeys_list if (prop_ontology_dict[propkey].type == PropType.Object) ]
    objectprop_names = [prop_ontology_dict[propkey].name for propkey in objectpropkeys_list]
    objectprop_sort_idxs = np.argsort(objectprop_names)

    objectprop_dict = {
        'idxs':objectprop_sort_idxs,
        'keys_list':objectpropkeys_list,
        'header':objectprops_header
    }

    propdicts = [objectprop_dict, dataprop_dict]

    for propdict in propdicts:
        propkeys_list = propdict['keys_list']
        prop_sort_idxs = propdict['idxs']
        lines.append(propdict['header'])
        for idx in prop_sort_idxs:
            prop_name = propkeys_list[idx]
            prop_rep = prop_ontology_dict[prop_name]
        
            #Check if property name already taken by a class name
            # if upper_split_camelcase(prop_rep.name) in class_ontology_dict:
            #     prop_rep.name = prop_rep.name + 'Property'

            lines.append("###  https://w3id.org/osdu#" + prop_rep.name)
            lines.append( add_prefix(prop_rep.name) + " rdf:type " + prop_rep.type.value + " ;")

            # Add comments
            for comment in prop_rep.comments:
                lines.append( "\trdfs:comment \"" + comment + " \" ;")
            
            # Add domain
            if len(prop_rep.domain) > 1:
                lines.append("\trdfs:domain [")
                lines.append("\t\trdf:type owl:Class ;")
                lines.append("\t\towl:unionOf (")

                for domain in prop_rep.domain:
                    lines.append("\t\t\tosdu:" + domain)
                lines.append("\t\t) ;")
                lines.append("\t] ;")
            elif len(prop_rep.domain) > 0:
                for domain in prop_rep.domain:
                    lines.append("\trdfs:domain " + add_prefix(domain) + " ;")
            # Add patterns for range
            for pattern in prop_rep.patterns:
                lines.append("\trdfs:pattern \"" + pattern + "\" ;")
            
            # Add range
            if len(prop_rep.range) > 1:
                lines.append("\t rdfs:range [")
                lines.append("\t\trdf:type owl:Class ;")
                lines.append("\t\towl:unionOf (")

                for range_name in prop_rep.range:
                    lines.append("\t\t\t"+reference_class(range_name, class_ontology_dict))
                lines.append("\t\t) ;")
                lines.append("\t] ;")
            elif len(prop_rep.range) == 1:
                if prop_rep.range[0] == "":
                        print("Issue!", prop_rep.name, prop_rep.domain)
                lines.append("\t"+generate_range_ttl_line(prop_rep.range[0], class_ontology_dict))

            # Add sameAs link
            if prop_rep.sameas != []:
                for link in prop_rep.sameas:
                    lines.append("\towl:sameAs " + link + " ;")
            
            lines.append(".\n")


    if write_file:
        with open(dest_filepath+"osdu_draft.ttl", "w+") as f:
            for line in lines:
                f.write(f"{line}\n")


def create_System(class_ontology_dict, prop_ontology_dict,):
    replace_key = "AbstractSystemProperties"
    new_key = "System"

    class_ontology_dict, prop_ontology_dict = replace_class(replace_key, new_key, class_ontology_dict, prop_ontology_dict)

    return class_ontology_dict, prop_ontology_dict

def remove_links_to_grandparents(class_ontology_dict, prop_ontology_dict):
    for potential_grandparent_key in class_ontology_dict.keys():
        for class_name, class_rep in class_ontology_dict.items():
            if potential_grandparent_key in class_rep.superclass_list:
                for superclass_key in class_rep.superclass_list:
                    if (superclass_key in class_ontology_dict) and \
                            (potential_grandparent_key in class_ontology_dict[superclass_key].superclass_list) :
                        class_rep.superclass_list.remove(potential_grandparent_key)
                        continue


    return class_ontology_dict, prop_ontology_dict


def create_ACL(class_ontology_dict, prop_ontology_dict,):
    replace_key = "AbstractAccessControlList"
    new_key = "ACL"

    return replace_class(replace_key, new_key, class_ontology_dict, prop_ontology_dict)

def replace_class(replace_key, new_key, class_ontology_dict, prop_ontology_dict):
    # Everywhere the old key is mentioned, rename it to the new key
    class_ontology_dict[new_key] = class_ontology_dict.pop(replace_key)
    class_ontology_dict[new_key].name = new_key

    for classname, class_rep in class_ontology_dict.items():
        if replace_key in class_rep.superclass_list:
            class_rep.superclass_list.remove(replace_key)
            class_rep.add_superclass(new_key)
    
    if ('has' + replace_key) in prop_ontology_dict:
        prop_ontology_dict['has' + new_key] = prop_ontology_dict.pop('has' + replace_key)

    for prop_name, prop_rep in prop_ontology_dict.items():
        if replace_key in prop_rep.domain:
            prop_rep.domain.append(new_key)
            prop_rep.domain.remove(replace_key)
        if replace_key in prop_rep.range:
            prop_rep.range.append(new_key)
            prop_rep.range.remove(replace_key)

    # Add old class with sameAs property pointing to new class
    class_ontology_dict = \
        add_class_from_parameters(replace_key, class_ontology_dict[new_key].superclass_list.copy(), class_ontology_dict)

    return class_ontology_dict, prop_ontology_dict

def create_org_classes(class_ontology_dict, prop_ontology_dict,):
    # Create MasterData class
    class_ontology_dict = \
        add_class_from_parameters("MasterData", ['System'], class_ontology_dict)
    # Create ReferenceData class
    class_ontology_dict = \
        add_class_from_parameters("ReferenceData", ['System'], class_ontology_dict)
    # Create WorkProductComponent class
    class_ontology_dict = \
        add_class_from_parameters("WorkProductComponent", ['System'], class_ontology_dict)
    # Create Dataset class
    class_ontology_dict = \
        add_class_from_parameters("Dataset", ['System'], class_ontology_dict)
    # Create Array class
    class_ontology_dict = \
        add_class_from_parameters("Array", ['owl:Thing'], class_ontology_dict)
    prop_ontology_dict = \
        add_property_from_parameters("items", domain_name="Array", range_name='number', \
            ontology_dict=prop_ontology_dict)

    return class_ontology_dict, prop_ontology_dict

def link_to_open_onts(class_ontology_dict, prop_ontology_dict):
    open_ont_dict = config_open_onts()

    # Go through each ontology key, insert them into the appropriate class or property dictionary
    for ont_key, ont_links_dict in open_ont_dict.items():
        ranges_dict = ont_links_dict["ranges_dict"]
        for ont_class_name, prop_list in ranges_dict.items():
            for prop in prop_list:
                prop_ontology_dict[prop].change_range(ont_key + ":" + ont_class_name)

        subclass_dict = ont_links_dict["subclass_dict"]
        for ont_class_name, class_list in subclass_dict.items():
            for class_name in class_list:
                class_ontology_dict[class_name].add_superclass(ont_key + ":" + ont_class_name, process_name_flag=False)
            
        sameas_dict = ont_links_dict["sameas_dict"]
        for ont_identifier, identifier_list in sameas_dict.items():
            for identifier in identifier_list:
                if identifier in class_ontology_dict:
                    class_ontology_dict[identifier].add_sameas_link(ont_key + ":" + ont_identifier)
                if identifier in prop_ontology_dict:
                    prop_ontology_dict[identifier].add_sameas_link(ont_key + ":" + ont_identifier)
                    
    return class_ontology_dict, prop_ontology_dict

def process_subclasses(class_ontology_dict, prop_ontology_dict):
    for classname, class_rep in class_ontology_dict.items():
        if class_rep.subclass_list != []:
            for subclass_name in class_rep.subclass_list:
                class_ontology_dict[subclass_name].add_superclass(classname)

    return class_ontology_dict, prop_ontology_dict

def generate_range_ttl_line(range_name,class_ontology_dict):
    if range_name in literals_dict:
        return ("rdfs:range " + literals_dict[range_name] + " ;")
    elif has_prefix(range_name):
        return ("rdfs:range " + range_name + " ;")
    elif range_name in class_ontology_dict:
        return ("rdfs:range " + add_prefix(range_name) + " ;")
    else:
        return ""

def reference_class(class_name, class_ontology_dict):
    if class_name in literals_dict:
        return literals_dict[class_name] 
    elif has_prefix(class_name):
        return class_name
    elif class_name in class_ontology_dict:
        return add_prefix(class_name)
    else:
        return ""
