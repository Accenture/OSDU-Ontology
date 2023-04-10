import regex as re
from enum import Enum
from .str_utils import *

# Enumerating the OWL objects used in this ontology
class PropType(Enum):
    Class = 'owl:Class'
    Object = 'owl:ObjectProperty'
    Datatype = 'owl:DatatypeProperty'

# Dictionary to reference the literal types used in this ontology
literals_dict = {"string":"xsd:string",
                 "integer":"xsd:integer",
                 "number":"xsd:decimal",
                 "object":"owl:Thing",
                 "boolean":"xsd:boolean"}

def process_range(name:str) -> str:
    if name in literals_dict:
        return name
    else:
        return process_name(extract_classname_from_filename(name))

class PropertyRep:
    def __init__(self, name:str, domain_name_list:list, 
                range_name:str, comments:list=[], 
                prop_type:str=PropType.Datatype,
                pattern:str='', ):
        """Defines a representation of an OSDU property, 
            identified using the name field.
            Associates one or multiple domains with the property,
            and only one possible literal or Object range. 
            Type of property identified via the PropType enum, and
            a possible regex pattern can be associated with the property value. 

        Args:
            name (str): Name for the class within the OSDU ontology.
            domain_name_list (list): list of names describing OSDU classes 
                that may be described by this property
            range_name (str): name of OSDU class, or literal type, that this Property will take on 
            comments (list, optional): List of string comments to associate with this property. 
                Defaults to [].
            prop_type (str, optional): identify whether the Property is an Object, or Datatype. 
                Defaults to PropType.Datatype.
            pattern (str, optional): regex pattern associated with this property. Defaults to ''.
        """
        self.name = process_prop_name(name)
        self.domain = [process_name(domain_name) for domain_name in domain_name_list]
        self.range = [process_range(range_name)]
        self.comments = process_comments(comments)
        self.type = prop_type
        if (process_range(range_name) not in literals_dict) or \
            (process_range(range_name) == 'object'):
            self.type = PropType.Object
        else:
            self.type = PropType.Datatype
        self.patterns = process_new_patterns(pattern)
        self.sameas = []

    def add_domain(self, domain_name:str) -> None:
        """Process and add a domain if it is not already associated with the property.
        Args:
            domain_name (str): string identifier for an ODSU class domain
        """
        processed_domain = process_name(domain_name)
        if (domain_name != '') and (processed_domain not in self.domain):
            self.domain.append(processed_domain)


    def change_range(self, range_name:str) -> None:
        """Change the range for this property to a specified string
            WARNING: given string will not be formatted or checked. 
            Any class name in OSDU used as the range must be formatted externally

        Args:
            range_name (str): string identifying the new range of this property
        """
        if len(self.range) == 1:
            self.range = [range_name]
        elif range_name not in self.range:
            self.range.append(range_name)

    def add_comment(self, comment:str) -> None:
        """Process and add a comment if it is not already associated with the property.
        Args:
            comment (str): string description of the property
        """
        processed_comment = process_comment(comment)
        if (comment != '') and (processed_comment not in self.comments):
            self.comments.append(processed_comment)

    def add_sameas_link(self, identifier):
        self.sameas.append(identifier)

    def add_pattern(self, pattern:str) -> None:
        """Process and add a pattern if it is not already associated with the property.
        Args:
            pattern (str): regex pattern identifying the string format this property may take on
        """
        processed_pattern = process_pattern(pattern)
        if (pattern != '') and ( processed_pattern not in self.patterns):
            self.patterns.append(processed_pattern)

    def verify_match(self, range_name:str, prop_type:str, replace_range=True) -> None:
        """Identify whether potential range and property types
        are compatible with this property. If so, updates the range. 
        This includes updating literal range types to more specific versions,
        and removing version numbers from the range name.
        Intended property type must match the original exactly.

        Args:
            range_name (str): name of OSDU class, or literal type, that this Property may take on 
            prop_type (str): identify whether the Property is an Object, or Datatype. 
        """

        if self.type != prop_type:
            raise Exception('Incorrect property type '+ prop_type, ". Type should be "+ self.type )

        new_range_name = process_range(range_name)
        if new_range_name not in self.range:
            if new_range_name not in literals_dict:
                self.type = PropType.Object
            if replace_range and (len(self.range) == 1):
                self.range = [new_range_name]
            else:
                self.range.append(new_range_name)

    
class ClassRep:
    def __init__(self, name:str, superclass_list:list=[], 
                comments:list=[], pref_label:str='', subclass_list:list=[]):
        """Defines a representation of an OSDU class node, 
            identified using the name field, 
            and having a list of inherited superclass pointing to this class.
            Associates possible comments to the instance, and a possible alternate name for the class.

        Args:
            name (str): Name for the class within the OSDU ontology.
            superclass_list (list, optional): List of classes which this class should inherit. Defaults to [].
            comments (list, optional): Comments about the nature of this property. Defaults to [].
            pref_label (str, optional): Provides the option to specify an skos:prefLabel in the ontology
                 Defaults to '', does not generate the prefLabel given an empty string.
        """
        self.name = process_name(name) 

        # Option to specify an skos:prefLabel
        self.pref_label = pref_label if (pref_label != self.name) else ''
        
        # Storage of ontology inheritance hierarchy using list of pointers to other classes
        self.superclass_list = []
        self.add_superclasses(superclass_list)

        # Clean comments for compatibility with the TopBraid Ontology Composer
        self.comments = process_comments(comments)
        self.type = PropType.Class

        self.sameas = []

        self.subclass_list = []
        self.add_subclasses(subclass_list)

        self.array_props = []
    
    def add_comment(self, comment:str):
        """Process and add a comment if it is not already associated with the class
        Args:
            comment (str): string description associated with the class
        """
        processed_comment = process_comment(comment)
        if (comment != '') and (processed_comment not in self.comments):
            self.comments.append(processed_comment)
    
    def add_comments(self, comments:list):
        """Process and add a list of comments if they are not already associated with the class
        Args:
            comments (list): list of string descriptions of the class
        """
        if (comments != []):
            for comment in comments:
                self.add_comment(comment)
    
    def add_sameas_link(self, identifier):
        self.sameas.append(identifier)
    
    def add_superclass(self, superclass:str, process_name_flag=True) -> None:
        """Add a class which is inherited by the current one, if not already listed
        Args:
            superclass (str): string name referencing an OSDU class
        """
        if process_name_flag:
            processed_superclass = process_name(extract_classname_from_filename(superclass))
        else:
            processed_superclass = superclass

        if (processed_superclass in ['ReferenceData', 'MasterData', 'Dataset', 'WorkProductComponent', 'Abstract']) and \
            ('owl:Thing' in self.superclass_list) :
            self.superclass_list.remove('owl:Thing')
            self.superclass_list.append(processed_superclass)
        elif (superclass == 'owl:Thing') and \
            ('ReferenceData' not in self.superclass_list) and \
            ('MasterData' not in self.superclass_list) and \
            ('Dataset' not in self.superclass_list) and \
            ('WorkProductComponent' not in self.superclass_list) and \
            ('Abstract' not in self.superclass_list) and ('owl:Thing' not in self.superclass_list):
            self.superclass_list.append(superclass)
        elif ((superclass != '') and (processed_superclass not in self.superclass_list) and \
            (self.name != processed_superclass)) and (superclass != 'owl:Thing'):
            if 'owl:Thing' in self.superclass_list:
                self.superclass_list.remove('owl:Thing')
            self.superclass_list.append(processed_superclass)

    def add_superclasses(self, superclass_list:list):
        """Add a list of classes which are inherited by the current one, if not already listed
        Args:
            superclass_list (list): string names referencing OSDU classes
        """
        if superclass_list != []:
            for superclass in superclass_list:
                self.add_superclass(superclass)

    def add_subclass(self, subclass_name:str, process_name_flag=True) -> None:
        if process_name_flag:
            processed_subclass = process_name(extract_classname_from_filename(subclass_name))
        else:
            processed_subclass = subclass_name
        if processed_subclass not in self.subclass_list:
            self.subclass_list.append(processed_subclass)

    def add_subclasses(self, subclass_list:list):
        """Add a list of classes which inherit the current one, if not already listed
        Args:
            subclass_list (list): string names referencing OSDU classes
        """
        if subclass_list != []:
            for subclass in subclass_list:
                self.add_subclass(subclass)

    def add_array_property_restriction(self, property_name:str, on_class:str, min_card:int=1):
        array_prop = {"prop_name":process_prop_name(property_name), 
                    "min_card":min_card,
                    "on_class":process_name(on_class)}
        self.array_props.append(array_prop)

def add_property_from_parameters(property_name:str, 
                                domain_name:str,
                                range_name:str,
                                ontology_dict:dict, 
                                property_type:str=PropType.Datatype,
                                comment:str='',
                                pattern:str='', replace_range=True,
                                verbose:bool=False) -> dict:
    """If a property has not yet been encountered,
        creates a PropertyRep object based on externally-specified parameters.
        If a property has been encountered, updates the previously specified PropertyRep object.

    Args:
        property_name (str): Extracted name for a property within the OSDU ontology.
        domain_name (str): Name of a class which this property can describe.
        range_name (str): Name of a literal type or class which describes the data this property can take on.
        ontology_dict (dict): Dictionary mapping explored OSDU property names to PropertyRep objects.
        property_type (str, optional): Enum string for the type of property this should describe. 
                                        Defaults to PropType.Datatype.
        comment (str, optional): Extracted comment about the nature of this property. Defaults to ''.
        pattern (str, optional): Extracted regex pattern describing the format of this property. Defaults to ''.
        verbose (bool, optional): Whether to report detailed errors. Defaults to False.

    Returns:
        dict: Updated dictionary mapping explored OSDU property names to PropertyRep objects.
    """

    if process_prop_name(property_name) in ontology_dict:
        property_name = process_prop_name(property_name)
        try:
            ontology_dict[property_name].verify_match(range_name, property_type, replace_range)
            ontology_dict[property_name].add_domain(domain_name)
            ontology_dict[property_name].add_comment(comment)
            ontology_dict[property_name].add_pattern(pattern)
        except Exception as e:
            if verbose:
                print(e)
                print("\nTried to create property on top of a class:", property_name, domain_name)
    else:
        ontology_dict[process_prop_name(property_name)] = PropertyRep(property_name, 
                                        [domain_name], range_name,
                                        [comment], property_type, pattern)
    return ontology_dict


def add_class_from_parameters(class_name:str, superclass_list:list, 
                                ontology_dict:dict, comments:list=[],
                                pref_label:str='', subclass_list:list=[],
                                verbose=False) -> dict:
    """If a class has not yet been encountered,
        creates a ClassRep object based on externally-specified parameters.
        If a class has been encountered, updates the previously specified ClassRep object.

    Args:
        class_name (str): Extracted name for a class within the OSDU ontology.
        superclass_list (list): Extracted list of classes which this class should inherit.
        ontology_dict (dict): Dictionary mapping explored OSDU class names to ClassRep objects.
        comments (list, optional): Extracted comments about the nature of this property. Defaults to [].
        pref_label (str, optional): Extracted alternate name for the  Defaults to ''.

    Returns:
        dict: Updated dictionary mapping explored OSDU class names to ClassRep objects.
    """
    if process_name(class_name) in ontology_dict:
        try:
            ontology_dict[process_name(class_name)].add_superclasses(superclass_list)
            ontology_dict[process_name(class_name)].add_subclasses(subclass_list)
            ontology_dict[process_name(class_name)].add_comments(comments)
        except(Exception):
            if verbose:
                print("Error in adding superclass or comment to:", class_name)
    else:
        ontology_dict[process_name(class_name)] = ClassRep(class_name, 
                                        superclass_list,
                                        comments, pref_label=pref_label,
                                        subclass_list=subclass_list)
    return ontology_dict