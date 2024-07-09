import pandas as pd


def get_callable_df_with_columns(columns):
    def _callable(**kwargs):
        data = kwargs[list(kwargs.keys())[0]]
        df = pd.DataFrame(data)
        df.columns = columns
        return df

    return _callable


def MODE_SELECTOR_CALL(mode):
    return mode


def EXTRACT_GOAL_DETAILS_CALL(goal_type, goal_description, goal_milestones, goal_progress, goal_target_date):
    return {"goal_type": goal_type, "goal_description": goal_description, "goal_milestones": goal_milestones, "goal_progress": goal_progress, "goal_target_date": goal_target_date}


def APPOINTMENT_OR_PURCHASE_SERVICE_CALL(event_type, event_description, event_contact, event_date, event_time):
    return {"event_type": event_type, "event_description": event_description, "event_contact": event_contact, "event_date": event_date, "event_time": event_time}

