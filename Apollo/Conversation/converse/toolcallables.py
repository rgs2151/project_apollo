import pandas as pd


def get_callable_df_with_columns(columns):
    def _callable(**kwargs):
        data = kwargs[list(kwargs.keys())[0]]
        df = pd.DataFrame(data)
        df.columns = columns
        return df

    return _callable


