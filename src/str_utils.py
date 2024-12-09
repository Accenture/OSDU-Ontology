import regex as re
from nltk.tokenize import word_tokenize


def strip_whitespace(name: str) -> str:
    """Remove any instance of whitespace from a string
    Args:
        name (str): String to be stripped of whitespace. This string should be the name of a class or property.
    Returns:
        str: Whitespace-stripped string.
    """
    return re.sub("\s", "", name)


def remove_punctuation(name: str) -> str:
    return re.sub("\.", "", name)


def process_name(name: str) -> str:
    """Removes asterisks and periods from a string, to be formatted as a name for a class or property.
    Args:
        name (str): String to be processed.
    Returns:
        str: Processed string.
    """
    name = re.sub(r"\.", "", re.sub(r"\*", "", strip_whitespace(name)))
    return upper_split_camelcase(name)


def process_prop_name(name: str) -> str:
    name = re.sub(r"\.", "", re.sub(r"\*", "", strip_whitespace(name)))
    return lower_split_camelcase(name)


def process_comment(comment: str) -> str:
    """Removes slashes, quotes, and newline characters from a string, to be formatted as a comment.
    Args:
        comment (str): String to be processed.
    Returns:
        str: Processed string.
    """
    return re.sub("\n", " ", re.sub('"', "", re.sub(r"\\", "", comment)))


def process_comments(comments: list) -> list:
    """Removes slashes, quotes, and newline characters from a list of strings, all to be formatted as comments.
    Args:
        comments (list): Strings to be processed.
    Returns:
        list: Processed strings.
    """
    new_comments = (
        [process_comment(comment) for comment in comments.copy()]
        if comments != [""]
        else []
    )
    return new_comments


def process_pattern(pattern: str) -> str:
    """Introduces a correct pattern of slashes to a string representing a regex pattern.
    Args:
        pattern (str): String to be processed.
    Returns:
        str: Processed string.
    """
    return re.sub(r"\\", r"\\\\\\\\", pattern)


def process_new_patterns(pattern: str) -> list:
    """Introduces a correct pattern of slashes to a list of strings representing regex patterns.
    Args:
        patterns (list): Strings to be processed.
    Returns:
        list: Processed strings.
    """
    new_patterns = [process_pattern(pattern)] if pattern != "" else []
    return new_patterns


def lower_process_name(property_name: str) -> str:
    """_summary_
    Args:
        prop_name (str): _description_
    Returns:
        str: _description_
    """
    return str.lower(process_name(property_name))


def split_camelcase(name: str) -> list:
    """_summary_
    Args:
        name (str): _description_
    Returns:
        str: _description_
    """
    return re.findall(
        "(?:[A-Z](?:[a-z]+|[A-Z]*(?=[A-Z]|$)))|[a-z]+|[A-Z]*(?=[A-Z]|$)", name
    )


def upper_split_camelcase(name: str) -> str:
    name_comps = split_camelcase(remove_punctuation(name))
    name_comps.remove("")

    if (len(name_comps) > 0) and (not name_comps[0][0].isupper()):
        name_comps[0] = name_comps[0][0].upper() + name_comps[0][1:]
    return "".join(name_comps)


def lower_split_camelcase(name: str) -> str:
    name_comps = split_camelcase(remove_punctuation(name))
    name_comps.remove("")

    if (len(name_comps) > 0) and (not name_comps[0][0].islower()):
        name_comps[0] = name_comps[0][0].lower() + name_comps[0][1:]
    return "".join(name_comps)


def extract_version(url: str) -> int:
    """Extract a 3-digit integer representing the version number of the schema file,
        from the filename
    Args:
        url (str): a filename or relative url, ending in format "filename.x1.x2.x3.json
    Returns:
        int: 3-digit integer representing a 3-digit version number, returned as x1*100 + x2*10 + x3
    """
    version_str = re.search("(.+)\.\d\.\d\.\d\.json", url)
    if version_str is not None:
        version_num = int("".join(re.search("(\d)\.(\d)\.(\d)\.json", url).groups()))
        return version_num
    else:
        return None


def extract_classname_from_kind(value: str) -> str:
    classname = "".join(re.search(":(\w+):\d\.\d\.\d", value).groups())
    return classname


def extract_classname_from_filename(value: str) -> str:
    class_name = re.search("([A-z]+)\.\d\.\d\.\d\.json", value)
    class_name = str(value) if class_name is None else "".join(class_name.groups())
    return class_name


def has_prefix(value: str) -> bool:
    """Returns true if the string input takes a form 'prefix:classOrProperty'
    Args:
        value (str): string input to be checked
    Returns:
        bool: true if the string input takes a form 'prefix:classOrProperty'
    """
    return re.search("([A-z]+):", value) is not None
