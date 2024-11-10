import pandas as pd
import statsmodels.api as sm
from bs4 import BeautifulSoup
import requests

expected_stats = pd.read_csv('spindata.csv')
player_info = pd.read_csv('playerinformation.csv')

def scrape_espncricinfo_table(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find('table')
    
    rows = []
    for row in table.find_all('tr'):
        columns = row.find_all(['td', 'th'])
        row_data = []
        for column in columns:
            link = column.find('a', href=True)
            if link:
                row_data.append(f"https://www.cricinfo.com{link['href']}")
            else:
                row_data.append(column.text.strip())
        rows.append(row_data)
    
    headers = rows[0]
    data = rows[1:]
    df = pd.DataFrame(data, columns=headers)
    
    return df

current_player_stats = scrape_espncricinfo_table('https://www.espncricinfo.com/records/tournament/bowling-most-wickets-career/county-championship-division-one-2024-15937')

for index, row in current_player_stats.iterrows():
    player_link = row['Player']
    pinfo = player_info[player_info['Player Links'] == player_link]
    if not pinfo.empty:
        player_name = pinfo['Player Names'].values[0]  # Extracting the single value
        current_player_stats.at[index, 'Player Name'] = player_name  # Updating the DataFrame

for index, row in expected_stats.iterrows():
    player_name = row['Bowler']
    cricinfo = current_player_stats[current_player_stats['Player Name'] == player_name]
    if not cricinfo.empty:
        avg = cricinfo['Ave'].values[0]
        overs = cricinfo['Overs'].values[0]
        expected_stats.at[index, 'Avg'] = float(avg)
        expected_stats.at[index, 'Overs'] = float(overs)

reg_df = expected_stats[expected_stats['Overs'] > 50]

#print(reg_df.columns)

x = sm.add_constant(reg_df[['Edge Percentage']])
y = reg_df['Avg']


model = sm.OLS(y, x).fit()
p_values = model.pvalues

print(model.summary())

print(p_values)