"""Resource utility functions."""
from datetime import datetime

import pytz
import tzlocal

from resdk.constants import RESOLWE_DATETIME_FORMAT


def iterate_fields(fields, schema):
    """Recursively iterate over all DictField sub-fields.

    :param fields: Field instance (e.g. input)
    :type fields: dict
    :param schema: Schema instance (e.g. input_schema)
    :type schema: dict

    """
    schema_dict = {val["name"]: val for val in schema}
    for field_id, properties in fields.items():
        if "group" in schema_dict[field_id]:
            for _field_sch, _fields in iterate_fields(
                properties, schema_dict[field_id]["group"]
            ):
                yield (_field_sch, _fields)
        else:
            yield (schema_dict[field_id], fields)


def iterate_schema(fields, schema, path=None):
    """Recursively iterate over all schema sub-fields.

    :param fields: Field instance (e.g. input)
    :type fields: dict
    :param schema: Schema instance (e.g. input_schema)
    :type schema: dict
    :path schema: Field path
    :path schema: string

    """
    for field_schema in schema:
        name = field_schema["name"]
        if "group" in field_schema:
            for rvals in iterate_schema(
                fields[name] if name in fields else {},
                field_schema["group"],
                None if path is None else "{}.{}".format(path, name),
            ):
                yield rvals
        else:
            if path is None:
                yield (field_schema, fields)
            else:
                yield (field_schema, fields, "{}.{}".format(path, name))


def flatten_field(field, schema, path):
    """Reduce dicts of dicts to dot separated keys.

    :param field: Field instance (e.g. input)
    :type field: dict
    :param schema: Schema instance (e.g. input_schema)
    :type schema: dict
    :param path: Field path
    :type path: string
    :return: flattened instance
    :rtype: dictionary

    """
    flat = {}
    for field_schema, fields, current_path in iterate_schema(field, schema, path):
        name = field_schema["name"]
        typ = field_schema["type"]
        label = field_schema["label"]
        value = fields.get(name, None)
        flat[current_path] = {"name": name, "type": typ, "label": label, "value": value}

    return flat


def fill_spaces(word, desired_length):
    """Fill spaces at the end until word reaches desired length."""
    return str(word) + " " * (desired_length - len(word))


def _print_input_line(element_list, level):
    """Pretty print of input_schema."""
    spacing = 2

    for element in element_list:
        if "group" in element:
            print(
                "{}- {} - {}".format("    " * level, element["name"], element["label"])
            )
            _print_input_line(element["group"], level + 1)
        else:
            max_name_len = max([len(elm["name"]) for elm in element_list])
            max_type_len = max(
                [
                    len(elm["type"]) or 0
                    for elm in [e for e in element_list if "group" not in e]
                ]
            )
            print(
                "{}- {} {} - {}".format(
                    "    " * level,
                    fill_spaces(element["name"], max_name_len + spacing),
                    fill_spaces("[" + element["type"] + "]", max_type_len + spacing),
                    element["label"],
                )
            )


def get_collection_id(collection):
    """Return id attribute of the object if it is collection, otherwise return given value."""
    return collection.id if type(collection).__name__ == "Collection" else collection


def get_data_id(data):
    """Return id attribute of the object if it is data, otherwise return given value."""
    return data.id if type(data).__name__ == "Data" else data


def get_descriptor_schema_id(dschema):
    """Get descriptor schema id.

    Return id attribute of the object if it is descriptor schema,
    otherwise return given value.

    """
    return dschema.id if type(dschema).__name__ == "DescriptorSchema" else dschema


def get_process_id(process):
    """Return id attribute of the object if it is process, otherwise return given value."""
    return process.id if type(process).__name__ == "Process" else process


def get_sample_id(sample):
    """Return id attribute of the object if it is sample, otherwise return given value."""
    return sample.id if type(sample).__name__ == "Sample" else sample


def get_relation_id(relation):
    """Return id attribute of the object if it is relation, otherwise return given value."""
    return relation.id if type(relation).__name__ == "Relation" else relation


def get_user_id(user):
    """Return id attribute of the object if it is relation, otherwise return given value."""
    return user.id if type(user).__name__ == "User" else user


def is_collection(collection):
    """Return ``True`` if passed object is Collection and ``False`` otherwise."""
    return type(collection).__name__ == "Collection"


def is_data(data):
    """Return ``True`` if passed object is Data and ``False`` otherwise."""
    return type(data).__name__ == "Data"


def is_descriptor_schema(data):
    """Return ``True`` if passed object is DescriptorSchema and ``False`` otherwise."""
    return type(data).__name__ == "DescriptorSchema"


def is_process(process):
    """Return ``True`` if passed object is Process and ``False`` otherwise."""
    return type(process).__name__ == "Process"


def is_sample(sample):
    """Return ``True`` if passed object is Sample and ``False`` otherwise."""
    return type(sample).__name__ == "Sample"


def is_relation(relation):
    """Return ``True`` if passed object is Relation and ``False`` otherwise."""
    return type(relation).__name__ == "Relation"


def is_user(user):
    """Return ``True`` if passed object is User and ``False`` otherwise."""
    return type(user).__name__ == "User"


def is_group(group):
    """Return ``True`` if passed object is Group and ``False`` otherwise."""
    return type(group).__name__ == "Group"


def parse_resolwe_datetime(dtime):
    """Convert string representation of time to local datetime.datetime object."""
    if dtime:
        # Get naive (=time-zone unaware) version of UTC time:
        utc_naive = datetime.strptime(dtime[:-6], RESOLWE_DATETIME_FORMAT)
        # Localize the time so it includes UTC timezone info:
        utc_aware = pytz.utc.localize(utc_naive)
        # Get name local time zone:
        local_tz = tzlocal.get_localzone()
        # Present time in the local time zone
        local_time = utc_aware.astimezone(local_tz)

        return local_time
