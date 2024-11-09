import pandas as pd
import statsmodels.api as sm
import numpy as np

df = pd.read_csv('Champo 2024 Full.csv')

releasey_std = df['ReleaseY'].std()
releasez_std = df['ReleaseZ'].std()
pitchx_std = df['PitchX'].std()
pitchy_std = df['PitchY'].std()
speed_std = df['Speed'].std()

bowlers = df['Bowler'].unique().tolist()

def stat_calculations(bowler):
    bowler_balls = df[df['Bowler'] == bowler]
    middle_percentage = []
    whiff_percentage = []
    edge_percentage = []

    for index, row in bowler_balls.iterrows():
        releasey = row['ReleaseY']
        releasez = row['ReleaseZ']
        pitchx = row['PitchX']
        pitchy = row['PitchY']
        speed = row['Speed']

        similar_balls1 = df[(df['ReleaseY'] < releasey + releasey_std) & (df['ReleaseY'] > releasey - releasey_std)
                           & (df['ReleaseZ'] < releasez + releasez_std) & (df['ReleaseZ'] > releasez - releasez_std)
                           & (df['PitchX'] < pitchx + pitchx_std) & (df['PitchX'] > pitchx - pitchx_std)
                           & (df['PitchY'] < pitchy + pitchy_std) & (df['PitchY'] > pitchy - pitchy_std)
                            & (df['Speed'] < speed + speed_std) & (df['Speed'] > speed - speed)]
        
        similar_balls = similar_balls1[~similar_balls1['Shot'].isin(['Padded Away', 'No Shot'])]

        swings = 0
        middles = 0
        whiffs = 0
        edges = 0
        for index, row in similar_balls.iterrows():
            swings += 1
            if row['Connection'] == 'Middled':
                middles += 1
            elif row['Connection'] in ['Thick Edge', 'Inside Edge', 'Outside Edge','Leading Edge']:
                edges += 1
            elif row['Connection'] == 'Missed':
                whiffs += 1
            else:
                continue
        if swings == 0:
            middle_percentage.append(0)
            whiff_percentage.append(0)
            edge_percentage.append(0)
        else:
            middle_percentage.append(round(middles/swings, 3))
            whiff_percentage.append(round(whiffs/swings, 3))   
            edge_percentage.append(round(edges/swings, 3))
    
    xmiddle_percentage = np.mean(middle_percentage)
    xwhiff_percentage = np.mean(whiff_percentage)
    xedge_percentage = np.mean(edge_percentage)

    return xmiddle_percentage, xwhiff_percentage, xedge_percentage

xmp = []
xwp = []
xep = []

for i in bowlers:
    xmiddle_percentage, xwhiff_percentage, xedge_percentage = stat_calculations(i)
    print(xedge_percentage)
    xmp.append(xmiddle_percentage)
    xwp.append(xwhiff_percentage)
    xep.append(xedge_percentage)

data = {'Bowlers': bowlers, 'Expected Middle Percentage': xmp, 'Expected Whiff Percentage': xwp, 'Expected Edge Percentage': xep}

final_df = pd.DataFrame(data)
final_df.to_csv('expected_percentages_half_sd.csv')
