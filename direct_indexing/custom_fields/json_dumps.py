import json
import logging

JSON_FIELDS = [
    "reporting-org",
    "title",
    "description",
    "participating-org",
    "other-identifier",
    "activity-date",
    "contact-info",
    "recipient-country",
    "recipient-region",
    "location",
    "sector",
    "tag",
    "country-budget-items",
    "humanitarian-scope",
    "policy-marker",
    "default-aid-type",
    "budget",
    "planned-disbursement",
    "transaction",
    "document-link",
    "related-activity",
    "legacy-data",
    "conditions",
    "result",
    "crs-add",
    "fss",
]


def add_json_dumps(data):
    for activity in data:
        for field in JSON_FIELDS:
            if field not in activity:
                continue
            activity[field] = _json_dump_transaction_fix(activity[field], field)
            if isinstance(activity[field], list):
                _json_dump_list(activity, field)
            else:
                try:
                    activity[f'json.{field}'] = json.dumps(activity[field])
                except Exception as e:
                    logging.error(f"Error serializing {field}: type: {type(e)} stack: {e}")


# JSON dump transaction fix, as the date is a list of one element, but the field is a string.
def _json_dump_transaction_fix(subfield, field):
    if field == 'transaction':
        for t in subfield:
            td = t['transaction-date']
            if isinstance(td, list):
                if len(td) > 1:
                    logging.error(f"Transaction date is a list with more than one element: {td}")
                t['transaction-date'] = td[0]
    return subfield


def _json_dump_list(activity, field):
    activity[f'json.{field}'] = []
    for item in activity[field]:
        try:
            activity[f'json.{field}'].append(json.dumps(item))
        except Exception as e:
            logging.error(f"Error serializing {field}: type: {type(e)} stack: {e}")
