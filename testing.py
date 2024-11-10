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
connection = df['Connection'].unique().tolist()
print(connection)

def stat_calculations(bowler):
    bowler_balls = df[df['Bowler'] == bowler]
    middle_percentage = []
    whiff_percentage = []
    edge_percentage = []
    balls = []

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
                            & (df['Bowler Type'] == row['Bowler Type']) & (df['Batting Hand'] == row['Batting Hand'])
                           & (df['Speed'] < speed + speed_std) & (df['Speed'] > speed - speed_std)
                           & (df['Match'] == row['Match']) & (df['Date'] == row['Date']) & (df['Innings'] == row['Innings'])]
        
        similar_balls = similar_balls1[~similar_balls1['Shot'].isin(['Padded Away', 'No Shot'])]



        swings = 0
        middles = 0
        whiffs = 0
        edges = 0

        for index, row in similar_balls.iterrows():
            swings += 1
            if row['Connection'] == 'Middled':
                middles += 1
            elif row['Connection'] in ['Thick Edge', 'Inside Edge', 'Outside Edge','Leading Edge', 'Top Edge', 'Bottom Edge']:
                edges += 1
            elif row['Connection'] == 'Missed':
                whiffs += 1
            else:
                continue
        if swings == 0:
            middle_percentage.append(0)
            whiff_percentage.append(0)
            edge_percentage.append(0)
            balls.append(similar_balls.shape[0])
        else:
            middle_percentage.append(round(middles/swings, 3))
            whiff_percentage.append(round(whiffs/swings, 3))   
            edge_percentage.append(round(edges/swings, 3))
            balls.append(similar_balls.shape[0])
    
    adjusted_edgepct = []
    totalballs = np.sum(balls)
    for i, j in zip(balls, edge_percentage):
        adj = (i/totalballs)*j
        adjusted_edgepct.append(adj)

    adjusted_middlepct = []
    totalballs = np.sum(balls)
    for i, j in zip(balls, middle_percentage):
        adj = (i/totalballs)*j
        adjusted_middlepct.append(adj)

    adjusted_whiffpct = []
    totalballs = np.sum(balls)
    for i, j in zip(balls, whiff_percentage):
        adj = (i/totalballs)*j
        adjusted_whiffpct.append(adj)

    xmiddle_percentage = np.sum(adjusted_middlepct)
    xwhiff_percentage = np.sum(adjusted_whiffpct)
    xedge_percentage = np.sum(adjusted_edgepct)

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
