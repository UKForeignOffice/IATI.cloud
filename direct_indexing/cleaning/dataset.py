from collections import OrderedDict

LANG_STR = 'lang'
XML_LANG_STR = '@{http://www.w3.org/XML/1998/namespace}' + LANG_STR
XML_LANG_STR_STRIPPED = XML_LANG_STR[1:]


def recursive_attribute_cleaning(data):
    """
    Recursively clean the attributes of the dataset.

    :param data: either a dict, list of ordered dicts or an ordered dict.
    :return: the cleaned dataset.
    """
    if type(data) in [OrderedDict, dict]:
        # Filter out any @ symbols in the keys. (@attribute to attribute)
        data = {key.replace('@', ''): item for key, item in data.items()}
        # Remove the lang xml tag
        data = {key.replace(XML_LANG_STR_STRIPPED, LANG_STR): item for key, item in data.items()}
        data = {key: item for key, item in data.items() if '._' not in key}
        data = {key: item for key, item in data.items() if 'http' not in key}

        # A list of fields that need to be appended to the dataset
        add_fields = {}
        for key, value in data.items():
            add_fields = extract_key_value_fields(data, add_fields, key, value)
        # Add the fields to be appended to the dataset
        for key in add_fields:
            data[key] = add_fields[key]
    # If a dataset is a list, it will contain multiple dicts, so loop over and
    # process the individual dicts.
    elif type(data) is list:
        for i in range(len(data)):
            data[i] = recursive_attribute_cleaning(data[i])
    return data


def extract_key_value_fields(data, add_fields, key, value):
    """
    These fields always contain a single value, but can be in a list

    :param data: the overarching data.
    :param add_fields: the additional fields to be appended to the dataset.
    :param key: the key of the key:value pair.
    :param value: the value of the key:value pair.
    """
    if key in [
        'iati-identifier', 'telephone', 'email', 'website', 'pos', 'channel-code', 'organisation-identifier'
    ]:
        extract_literal_values(value, key, data)
    elif key in ['value', 'forecast', 'narrative']:
        # A value is always single value,
        # but narrative and forecast can be multiple values.
        if type(value) is list:
            add_fields = extract_list_values(add_fields, value, key, data)

        else:  # if there is only a single entry
            add_fields = extract_single_values(add_fields, value, key, data)
    # If the fields are not yet at the lowest level of key-value pair,
    # process the underlying field.
    elif type(value) in [OrderedDict, dict, list]:  # was list instead of dict
        data[key] = recursive_attribute_cleaning(value)
    return add_fields


def extract_literal_values(value, key, data):
    """
    Supplied is a key:value pair, as well as the overarching data.
    Data is a reference, so that the value can be updated.

    Take the value out of var-name.$ = 42 and save it as var-name = 42.

    :param value: the value of the key:value pair.
    :param key: the key of the key:value pair.
    :param data: the overarching data.
    :return: None, as data is a reference
    """
    if type(value) is list:
        # initialize array and add each element to the array
        data[key] = []
        for element in value:
            if '$' in element:
                data[key].append(element['$'])
    else:
        # Retrieve the single value if the field is not a list
        if '$' in value:
            data[key] = value['$']


def extract_list_values(add_fields, value, key, data):
    """
    Extract all of the list items to the additional fields
    Data is a reference and thus the value can be updated.

    Take the values out of, for example:
        var-name.narrative.$ = ["This is a narrative", "This is another narrative"]
        var-name.narrative.@lang = ["en", "fr"]
    and save it as:
        var-name.narrative = ["This is a narrative", "This is another narrative"]
        var-name.narrative.lang = ["en", "fr"]

    :param add_fields: the additional fields to be appended to the dataset.
    :param value: the value of the key:value pair.
    :param key: the key of the key:value pair.
    :param data: the overarching data.
    :return: the additional fields to be appended to the dataset.
    """
    # initialize array and add each element to the array
    data[key] = []  # the actual value.
    for item in ['currency', 'value_date', 'year', 'lang']:
        add_fields[f'{key}.{item}'] = []
    for element in value:
        list_values(element, data, key, add_fields)

    return add_fields


def list_values(element, data, key, add_fields):
    """
    Extract all of the list items to the additional fields

    :param element: the element to be processed.
    :param data: the overarching data.
    :param key: the key of the key:value pair.
    :param add_fields: the additional fields to be appended to the dataset.
    """
    if len(element) == 0:  # Skip empty elements.
        return data, add_fields
    if '$' in element:
        data[key].append(element['$'])
    else:
        data[key].append(' ')
    for string in ['@currency', '@value-date', '@year']:
        if string in element:
            add_fields[f'{key}.{string[1:]}'].append(element[string])
    if XML_LANG_STR in element:
        add_fields[f'{key}.{LANG_STR}'].append(
            element[XML_LANG_STR])
    else:  # Avoid having an inconsistent length between narrative lang and value
        if key != 'value':
            add_fields[f'{key}.{LANG_STR}'].append(' ')
    return data, add_fields


def extract_single_values(add_fields, value, key, data):
    """
    Extract single values to the additional fields.
    Data is a reference and thus the value can be updated.

    Take the values out of, for example:
        var-name.value.value-date.$ = "This is a narrative"
        var-name.narrative.@lang = "en"
    and save it as:
        var-name.narrative = "This is a narrative"
        var-name.narrative.lang = "en"

    :param add_fields: the additional fields to be appended to the dataset.
    :param value: the value of the key:value pair.
    :param key: the key of the key:value pair.
    :param data: the overarching data.
    :return: the additional fields to be appended to the dataset.
    """
    if type(value) is list and len(value) == 0:
        # Skip empty elements.
        return add_fields
    if type(value) in [int, str, float]:  # if the value is directly available
        data[key] = value
        return add_fields
    if type(value) is bool:
        data[key] = 1 if value else 0
        return add_fields
    if '$' in value:
        data[key] = value['$']
    else:
        data[key] = ' '
    for string in ['@currency', '@value-date', '@year']:
        if string in value:
            add_fields[f'{key}.{string[1:]}'] = value[string]
    # The language can still be a child element which has not
    # yet been converted within recursion.
    if XML_LANG_STR in value:
        add_fields[f'{key}.{LANG_STR}'] = value[
            XML_LANG_STR]
    # assume the language is not provided
    else:
        if key != 'value':
            add_fields[f'{key}.{LANG_STR}'] = ' '

    return add_fields


def clean_known_issues(data):
    """Known issues:
    - recipient-org-budget.value = " "
    - transaction.value-gbp-type = [IF, 0]
    - transaction.value-usd-type = [IF, 0]
    - budget.period-start.iso-date: date string formatted as 'YYYY-MM-DD+HH:MM' instead of YYYY-MM-DDTHH:MM:SSZ
    - result.document-link.document-date.iso-date: date string formatted as 'YYYY-MM-DD+HH:MM' instead of YYYY-MM-DDTHH:MM:SSZ
    - activity-date.start-planned: date string formatted as 'YYYY-MM-DD+HH:MM' instead of YYYY-MM-DDTHH:MM:SSZ
    - activity-date.iso-date: date string formatted as 'YYYY-MM-DD+HH:MM' instead of YYYY-MM-DDTHH:MM:SSZ

    Args:
        data (dict): activity data
    """
    # Fix for recipient-org-budget.value = " "
    if 'recipient-org-budget.value' in data and data['recipient-org-budget.value'] == ' ':
        data['recipient-org-budget.value'] = 0
    # In case it is not one object
    if 'recipient-org-budget' in data and 'value' in data['recipient-org-budget'] and data['recipient-org-budget']['value'] == ' ':
        data['recipient-org-budget']['value'] = 0

    data = _clean_known_issues_types(data)

    # Fix for malformed date strings
    date_fields_to_fix = [
        'budget.period-start.iso-date',
        'result.document-link.document-date.iso-date',
        'activity-date.start-planned',
        'activity-date.iso-date',
    ]
    for field in date_fields_to_fix:
        if field in data:
            value = data[field]
            if isinstance(value, list):
                data[field] = [_reformat_date_str(d) for d in value]
            else:
                data[field] = _reformat_date_str(value)

    data = _clean_known_issues_dates(data)
    return data


def _clean_known_issues_types(data):
    # Fix for transaction.value-gbp-type and transaction.value-usd-type
    for field in ['transaction.value-gbp-type', 'transaction.value-usd-type']:
        if field in data and isinstance(data[field], list):
            # Per instructions, replace any values not in range(1, 14) with 1.
            # Valid transaction type codes are integers from 1 to 13.
            cleaned_list = []
            for item in data[field]:
                if not isinstance(item, int):
                    try:
                        item = int(item)
                    except Exception:
                        pass
                if isinstance(item, int) and 1 <= item <= 13:
                    cleaned_list.append(item)
                else:
                    cleaned_list.append(1)
            data[field] = cleaned_list
    return data


def _reformat_date_str(date_str):
    # Fix for date strings like 'YYYY-MM-DD+HH:MM' by replacing '+' with 'T'.
    # This converts it to a valid ISO 8601 format.
    # We check for 'T' not in string to avoid re-formatting strings that
    # already have a time designator and a timezone offset (e.g. '...T...+...').
    if isinstance(date_str, str) and '+' in date_str and 'T' not in date_str:
        return date_str.replace('+', 'T', 1)
    return date_str


def _clean_known_issues_dates(data):
    if 'budget' in data and 'period-start' in data['budget'] and 'iso-date' in data['budget']['period-start']:
        value = data['budget']['period-start']['iso-date']
        if isinstance(value, list):
            data['budget']['period-start']['iso-date'] = [_reformat_date_str(d) for d in value]
        else:
            data['budget']['period-start']['iso-date'] = _reformat_date_str(value)

    if 'result' in data and 'document-link' in data['result'] and 'document-date' in data['result']['document-link'] and 'iso-date' in data['result']['document-link']['document-date']:
        value = data['result']['document-link']['document-date']['iso-date']
        if isinstance(value, list):
            data['result']['document-link']['document-date']['iso-date'] = [_reformat_date_str(d) for d in value]
        else:
            data['result']['document-link']['document-date']['iso-date'] = _reformat_date_str(value)

    if 'activity-date' in data and 'iso-date' in data['activity-date']:
        value = data['activity-date']['iso-date']
        if isinstance(value, list):
            data['activity-date']['iso-date'] = [_reformat_date_str(d) for d in value]
        else:
            data['activity-date']['iso-date'] = _reformat_date_str(value)
    return data
