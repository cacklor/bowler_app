import pandas as pd

exp = pd.read_csv('/Users/jamesbrooker/bowler_app/expected_percentages.csv')

def maindataframe():
    df2 = pd.read_csv('Champo 2024 Full.csv')
    df1 = df2[(~df2['PitchX'].isna())& (~df2['ReleaseY'].isna())]
    df = df1[(df1['Speed'] > 0) & (df1['ReleaseX'] > 0)]
    df['Time'] = df['ReleaseX'] / df['Speed']
    average_release = df['ReleaseX'].mean()
    df['adjusted_speed'] = round(average_release/df['Time'], 2)
    bowlers = df['Bowler'].unique().tolist()
    
    average_adjusted_velocity = []
    ninety_adj_speed = []
    ten_adj_speed = []
    average_release_height = []
    average_adjusted_percentile_difference = []
    for i in bowlers:
        bowler_balls = df[df['Bowler'] == i]
        mean_adj_speed = bowler_balls['adjusted_speed'].mean()
        bowler_balls = bowler_balls[bowler_balls['adjusted_speed'] <= 100]
        average_adjusted_velocity.append(round(mean_adj_speed,2))
        threshold = bowler_balls['adjusted_speed'].quantile(0.9)
        threshold1 = bowler_balls['adjusted_speed'].quantile(0.1)
        filtered_df = bowler_balls[bowler_balls['adjusted_speed'] >= threshold]
        filtered_df1 = bowler_balls[bowler_balls['adjusted_speed'] <= threshold1]
        avr_n = filtered_df['adjusted_speed'].mean()
        avr_ten = filtered_df1['adjusted_speed'].mean()
        ninety_adj_speed.append(round(avr_n,2))
        ten_adj_speed.append(round(avr_ten,2))
        mean_release_point = bowler_balls['ReleaseZ'].mean()
        average_release_height.append(round(mean_release_point,3))
        
    for i, j in zip(ninety_adj_speed, ten_adj_speed):
        average_adjusted_percentile_difference.append(round(i-j,2))
        
    middle_percentage = []
    whiff_percentage = []
    edge_percentage = []
    for i in bowlers:
        bowler_balls = df1[df1['Bowler'] == i]
        bowler_balls1 = bowler_balls[~bowler_balls['Shot'].isin(['Padded Away', 'No Shot'])]
        swings = 0
        middles = 0
        whiffs = 0
        edges = 0
        for index, row in bowler_balls1.iterrows():
            swings += 1
            if row['Connection'] == 'Middled':
                middles += 1
            elif row['Connection'] in ['Thick Edge', 'Inside Edge', 'Outside Edge','Leading Edge']:
                edges += 1
            elif row['Connection'] == 'Missed':
                whiffs += 1
            else:
                continue
        middle_percentage.append(round(middles/swings, 3))
        whiff_percentage.append(round(whiffs/swings, 3))   
        edge_percentage.append(round(edges/swings, 3))
    
    runs_per_edge = []

    for i in bowlers:
        bowler_balls = df1[df1['Bowler'] == i]
        edged_balls = bowler_balls[bowler_balls['Connection'].isin(['Thick Edge', 'Inside Edge', 'Outside Edge', 'Leading Edge'])]
        if edged_balls.empty:
            runs_per_edge.append(round(0,2))
        else:
            runs_per_edge.append(round(edged_balls['Runs'].mean(), 2))
        
    #edge_dataframe = df1[df1['Connection'].isin(['Thick Edge', 'Inside Edge', 'Outside Edge', 'Leading Edge'])]
    #print(round(edge_dataframe['Runs'].mean(),2))
            
    data1 = {'Bowler':bowlers,'Average Adjusted Velocity': average_adjusted_velocity,
             '90th Percentile Adjusted Velocity':ninety_adj_speed,
             'Adjusted Velocity Variation': average_adjusted_percentile_difference,
             'Average Release Height':average_release_height,
             'Middle Percentage': middle_percentage,
             'Whiff Percentage': whiff_percentage,
             'Edge Percentage': edge_percentage,
             'Runs per Edge': runs_per_edge}
    data = pd.DataFrame(data1)

    

    pace_data = data[data['Average Adjusted Velocity'] >= 70]
    spin_data = data[data['Average Adjusted Velocity'] < 70]

    for index, row in data.iterrows():
        bowler_data = exp[exp['Bowlers'] == row['Bowler']]
        if not bowler_data.empty:  # Check if matching data exists
            data.at[index, 'Expected Middle Percentage'] = round(bowler_data['Expected Middle Percentage'].iloc[0], 4)
            data.at[index, 'Expected Whiff Percentage'] = round(bowler_data['Expected Whiff Percentage'].iloc[0], 4)
            data.at[index, 'Expected Edge Percentage'] = round(bowler_data['Expected Edge Percentage'].iloc[0], 4)

    
    expected_data = data.drop(columns=['Middle Percentage', 'Whiff Percentage', 'Edge Percentage'])
    new_order = ['Bowler', 'Average Adjusted Velocity', '90th Percentile Adjusted Velocity',
                                             'Adjusted Velocity Variation', 'Average Release Height', 'Expected Middle Percentage',
                                             'Expected Whiff Percentage', 'Expected Edge Percentage', 'Runs per Edge']
    expected_data_rearranged = expected_data[new_order]
    
    exp_pace_data = expected_data_rearranged[expected_data_rearranged['Average Adjusted Velocity'] >= 70]
    exp_spin_data = expected_data_rearranged[expected_data_rearranged['Average Adjusted Velocity'] < 70]
    
  
    def percentile_rank(column):
        return column.rank(pct=True) * 100
    
    pace_percentile_df = pace_data.copy()
    pace_percentile_df.iloc[:, 1:] = pace_data.iloc[:, 1:].apply(percentile_rank)
    pace_percentile_df = pace_percentile_df.round(2)

    pace_percentile_df['Middle Percentage'] = 100 - pace_percentile_df['Middle Percentage']
    pace_percentile_df['Runs per Edge'] = 100 - pace_percentile_df['Runs per Edge']
    
    spin_percentile_df = spin_data.copy()
    spin_percentile_df.iloc[:, 1:] = spin_data.iloc[:, 1:].apply(percentile_rank)
    spin_percentile_df = spin_percentile_df.round(2)

    spin_percentile_df['Middle Percentage'] = 100 - spin_percentile_df['Middle Percentage']
    spin_percentile_df['Runs per Edge'] = 100 - spin_percentile_df['Runs per Edge']
    
    pace_data.to_csv('/Users/jamesbrooker/bowler_app/pacedata.csv',index=False)
    pace_percentile_df.to_csv('/Users/jamesbrooker/bowler_app/pacepercentileranks.csv',index=False)
    
    spin_data.to_csv('/Users/jamesbrooker/bowler_app/spindata.csv',index=False)
    spin_percentile_df.to_csv('/Users/jamesbrooker/bowler_app/spinpercentileranks.csv',index=False)

    exp_pace_percentile_df = exp_pace_data.copy()
    exp_pace_percentile_df.iloc[:, 1:] = exp_pace_data.iloc[:, 1:].apply(percentile_rank)
    exp_pace_percentile_df = exp_pace_percentile_df.round(2)

    exp_pace_percentile_df['Expected Middle Percentage'] = 100 - exp_pace_percentile_df['Expected Middle Percentage']
    exp_pace_percentile_df['Runs per Edge'] = 100 - exp_pace_percentile_df['Runs per Edge']
    
    exp_spin_percentile_df = exp_spin_data.copy()
    exp_spin_percentile_df.iloc[:, 1:] = exp_spin_data.iloc[:, 1:].apply(percentile_rank)
    exp_spin_percentile_df = exp_spin_percentile_df.round(2)

    exp_spin_percentile_df['Expected Middle Percentage'] = 100 - exp_spin_percentile_df['Expected Middle Percentage']
    exp_spin_percentile_df['Runs per Edge'] = 100 - exp_spin_percentile_df['Runs per Edge']
    
    exp_pace_data.to_csv('/Users/jamesbrooker/bowler_app/exppacedata.csv',index=False)
    exp_pace_percentile_df.to_csv('/Users/jamesbrooker/bowler_app/exppacepercentileranks.csv',index=False)
    
    exp_spin_data.to_csv('/Users/jamesbrooker/bowler_app/expspindata.csv',index=False)
    exp_spin_percentile_df.to_csv('/Users/jamesbrooker/bowler_app/expspinpercentileranks.csv',index=False)
    
    heatmaps_df = df[['Bowler','Runs', 'PitchX', 'PitchY']]
    release_df = df[['Bowler','Runs', 'ReleaseY','ReleaseZ', 'Bowler Type']]
    
    heatmaps_df.to_csv('heatmaps.csv',index=False)
    release_df.to_csv('release.csv',index=False)
    
    all_maps = df1[['Bowler','Runs','Batting Hand', 'Bowler Type', 'ReleaseY','ReleaseZ' , 'PitchX', 'PitchY', 'PastY', 'PastZ']]
    all_maps.to_csv('/Users/jamesbrooker/Old Data/allmaps.csv', index=False)
    
    return data, heatmaps_df, release_df, all_maps


print(maindataframe())