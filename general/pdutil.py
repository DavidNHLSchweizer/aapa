import pandas as pd

def nrows(df: pd.DataFrame)->int:
    return df.shape[0]

def ncols(df: pd.DataFrame)->int:
    return df.shape[1]