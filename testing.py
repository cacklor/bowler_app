import pandas as pd

df = pd.read_csv('/Users/jamesbrooker/Old Data/Champo 2024 Full.csv')

df1 = df[(df['Bowler'] == 'AAP Atkinson') & (~df['ReleaseX'].isna()) & (~df['Speed'].isna())]

print(df1.shape[0])