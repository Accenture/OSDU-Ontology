import os
import json
import re


def load_schemas(schema_path: str) -> dict:
    """_summary_
    Borrows from 2-scripts/load_manifest_scripts/src/loading_manifest/csv_to_json.py in
        https://community.opengroup.org/osdu/platform/data-flow/data-loading/open-test-data/-/blob/master/rc--3.0.0/2-scripts/

    Args:
        schema_path (str): filepath to schema dictionary
    """

    def list_schema_files(path, file_list):
        files = os.listdir(path)
        for file in files:
            full_path = os.path.join(path, file)
            if os.path.isfile(full_path):
                if file.endswith(".json"):
                    file_list.append(full_path)
            elif os.path.isdir(full_path):
                list_schema_files(full_path, file_list)

    dict_schemas = {}

    # Load all json files
    file_list = []
    list_schema_files(schema_path, file_list)

    for schema_file in file_list:
        with open(schema_file, "r", encoding="utf-8") as fp:
            a_schema = json.load(fp)

            file_id = a_schema.get("$id")
            if file_id is None:
                file_id = a_schema.get("$ID")
            if file_id is not None:
                dict_schemas[file_id] = a_schema

    # Resolve latest version
    dict_latest_key = {}
    dict_latest_version = {}

    for key, val in dict_schemas.items():
        # Strip the version at the end
        key_parts = key.split("/")
        key_version = None
        if len(key_parts) > 1:
            key_version = int(
                "".join(re.search("(\d)\.(\d)\.(\d)", key_parts[-1]).groups())
            )

        if key_version is not None:
            key_latest_id = (
                re.search("(.+)\.\d\.\d\.\d\.json", key).groups()[0] + ".json"
            )
            previous_key_version = dict_latest_version.get(key_latest_id, None)
            if previous_key_version is None or key_version > previous_key_version:
                dict_latest_version[key_latest_id] = key_version
                dict_latest_key[key_latest_id] = key

    new_dict_schemas = {}

    for latest_key, key in dict_latest_key.items():
        new_dict_schemas[key] = dict_schemas[key]

    return new_dict_schemas
