def raise_h2_budget_data_to_h1(data):
    """
    Data is the complete dataset of activities

    Check if data is h1, if so, check if it has related-activities
    """
    for activity in data:
        if 'hierarchy' in activity and activity['hierarchy'] == 1 and 'related-activity' in activity:
            if type(activity['related-activity']) is dict:
                activity['related-activity'] = [activity['related-activity']]
            data_present, related_data = pull_related_data_to_h1(data, activity)
            if data_present:
                for r in related_data:
                    activity[r] = related_data[r]
    return data


def pull_related_id_title_description(id_title_description, activity):
    if id_title_description != "":
        id_title_description += " \n "

    _id = activity.get('iati-identifier', '')
    _title = activity.get('title', {}).get('narrative', [])
    if isinstance(_title, list):
        _title = ". ".join(_title)
    # Get the descriptions, can be 1..* with 1..* narratives
    _descriptions = activity.get('description', [])
    if not isinstance(_descriptions, list):
        _descriptions = [_descriptions]
    _description = []
    for _desc in _descriptions:
        _desc = _desc.get('narrative', [])
        if isinstance(_desc, list):
            _desc = ". ".join(_desc)
        _description.append(_desc)
    _description = ". ".join(_description)

    id_title_description += f"ID: {_id}\nTitle: {_title}\nDescription: {_description}\n"
    return id_title_description


def pull_related_data_to_h1(data, activity):
    """
    we want to collect the following data:
    budget.period-end.quarter,
    budget.period-start.quarter
    budget_period_start_iso_date
    budget_period_end_iso_date
    budget_value

    data: has all the activities in a dataset
    activity: the activity for which we are pulling data
    """
    related_data = False
    related_budget_value = []
    related_budget_period_start_quarter = []
    related_budget_period_end_quarter = []
    related_budget_period_start_iso_date = []
    related_budget_period_end_iso_date = []
    id_title_description = pull_related_id_title_description("", activity)

    related_activity_refs = [rel['ref'] for rel in activity.get('related-activity', []) if 'ref' in rel]
    for _activity in data:
        if 'iati-identifier' in _activity and _activity['iati-identifier'] in related_activity_refs:
            related_data = True
            if 'budget' in _activity:
                if type(_activity['budget']) is dict:
                    _activity['budget'] = [_activity['budget']]

                for budget in _activity['budget']:
                    related_budget_value.append(budget['value'])
                    # use hardcoded [0] as there is always one period-start and one period-end
                    related_budget_period_start_iso_date.append(budget['period-start'][0]['iso-date'])
                    related_budget_period_end_iso_date.append(budget['period-end'][0]['iso-date'])

                related_budget_period_start_quarter.extend(_activity.get('budget.period-start.quarter', []))
                related_budget_period_end_quarter.extend(_activity.get('budget.period-end.quarter', []))
            id_title_description = pull_related_id_title_description(id_title_description, _activity)

    return related_data, {
        'related_budget_value': related_budget_value,
        'related_budget_period_start_quarter': related_budget_period_start_quarter,
        'related_budget_period_end_quarter': related_budget_period_end_quarter,
        'related_budget_period_start_iso_date': related_budget_period_start_iso_date,
        'related_budget_period_end_iso_date': related_budget_period_end_iso_date,
        'related_activity_context': id_title_description,
    }
