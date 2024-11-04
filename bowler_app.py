import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.gridspec import GridSpec
import matplotlib.patches as patches
from bs4 import BeautifulSoup
import requests
import numpy as np

# Load the player information from CSV files
player_info = pd.read_csv('playerinformation.csv')
pace_player_data = pd.read_csv('pacedata.csv')
pace_player_percentiles = pd.read_csv('pacepercentileranks.csv')
spin_player_data = pd.read_csv('spindata.csv')
spin_player_percentiles = pd.read_csv('spinpercentileranks.csv')
pace_bowlers = pace_player_data['Bowler'].unique().tolist()
spin_bowlers = spin_player_data['Bowler'].unique().tolist()

@st.cache_data
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

def bowler_cards(bowler_name, batting_hand, bowler_side, average_lines):
    # Filter the player info for the given bowler name
    info = player_info[player_info['Player Names'] == bowler_name].iloc[0]
    
    # Get the correct image path using the 'Alternative Name'
    image_route = 'Bowling Cards/' + info['Alternative Name'] + '.jpg'
    
    # Create an A4 size figure (8.27 x 11.69 inches)
    fig = plt.figure(figsize=(11.69, 16.54))
    
    # Use GridSpec to create a layout with more rows for scatter plots
    gs = GridSpec(7, 4, figure=fig)  # Increase rows to 10

    # Title area in the middle column (row 0, column 1)
    ax_title = fig.add_subplot(gs[0, 1:3])
    ax_title.text(0.5, 0.6, str(info['Player Names']), ha='center', fontsize=18)
    ax_title.text(0.5, 0.4, "Born: " + str(info['Birth Dates']), ha='center', fontsize=14)
    ax_title.text(0.5, 0.2, "Team: " + str(info['Teams']), ha='center', fontsize=14)
    ax_title.axis('off')

    # Image in the top left corner (row 1-4, column 0)
    ax_img = fig.add_subplot(gs[0, 0])
    img = mpimg.imread(image_route)
    ax_img.imshow(img)
    ax_img.axis('off')
    
    # Filter stats and percentiles
    season_stats = current_player_stats[current_player_stats['Player'] == info['Player Links']]
    season_stats = season_stats.iloc[:, 2:]

    # Table area spanning all columns (row 5-6, columns 0-3)
    ax_table = fig.add_subplot(gs[1, :])
    ax_table.axis('off')
    
    table = plt.table(cellText=season_stats.values,
                      colLabels=season_stats.columns,
                      cellLoc='center', 
                      loc='center',
                      colColours=["#f5f5f5"] * len(season_stats.columns))
    table.scale(1, 4)
    table.auto_set_font_size(False)
    table.set_fontsize(12)

    
    if bowler_name in pace_bowlers:
        pstats = pace_player_data[pace_player_data['Bowler'] == bowler_name]
        percentiles = pace_player_percentiles[pace_player_percentiles['Bowler'] == bowler_name]
    elif bowler_name in spin_bowlers:
        pstats = spin_player_data[spin_player_data['Bowler'] == bowler_name]
        percentiles = spin_player_percentiles[spin_player_percentiles['Bowler'] == bowler_name]

    # Create subplots for colored rectangles
    n_cols = 4
    n_rows = 2
    rect_height = 0.8  # Adjust height of the rectangles

    for i, col in enumerate(pstats.columns[1:]):  # Skip the first column
        row = i // n_cols + 2  # Start from row 7
        col_idx = i % n_cols

        if row >= 9:
            print(f"Row {row} is out of bounds, adjust GridSpec or reduce number of rectangles.")
            break

        ax_rect = fig.add_subplot(gs[row, col_idx])
        ax_rect.axis('off')

        # Get percentile value for the column
        percentile_value = percentiles[col].values[0] if col in percentiles.columns else 0
        # Normalize percentile to a color map range (0-1)
        color = plt.cm.RdYlGn(percentile_value / 100)

        # Create rectangle with an outline
        rect = patches.FancyBboxPatch((0, 0.2), 1, rect_height, boxstyle="round,pad=0.05", color=color, edgecolor='black')
        ax_rect.add_patch(rect)
        ax_rect.text(0.5, 0.7, col, ha='center', va='center', fontsize=10, color='black', fontstyle='oblique')

        # Add pstats value below the rectangle
        pstat_value = pstats[col].values[0] if col in pstats.columns else 'N/A'
        ax_rect.text(0.5, 0.5, f"{pstat_value}", ha='center', va='center', fontsize=15)

    # Color key subplot (make it smaller in height)
    ax_color_key = fig.add_subplot(gs[4, :])
    ax_color_key.axis('off')
    
    # Create a gradient color bar for the key
    gradient = np.linspace(0, 1, 256)
    gradient = np.vstack((gradient, gradient))

    # Display the gradient with a smaller height and aspect ratio 2:1
    ax_color_key.imshow(gradient, aspect=14, cmap='RdYlGn', interpolation='none')
    ax_color_key.text(1.05, 0.5, 'Low Percentile', ha='left', va='center', fontsize=10, color='black')
    ax_color_key.text(228, 0.5, 'High Percentile', ha='left', va='center', fontsize=10, color='black')

    # Load heatmaps and release data
    heatmaps = pd.read_csv('heatmaps.csv')
    release = pd.read_csv('release.csv')
    allmaps = pd.read_csv('allmaps.csv')
    
    heatmaps = heatmaps[heatmaps['Bowler'] == bowler_name]
    release = release[release['Bowler'] == bowler_name]
    all_bowlers = allmaps
    allmaps = allmaps[allmaps['Bowler'] == bowler_name]
    bowler_type = allmaps['Bowler Type'].iloc[0] #May have to .iloc[0]
    releases = all_bowlers[all_bowlers['Bowler Type'] == bowler_type]
    
    
    if bowler_type[0] == 'R':
        if bowler_side == 'Over':
            releases = all_bowlers[all_bowlers['ReleaseY'] < 0]
        elif bowler_side == 'Round':
            releases = all_bowlers[all_bowlers['ReleaseY'] > 0]
        elif bowler_side == 'Both':
            over_releases = all_bowlers[all_bowlers['ReleaseY'] < 0]
            round_releases = all_bowlers[all_bowlers['ReleaseY'] > 0]
    elif bowler_type[0] == 'L':
        if bowler_side == 'Over':
            releases = all_bowlers[all_bowlers['ReleaseY'] > 0]
        elif bowler_side == 'Round':
            releases = all_bowlers[all_bowlers['ReleaseY'] < 0]
        elif bowler_side == 'Both':
            over_releases = all_bowlers[all_bowlers['ReleaseY'] > 0]
            round_releases = all_bowlers[all_bowlers['ReleaseY'] < 0]

    avg_release_y = releases['ReleaseY'].mean()
    avg_release_z = releases['ReleaseZ'].mean()
    if bowler_side  == 'Both':
        both_avg_release_y_over = over_releases['ReleaseY'].mean()
        both_avg_release_z_over = over_releases['ReleaseZ'].mean()
        both_avg_release_y_round = round_releases['ReleaseY'].mean()
        both_avg_release_z_round = round_releases['ReleaseZ'].mean()
    
    if batting_hand == 'Right':
        allmaps = allmaps[allmaps['Batting Hand'] == 'RHB']
        img_path = 'pitch.png'
        pitch = mpimg.imread(img_path)
        # Scatter plot for PitchX vs PitchY
        ax_pitch = fig.add_subplot(gs[5:7, 1:2])
        #ax_pitch.imshow(pitch, extent=[-1.525, 1.525, 0, 21], aspect='auto')
        rect = patches.Rectangle((-1.83, -1.83), 3.66, 22.56, linewidth=1, edgecolor='black', facecolor='#d0f7e3', alpha=0.7)
        ax_pitch.add_patch(rect)
        ax_pitch.plot([-1.83, 1.83], [2.44, 2.44], color='black', linewidth=1, alpha=0.7)
        ax_pitch.plot([-1.83, 1.83], [20.12, 20.12], color='black', linewidth=1, alpha=0.7)
        ax_pitch.scatter(x=0, y=1.22, s=40, color='brown', linewidth=0.8, alpha=.7)
        ax_pitch.scatter(x=-0.13, y=1.22, s=40, color='brown', linewidth=0.8, alpha=.7)
        ax_pitch.scatter(x=0.13, y=1.22, s=40, color='brown', linewidth=0.8, alpha=.7)
        ax_pitch.scatter(x=0, y=22.56, s=40, color='brown', linewidth=0.8, alpha=.7)
        ax_pitch.scatter(x=-0.13, y=22.56, s=40, color='brown', linewidth=0.8, alpha=.7)
        ax_pitch.scatter(x=0.13, y=22.56, s=40, color='brown', linewidth=0.8, alpha=.7)
        ax_pitch.plot([-1.83, 1.83], [3.22, 3.22], color='black', linewidth=1, alpha=0.7)
        ax_pitch.text(x=1.5, y=2.8, s='Yorker', fontsize=5, fontweight='bold', color='black', ha='left')
        ax_pitch.plot([-1.83, 1.83], [6.22, 6.22], color='black', linewidth=1, alpha=0.7)
        ax_pitch.text(x=1.5, y=5.8, s='H-Volley', fontsize=5, fontweight='bold', color='black', ha='left')
        ax_pitch.plot([-1.83, 1.83], [7.22, 7.22], color='black', linewidth=1, alpha=0.7)
        ax_pitch.text(x=1.5, y=6.8, s='Full', fontsize=5, fontweight='bold', color='black', ha='left')
        ax_pitch.plot([-1.83, 1.83], [9.22, 9.22], color='black', linewidth=1, alpha=0.7)
        ax_pitch.plot([-1.83, 1.83], [10.22, 10.22], color='black', linewidth=1, alpha=0.7)
        ax_pitch.text(x=1.5, y=8.8, s='Good', fontsize=5, fontweight='bold', color='black', ha='left')
        ax_pitch.text(x=1.5, y=9.8, s='Back', fontsize=5, fontweight='bold', color='black', ha='left')
        ax_pitch.text(x=1.5, y=10.5, s='Short', fontsize=5, fontweight='bold', color='black', ha='left')

        if bowler_type[0] == 'R' and bowler_side == 'Over':
            allmaps1 = allmaps[allmaps['ReleaseY'] < 0]
        elif bowler_type[0] == 'R' and bowler_side == 'Round':
            allmaps1 = allmaps[allmaps['ReleaseY'] > 0]
        elif bowler_type[0] == 'L' and bowler_side == 'Over':
            allmaps1 = allmaps[allmaps['ReleaseY'] > 0]
        elif bowler_type[0] == 'L' and bowler_side == 'Round':
            allmaps1 = allmaps[allmaps['ReleaseY'] < 0]
        else:
            allmaps1 = allmaps

        ax_pitch.scatter(allmaps1['PitchY'], allmaps1['PitchX'], color='green', alpha=0.7, s=5)
        ax_pitch.set_xlim(left=1.83, right=-1.83)
        ax_pitch.set_ylim(top=20.12, bottom=0)
        ax_pitch.set_xticks([])  # Turn off x-axis tick labels
        ax_pitch.set_yticks([])  # Turn off y-axis tick labels
        ax_pitch.set_title('PitchX vs PitchY',fontsize=10)
    elif batting_hand == 'Left':
        allmaps = allmaps[allmaps['Batting Hand'] == 'LHB']
        img_path = 'pitch.png'
        pitch = mpimg.imread(img_path)
        # Scatter plot for PitchX vs PitchY
        ax_pitch = fig.add_subplot(gs[5:7, 1:2])
        #ax_pitch.imshow(pitch, extent=[-1.525, 1.525, 0, 21], aspect='auto')
        rect = patches.Rectangle((-1.83, -1.83), 3.66, 22.56, linewidth=1, edgecolor='black', facecolor='#d0f7e3', alpha=0.7)
        ax_pitch.add_patch(rect)
        ax_pitch.plot([-1.83, 1.83], [2.44, 2.44], color='black', linewidth=1, alpha=0.7)
        ax_pitch.plot([-1.83, 1.83], [20.12, 20.12], color='black', linewidth=1, alpha=0.7)
        ax_pitch.scatter(x=0, y=1.22, s=40, color='brown', linewidth=0.8, alpha=.7)
        ax_pitch.scatter(x=-0.13, y=1.22, s=40, color='brown', linewidth=0.8, alpha=.7)
        ax_pitch.scatter(x=0.13, y=1.22, s=40, color='brown', linewidth=0.8, alpha=.7)
        ax_pitch.scatter(x=0, y=22.56, s=40, color='brown', linewidth=0.8, alpha=.7)
        ax_pitch.scatter(x=-0.13, y=22.56, s=40, color='brown', linewidth=0.8, alpha=.7)
        ax_pitch.scatter(x=0.13, y=22.56, s=40, color='brown', linewidth=0.8, alpha=.7)
        ax_pitch.plot([-1.83, 1.83], [3.22, 3.22], color='black', linewidth=1, alpha=0.7)
        ax_pitch.text(x=1.5, y=2.8, s='Yorker', fontsize=5, fontweight='bold', color='black', ha='left')
        ax_pitch.plot([-1.83, 1.83], [6.22, 6.22], color='black', linewidth=1, alpha=0.7)
        ax_pitch.text(x=1.5, y=5.8, s='H-Volley', fontsize=5, fontweight='bold', color='black', ha='left')
        ax_pitch.plot([-1.83, 1.83], [7.22, 7.22], color='black', linewidth=1, alpha=0.7)
        ax_pitch.text(x=1.5, y=6.8, s='Full', fontsize=5, fontweight='bold', color='black', ha='left')
        ax_pitch.plot([-1.83, 1.83], [9.22, 9.22], color='black', linewidth=1, alpha=0.7)
        ax_pitch.plot([-1.83, 1.83], [10.22, 10.22], color='black', linewidth=1, alpha=0.7)
        ax_pitch.text(x=1.5, y=8.8, s='Good', fontsize=5, fontweight='bold', color='black', ha='left')
        ax_pitch.text(x=1.5, y=9.8, s='Back', fontsize=5, fontweight='bold', color='black', ha='left')
        ax_pitch.text(x=1.5, y=10.5, s='Short', fontsize=5, fontweight='bold', color='black', ha='left')

        if bowler_type[0] == 'R' and bowler_side == 'Over':
            allmaps1 = allmaps[allmaps['ReleaseY'] < 0]
        elif bowler_type[0] == 'R' and bowler_side == 'Round':
            allmaps1 = allmaps[allmaps['ReleaseY'] > 0]
        elif bowler_type[0] == 'L' and bowler_side == 'Over':
            allmaps1 = allmaps[allmaps['ReleaseY'] > 0]
        elif bowler_type[0] == 'L' and bowler_side == 'Round':
            allmaps1 = allmaps[allmaps['ReleaseY'] < 0]
        else:
            allmaps1 = allmaps

        ax_pitch.scatter(allmaps1['PitchY'], allmaps1['PitchX'], color='green', alpha=0.7, s=5)
        ax_pitch.set_xlim(left=1.83, right=-1.83)
        ax_pitch.set_ylim(top=20.12, bottom=0)
        ax_pitch.set_xticks([])  # Turn off x-axis tick labels
        ax_pitch.set_yticks([])  # Turn off y-axis tick labels
        ax_pitch.set_title('PitchX vs PitchY',fontsize=10)
    elif batting_hand == 'Both':
        img_path = 'pitch.png'
        pitch = mpimg.imread(img_path)
        # Scatter plot for PitchX vs PitchY
        ax_pitch = fig.add_subplot(gs[5:7, 1:2])
        #ax_pitch.imshow(pitch, extent=[-1.525, 1.525, 0, 21], aspect='auto')
        rect = patches.Rectangle((-1.83, -1.83), 3.66, 22.56, linewidth=1, edgecolor='black', facecolor='#d0f7e3', alpha=0.7)
        ax_pitch.add_patch(rect)
        ax_pitch.plot([-1.83, 1.83], [2.44, 2.44], color='black', linewidth=1, alpha=0.7)
        ax_pitch.plot([-1.83, 1.83], [20.12, 20.12], color='black', linewidth=1, alpha=0.7)
        ax_pitch.scatter(x=0, y=1.22, s=40, color='brown', linewidth=0.8, alpha=.7)
        ax_pitch.scatter(x=-0.13, y=1.22, s=40, color='brown', linewidth=0.8, alpha=.7)
        ax_pitch.scatter(x=0.13, y=1.22, s=40, color='brown', linewidth=0.8, alpha=.7)
        ax_pitch.scatter(x=0, y=22.56, s=40, color='brown', linewidth=0.8, alpha=.7)
        ax_pitch.scatter(x=-0.13, y=22.56, s=40, color='brown', linewidth=0.8, alpha=.7)
        ax_pitch.scatter(x=0.13, y=22.56, s=40, color='brown', linewidth=0.8, alpha=.7)
        ax_pitch.plot([-1.83, 1.83], [3.22, 3.22], color='black', linewidth=1, alpha=0.7)
        ax_pitch.text(x=1.5, y=2.8, s='Yorker', fontsize=5, fontweight='bold', color='black', ha='left')
        ax_pitch.plot([-1.83, 1.83], [6.22, 6.22], color='black', linewidth=1, alpha=0.7)
        ax_pitch.text(x=1.5, y=5.8, s='H-Volley', fontsize=5, fontweight='bold', color='black', ha='left')
        ax_pitch.plot([-1.83, 1.83], [7.22, 7.22], color='black', linewidth=1, alpha=0.7)
        ax_pitch.text(x=1.5, y=6.8, s='Full', fontsize=5, fontweight='bold', color='black', ha='left')
        ax_pitch.plot([-1.83, 1.83], [9.22, 9.22], color='black', linewidth=1, alpha=0.7)
        ax_pitch.plot([-1.83, 1.83], [10.22, 10.22], color='black', linewidth=1, alpha=0.7)
        ax_pitch.text(x=1.5, y=8.8, s='Good', fontsize=5, fontweight='bold', color='black', ha='left')
        ax_pitch.text(x=1.5, y=9.8, s='Back', fontsize=5, fontweight='bold', color='black', ha='left')
        ax_pitch.text(x=1.5, y=10.5, s='Short', fontsize=5, fontweight='bold', color='black', ha='left')

        if bowler_type[0] == 'R' and bowler_side == 'Over':
            allmaps1 = allmaps[allmaps['ReleaseY'] < 0]
        elif bowler_type[0] == 'R' and bowler_side == 'Round':
            allmaps1 = allmaps[allmaps['ReleaseY'] > 0]
        elif bowler_type[0] == 'L' and bowler_side == 'Over':
            allmaps1 = allmaps[allmaps['ReleaseY'] > 0]
        elif bowler_type[0] == 'L' and bowler_side == 'Round':
            allmaps1 = allmaps[allmaps['ReleaseY'] < 0]
        else:
            allmaps1 = allmaps

        ax_pitch.scatter(allmaps1['PitchY'], allmaps1['PitchX'], color='green', alpha=0.7, s=5)
        ax_pitch.set_xlim(left=1.83, right=-1.83)
        ax_pitch.set_ylim(top=20.12, bottom=0)
        ax_pitch.set_xticks([])  # Turn off x-axis tick labels
        ax_pitch.set_yticks([])  # Turn off y-axis tick labels
        ax_pitch.set_title('PitchX vs PitchY',fontsize=10)
    
    
    stumps_path = 'stumps.png'
    stumps = mpimg.imread(stumps_path)
    
    if batting_hand == 'Right':
        allmaps = allmaps[allmaps['Batting Hand'] == 'RHB']
        # Scatter plot for ReleaseY vs ReleaseZ
        if bowler_side == 'Over' and bowler_type[0] == 'R':
            ax_release = fig.add_subplot(gs[5:7, :1])
            ax_release.imshow(stumps, extent=[-0.1143, 0.1143, 0, 0.72], aspect='auto')
            ax_release.scatter(allmaps['ReleaseY'], allmaps['ReleaseZ'], alpha=0.7, s=5, color='green')
            ax_release.set_ylim(bottom=0, top=2.5)
            ax_release.set_xlim(left=-1.83, right=0)
            if average_lines:
                ax_release.plot([avg_release_y, avg_release_y], [0, 2.5], color='red', linewidth=1, alpha=0.5)
                ax_release.plot([-1.83, 0], [avg_release_z, avg_release_z], color='red', linewidth=1, alpha=0.5)
                ax_release.text(x=-1.8, y=0.1, s='Champ Average', fontsize=5, fontweight='bold', color='red', ha='left')
                plotted = allmaps[allmaps['ReleaseY'] < 0]
                ax_release.plot([plotted['ReleaseY'].mean(), plotted['ReleaseY'].mean()], [0, 2.5], color='green', linewidth=1, alpha=0.5)
                ax_release.plot([-1.83, 0], [plotted['ReleaseZ'].mean(), plotted['ReleaseZ'].mean()], color='green', linewidth=1, alpha=0.5)
                ax_release.text(x=-1.8, y=0.05, s='Player Average', fontsize=5, fontweight='bold', color='green', ha='left')
            ax_release.set_xticks([])  # Turn off x-axis tick labels
            ax_release.set_yticks([])  # Turn off y-axis tick labels
            ax_release.set_title('ReleaseY vs ReleaseZ',fontsize=10)
        elif bowler_side == 'Round' and bowler_type[0] == 'R':
            ax_release = fig.add_subplot(gs[5:7, :1])
            ax_release.imshow(stumps, extent=[-0.1143, 0.1143, 0, 0.72], aspect='auto')
            ax_release.scatter(allmaps['ReleaseY'], allmaps['ReleaseZ'], alpha=0.7, s=5, color='green')
            ax_release.set_ylim(bottom=0, top=2.5)
            ax_release.set_xlim(left=0, right=1.83)
            if average_lines:
                ax_release.plot([avg_release_y, avg_release_y], [0, 2.5], color='red', linewidth=1, alpha=0.5)
                ax_release.plot([0, 1.83], [avg_release_z, avg_release_z], color='red', linewidth=1, alpha=0.5)
                ax_release.text(1.8, y=0.1, s='Champ Average', fontsize=5, fontweight='bold', color='red', ha='right')
                plotted = allmaps[allmaps['ReleaseY'] > 0]
                ax_release.plot([plotted['ReleaseY'].mean(), plotted['ReleaseY'].mean()], [0, 2.5], color='green', linewidth=1, alpha=0.5)
                ax_release.plot([-1.83, 0], [plotted['ReleaseZ'].mean(), plotted['ReleaseZ'].mean()], color='green', linewidth=1, alpha=0.5)
                ax_release.text(x=1.8, y=0.05, s='Player Average', fontsize=5, fontweight='bold', color='green', ha='right')
            ax_release.set_xticks([])  # Turn off x-axis tick labels
            ax_release.set_yticks([])  # Turn off y-axis tick labels
            ax_release.set_title('ReleaseY vs ReleaseZ',fontsize=10)
        elif bowler_side == 'Round' and bowler_type[0] == 'L':
            ax_release = fig.add_subplot(gs[5:7, :1])
            ax_release.imshow(stumps, extent=[-0.1143, 0.1143, 0, 0.72], aspect='auto')
            ax_release.scatter(allmaps['ReleaseY'], allmaps['ReleaseZ'], alpha=0.7, s=5, color='green')
            ax_release.set_ylim(bottom=0, top=2.5)
            ax_release.set_xlim(left=-1.83, right=0)
            if average_lines:
                ax_release.plot([avg_release_y, avg_release_y], [0, 2.5], color='red', linewidth=1, alpha=0.5)
                ax_release.plot([-1.83, 0], [avg_release_z, avg_release_z], color='red', linewidth=1, alpha=0.5)
                ax_release.text(-1.8, y=0.1, s='Champ Average', fontsize=5, fontweight='bold', color='red', ha='left')
                plotted = allmaps[allmaps['ReleaseY'] < 0]
                ax_release.plot([plotted['ReleaseY'].mean(), plotted['ReleaseY'].mean()], [0, 2.5], color='green', linewidth=1, alpha=0.5)
                ax_release.plot([-1.83, 0], [plotted['ReleaseZ'].mean(), plotted['ReleaseZ'].mean()], color='green', linewidth=1, alpha=0.5)
                ax_release.text(x=-1.8, y=0.05, s='Player Average', fontsize=5, fontweight='bold', color='green', ha='left')
            ax_release.set_xticks([])  # Turn off x-axis tick labels
            ax_release.set_yticks([])  # Turn off y-axis tick labels
            ax_release.set_title('ReleaseY vs ReleaseZ',fontsize=10)
        elif bowler_side == 'Over' and bowler_type[0] == 'L':
            ax_release = fig.add_subplot(gs[5:7, :1])
            ax_release.imshow(stumps, extent=[-0.1143, 0.1143, 0, 0.72], aspect='auto')
            ax_release.scatter(allmaps['ReleaseY'], allmaps['ReleaseZ'], alpha=0.7, s=5, color='green')
            ax_release.set_ylim(bottom=0, top=2.5)
            ax_release.set_xlim(left=0, right=1.83)
            if average_lines:
                ax_release.plot([avg_release_y, avg_release_y], [0, 2.5], color='red', linewidth=1, alpha=0.5)
                ax_release.plot([0, 1.83], [avg_release_z, avg_release_z], color='red', linewidth=1, alpha=0.5)
                ax_release.text(x=1.8, y=0.1, s='Champ Average', fontsize=5, fontweight='bold', color='red', ha='right')
                plotted = allmaps[allmaps['ReleaseY'] > 0]
                ax_release.plot([plotted['ReleaseY'].mean(), plotted['ReleaseY'].mean()], [0, 2.5], color='green', linewidth=1, alpha=0.5)
                ax_release.plot([-1.83, 0], [plotted['ReleaseZ'].mean(), plotted['ReleaseZ'].mean()], color='green', linewidth=1, alpha=0.5)
                ax_release.text(x=1.8, y=0.05, s='Player Average', fontsize=5, fontweight='bold', color='green', ha='right')
            ax_release.set_xticks([])  # Turn off x-axis tick labels
            ax_release.set_yticks([])  # Turn off y-axis tick labels
            ax_release.set_title('ReleaseY vs ReleaseZ',fontsize=10)
        elif bowler_side == 'Both':
            ax_release = fig.add_subplot(gs[5:7, :1])
            ax_release.imshow(stumps, extent=[-0.1143, 0.1143, 0, 0.72], aspect='auto')
            ax_release.scatter(allmaps['ReleaseY'], allmaps['ReleaseZ'], alpha=0.7, s=5, color='green')
            ax_release.set_ylim(bottom=0, top=2.5)
            ax_release.set_xlim(left=-1.83, right=1.83)
            if average_lines:
                ax_release.plot([both_avg_release_y_over, both_avg_release_y_over], [0, 2.5], color='red', linewidth=1, alpha=0.5)
                ax_release.plot([-1.83, 1.83], [both_avg_release_z_over, both_avg_release_z_over], color='red', linewidth=1, alpha=0.5)
                ax_release.text(x=-1.8, y=0.05, s='Champ Average', fontsize=5, fontweight='bold', color='red', ha='left')
                ax_release.plot([both_avg_release_y_round, both_avg_release_y_round], [0, 2.5], color='red', linewidth=1, alpha=0.5)
                ax_release.plot([-1.83, 1.83], [both_avg_release_z_round, both_avg_release_z_round], color='red', linewidth=1, alpha=0.5)
            plotted = allmaps[allmaps['ReleaseY'] < 0]
            ax_release.set_xticks([])  # Turn off x-axis tick labels
            ax_release.set_yticks([])  # Turn off y-axis tick labels
            ax_release.set_title('ReleaseY vs ReleaseZ',fontsize=10)

    elif batting_hand == 'Left':
        allmaps = allmaps[allmaps['Batting Hand'] == 'LHB']
        # Scatter plot for ReleaseY vs ReleaseZ
        if bowler_side == 'Over' and bowler_type[0] == 'R':
            ax_release = fig.add_subplot(gs[5:7, :1])
            ax_release.imshow(stumps, extent=[-0.1143, 0.1143, 0, 0.72], aspect='auto')
            ax_release.scatter(allmaps['ReleaseY'], allmaps['ReleaseZ'], alpha=0.7, s=5, color='green')
            ax_release.set_ylim(bottom=0, top=2.5)
            ax_release.set_xlim(left=-1.83, right=0)
            if average_lines:
                ax_release.plot([avg_release_y, avg_release_y], [0, 2.5], color='red', linewidth=1, alpha=0.5)
                ax_release.plot([-1.83, 0], [avg_release_z, avg_release_z], color='red', linewidth=1, alpha=0.5)
                ax_release.text(x=-1.8, y=0.1, s='Champ Average', fontsize=5, fontweight='bold', color='red', ha='left')
                plotted = allmaps[allmaps['ReleaseY'] < 0]
                ax_release.plot([plotted['ReleaseY'].mean(), plotted['ReleaseY'].mean()], [0, 2.5], color='green', linewidth=1, alpha=0.5)
                ax_release.plot([-1.83, 0], [plotted['ReleaseZ'].mean(), plotted['ReleaseZ'].mean()], color='green', linewidth=1, alpha=0.5)
                ax_release.text(x=-1.8, y=0.05, s='Player Average', fontsize=5, fontweight='bold', color='green', ha='left')
            ax_release.set_xticks([])  # Turn off x-axis tick labels
            ax_release.set_yticks([])  # Turn off y-axis tick labels
            ax_release.set_title('ReleaseY vs ReleaseZ',fontsize=10)
        elif bowler_side == 'Round' and bowler_type[0] == 'R':
            ax_release = fig.add_subplot(gs[5:7, :1])
            ax_release.imshow(stumps, extent=[-0.1143, 0.1143, 0, 0.72], aspect='auto')
            ax_release.scatter(allmaps['ReleaseY'], allmaps['ReleaseZ'], alpha=0.7, s=5, color='green')
            ax_release.set_ylim(bottom=0, top=2.5)
            ax_release.set_xlim(left=0, right=1.83)
            if average_lines:
                ax_release.plot([avg_release_y, avg_release_y], [0, 2.5], color='red', linewidth=1, alpha=0.5)
                ax_release.plot([0, 1.83], [avg_release_z, avg_release_z], color='red', linewidth=1, alpha=0.5)
                ax_release.text(1.8, y=0.1, s='Champ Average', fontsize=5, fontweight='bold', color='red', ha='right')
                plotted = allmaps[allmaps['ReleaseY'] > 0]
                ax_release.plot([plotted['ReleaseY'].mean(), plotted['ReleaseY'].mean()], [0, 2.5], color='green', linewidth=1, alpha=0.5)
                ax_release.plot([-1.83, 0], [plotted['ReleaseZ'].mean(), plotted['ReleaseZ'].mean()], color='green', linewidth=1, alpha=0.5)
                ax_release.text(x=1.8, y=0.05, s='Player Average', fontsize=5, fontweight='bold', color='green', ha='right')
            ax_release.set_xticks([])  # Turn off x-axis tick labels
            ax_release.set_yticks([])  # Turn off y-axis tick labels
            ax_release.set_title('ReleaseY vs ReleaseZ',fontsize=10)

        elif bowler_side == 'Round' and bowler_type[0] == 'L':
            ax_release = fig.add_subplot(gs[5:7, :1])
            ax_release.imshow(stumps, extent=[-0.1143, 0.1143, 0, 0.72], aspect='auto')
            ax_release.scatter(allmaps['ReleaseY'], allmaps['ReleaseZ'], alpha=0.7, s=5, color='green')
            ax_release.set_ylim(bottom=0, top=2.5)
            ax_release.set_xlim(left=-1.83, right=0)
            if average_lines:
                ax_release.plot([avg_release_y, avg_release_y], [0, 2.5], color='red', linewidth=1, alpha=0.5)
                ax_release.plot([-1.83, 0], [avg_release_z, avg_release_z], color='red', linewidth=1, alpha=0.5)
                ax_release.text(-1.8, y=0.1, s='Champ Average', fontsize=5, fontweight='bold', color='red', ha='left')
                plotted = allmaps[allmaps['ReleaseY'] < 0]
                ax_release.plot([plotted['ReleaseY'].mean(), plotted['ReleaseY'].mean()], [0, 2.5], color='green', linewidth=1, alpha=0.5)
                ax_release.plot([-1.83, 0], [plotted['ReleaseZ'].mean(), plotted['ReleaseZ'].mean()], color='green', linewidth=1, alpha=0.5)
                ax_release.text(x=-1.8, y=0.05, s='Player Average', fontsize=5, fontweight='bold', color='green', ha='left')
            ax_release.set_xticks([])  # Turn off x-axis tick labels
            ax_release.set_yticks([])  # Turn off y-axis tick labels
            ax_release.set_title('ReleaseY vs ReleaseZ',fontsize=10)
        elif bowler_side == 'Over' and bowler_type[0] == 'L':
            ax_release = fig.add_subplot(gs[5:7, :1])
            ax_release.imshow(stumps, extent=[-0.1143, 0.1143, 0, 0.72], aspect='auto')
            ax_release.scatter(allmaps['ReleaseY'], allmaps['ReleaseZ'], alpha=0.7, s=5, color='green')
            ax_release.set_ylim(bottom=0, top=2.5)
            ax_release.set_xlim(left=0, right=1.83)
            if average_lines:
                ax_release.plot([avg_release_y, avg_release_y], [0, 2.5], color='red', linewidth=1, alpha=0.5)
                ax_release.plot([0, 1.83], [avg_release_z, avg_release_z], color='red', linewidth=1, alpha=0.5)
                ax_release.text(x=1.8, y=0.1, s='Champ Average', fontsize=5, fontweight='bold', color='red', ha='right')
                plotted = allmaps[allmaps['ReleaseY'] > 0]
                ax_release.plot([plotted['ReleaseY'].mean(), plotted['ReleaseY'].mean()], [0, 2.5], color='green', linewidth=1, alpha=0.5)
                ax_release.plot([-1.83, 0], [plotted['ReleaseZ'].mean(), plotted['ReleaseZ'].mean()], color='green', linewidth=1, alpha=0.5)
                ax_release.text(x=1.8, y=0.05, s='Player Average', fontsize=5, fontweight='bold', color='green', ha='right')
            ax_release.set_xticks([])  # Turn off x-axis tick labels
            ax_release.set_yticks([])  # Turn off y-axis tick labels
            ax_release.set_title('ReleaseY vs ReleaseZ',fontsize=10)
        elif bowler_side == 'Both':
            ax_release = fig.add_subplot(gs[5:7, :1])
            ax_release.imshow(stumps, extent=[-0.1143, 0.1143, 0, 0.72], aspect='auto')
            ax_release.scatter(allmaps['ReleaseY'], allmaps['ReleaseZ'], alpha=0.7, s=5, color='green')
            ax_release.set_ylim(bottom=0, top=2.5)
            ax_release.set_xlim(left=-1.83, right=1.83)
            if average_lines:
                ax_release.plot([both_avg_release_y_over, both_avg_release_y_over], [0, 2.5], color='red', linewidth=1, alpha=0.5)
                ax_release.plot([-1.83, 1.83], [both_avg_release_z_over, both_avg_release_z_over], color='red', linewidth=1, alpha=0.5)
                ax_release.text(x=-1.8, y=0.05, s='Champ Average', fontsize=5, fontweight='bold', color='red', ha='left')
                ax_release.plot([both_avg_release_y_round, both_avg_release_y_round], [0, 2.5], color='red', linewidth=1, alpha=0.5)
                ax_release.plot([-1.83, 1.83], [both_avg_release_z_round, both_avg_release_z_round], color='red', linewidth=1, alpha=0.5)
            plotted = allmaps[allmaps['ReleaseY'] < 0]
            ax_release.set_xticks([])  # Turn off x-axis tick labels
            ax_release.set_yticks([])  # Turn off y-axis tick labels
            ax_release.set_title('ReleaseY vs ReleaseZ',fontsize=10)

    elif batting_hand == 'Both':
        if bowler_side == 'Over' and bowler_type[0] == 'R':
            ax_release = fig.add_subplot(gs[5:7, :1])
            ax_release.imshow(stumps, extent=[-0.1143, 0.1143, 0, 0.72], aspect='auto')
            ax_release.scatter(allmaps['ReleaseY'], allmaps['ReleaseZ'], alpha=0.7, s=5, color='green')
            ax_release.set_ylim(bottom=0, top=2.5)
            ax_release.set_xlim(left=-1.83, right=0)
            if average_lines:
                ax_release.plot([avg_release_y, avg_release_y], [0, 2.5], color='red', linewidth=1, alpha=0.5)
                ax_release.plot([-1.83, 0], [avg_release_z, avg_release_z], color='red', linewidth=1, alpha=0.5)
                ax_release.text(x=-1.8, y=0.1, s='Champ Average', fontsize=5, fontweight='bold', color='red', ha='left')
                plotted = allmaps[allmaps['ReleaseY'] < 0]
                ax_release.plot([plotted['ReleaseY'].mean(), plotted['ReleaseY'].mean()], [0, 2.5], color='green', linewidth=1, alpha=0.5)
                ax_release.plot([-1.83, 0], [plotted['ReleaseZ'].mean(), plotted['ReleaseZ'].mean()], color='green', linewidth=1, alpha=0.5)
                ax_release.text(x=-1.8, y=0.05, s='Player Average', fontsize=5, fontweight='bold', color='green', ha='left')
            ax_release.set_xticks([])  # Turn off x-axis tick labels
            ax_release.set_yticks([])  # Turn off y-axis tick labels
            ax_release.set_title('ReleaseY vs ReleaseZ',fontsize=10)
        elif bowler_side == 'Round' and bowler_type[0] == 'R':
            ax_release = fig.add_subplot(gs[5:7, :1])
            ax_release.imshow(stumps, extent=[-0.1143, 0.1143, 0, 0.72], aspect='auto')
            ax_release.scatter(allmaps['ReleaseY'], allmaps['ReleaseZ'], alpha=0.7, s=5, color='green')
            ax_release.set_ylim(bottom=0, top=2.5)
            ax_release.set_xlim(left=0, right=1.83)
            if average_lines:
                ax_release.plot([avg_release_y, avg_release_y], [0, 2.5], color='red', linewidth=1, alpha=0.5)
                ax_release.plot([0, 1.83], [avg_release_z, avg_release_z], color='red', linewidth=1, alpha=0.5)
                ax_release.text(1.8, y=0.1, s='Champ Average', fontsize=5, fontweight='bold', color='red', ha='right')
                plotted = allmaps[allmaps['ReleaseY'] > 0]
                ax_release.plot([plotted['ReleaseY'].mean(), plotted['ReleaseY'].mean()], [0, 2.5], color='green', linewidth=1, alpha=0.5)
                ax_release.plot([-1.83, 0], [plotted['ReleaseZ'].mean(), plotted['ReleaseZ'].mean()], color='green', linewidth=1, alpha=0.5)
                ax_release.text(x=1.8, y=0.05, s='Player Average', fontsize=5, fontweight='bold', color='green', ha='right')
            ax_release.set_xticks([])  # Turn off x-axis tick labels
            ax_release.set_yticks([])  # Turn off y-axis tick labels
            ax_release.set_title('ReleaseY vs ReleaseZ',fontsize=10)
        elif bowler_side == 'Round' and bowler_type[0] == 'L':
            ax_release = fig.add_subplot(gs[5:7, :1])
            ax_release.imshow(stumps, extent=[-0.1143, 0.1143, 0, 0.72], aspect='auto')
            ax_release.scatter(allmaps['ReleaseY'], allmaps['ReleaseZ'], alpha=0.7, s=5, color='green')
            ax_release.set_ylim(bottom=0, top=2.5)
            ax_release.set_xlim(left=-1.83, right=0)
            if average_lines:
                ax_release.plot([avg_release_y, avg_release_y], [0, 2.5], color='red', linewidth=1, alpha=0.5)
                ax_release.plot([-1.83, 0], [avg_release_z, avg_release_z], color='red', linewidth=1, alpha=0.5)
                ax_release.text(-1.8, y=0.1, s='Champ Average', fontsize=5, fontweight='bold', color='red', ha='left')
                plotted = allmaps[allmaps['ReleaseY'] < 0]
                ax_release.plot([plotted['ReleaseY'].mean(), plotted['ReleaseY'].mean()], [0, 2.5], color='green', linewidth=1, alpha=0.5)
                ax_release.plot([-1.83, 0], [plotted['ReleaseZ'].mean(), plotted['ReleaseZ'].mean()], color='green', linewidth=1, alpha=0.5)
                ax_release.text(x=-1.8, y=0.05, s='Player Average', fontsize=5, fontweight='bold', color='green', ha='left')
            ax_release.set_xticks([])  # Turn off x-axis tick labels
            ax_release.set_yticks([])  # Turn off y-axis tick labels
            ax_release.set_title('ReleaseY vs ReleaseZ',fontsize=10)
        elif bowler_side == 'Over' and bowler_type[0] == 'L':
            ax_release = fig.add_subplot(gs[5:7, :1])
            ax_release.imshow(stumps, extent=[-0.1143, 0.1143, 0, 0.72], aspect='auto')
            ax_release.scatter(allmaps['ReleaseY'], allmaps['ReleaseZ'], alpha=0.7, s=5, color='green')
            ax_release.set_ylim(bottom=0, top=2.5)
            ax_release.set_xlim(left=0, right=1.83)
            if average_lines:
                ax_release.plot([avg_release_y, avg_release_y], [0, 2.5], color='red', linewidth=1, alpha=0.5)
                ax_release.plot([0, 1.83], [avg_release_z, avg_release_z], color='red', linewidth=1, alpha=0.5)
                ax_release.text(x=1.8, y=0.1, s='Champ Average', fontsize=5, fontweight='bold', color='red', ha='right')
                plotted = allmaps[allmaps['ReleaseY'] > 0]
                ax_release.plot([plotted['ReleaseY'].mean(), plotted['ReleaseY'].mean()], [0, 2.5], color='green', linewidth=1, alpha=0.5)
                ax_release.plot([-1.83, 0], [plotted['ReleaseZ'].mean(), plotted['ReleaseZ'].mean()], color='green', linewidth=1, alpha=0.5)
                ax_release.text(x=1.8, y=0.05, s='Player Average', fontsize=5, fontweight='bold', color='green', ha='right')
            ax_release.set_xticks([])  # Turn off x-axis tick labels
            ax_release.set_yticks([])  # Turn off y-axis tick labels
            ax_release.set_title('ReleaseY vs ReleaseZ',fontsize=10)
        elif bowler_side == 'Both':
            ax_release = fig.add_subplot(gs[5:7, :1])
            ax_release.imshow(stumps, extent=[-0.1143, 0.1143, 0, 0.72], aspect='auto')
            ax_release.scatter(allmaps['ReleaseY'], allmaps['ReleaseZ'], alpha=0.7, s=5, color='green')
            ax_release.set_ylim(bottom=0, top=2.5)
            ax_release.set_xlim(left=-1.83, right=1.83)
            if average_lines:
                ax_release.plot([both_avg_release_y_over, both_avg_release_y_over], [0, 2.5], color='red', linewidth=1, alpha=0.5)
                ax_release.plot([-1.83, 1.83], [both_avg_release_z_over, both_avg_release_z_over], color='red', linewidth=1, alpha=0.5)
                ax_release.text(x=-1.8, y=0.05, s='Champ Average', fontsize=5, fontweight='bold', color='red', ha='left')
                ax_release.plot([both_avg_release_y_round, both_avg_release_y_round], [0, 2.5], color='red', linewidth=1, alpha=0.5)
                ax_release.plot([-1.83, 1.83], [both_avg_release_z_round, both_avg_release_z_round], color='red', linewidth=1, alpha=0.5)
            plotted = allmaps[allmaps['ReleaseY'] < 0]
            ax_release.set_xticks([])  # Turn off x-axis tick labels
            ax_release.set_yticks([])  # Turn off y-axis tick labels
            ax_release.set_title('ReleaseY vs ReleaseZ',fontsize=10)
    
    if batting_hand == 'Right':
        allmaps = allmaps[allmaps['Batting Hand'] == 'RHB']
        if bowler_type[0] == 'R' and bowler_side == 'Over':
            allmaps = allmaps[allmaps['ReleaseY'] < 0]
        elif bowler_type[0] == 'R' and bowler_side == 'Round':
            allmaps = allmaps[allmaps['ReleaseY'] > 0]
        elif bowler_type[0] == 'L' and bowler_side == 'Over':
            allmaps = allmaps[allmaps['ReleaseY'] > 0]
        elif bowler_type[0] == 'L' and bowler_side == 'Round':
            allmaps = allmaps[allmaps['ReleaseY'] < 0]
        else:
            allmaps = allmaps
        # Scatter plot for ReleaseY vs ReleaseZ
        ax_release = fig.add_subplot(gs[5:7, 2:])
        ax_release.imshow(stumps, extent=[-0.1143, 0.1143, 0, 0.72], aspect='auto')
        ax_release.scatter(allmaps['PastY'], allmaps['PastZ'], alpha=0.7, s=5, color='green')
        ax_release.set_ylim(bottom=0, top=2.5)
        ax_release.set_xlim(left=-1.525, right=1.525)
        ax_release.set_xticks([])  # Turn off x-axis tick labels
        ax_release.set_yticks([])  # Turn off y-axis tick labels
        ax_release.set_title('PastY vs PastZ',fontsize=10)
    elif batting_hand == 'Left':
        allmaps = allmaps[allmaps['Batting Hand'] == 'LHB']
        if bowler_type[0] == 'R' and bowler_side == 'Over':
            allmaps = allmaps[allmaps['ReleaseY'] < 0]
        elif bowler_type[0] == 'R' and bowler_side == 'Round':
            allmaps = allmaps[allmaps['ReleaseY'] > 0]
        elif bowler_type[0] == 'L' and bowler_side == 'Over':
            allmaps = allmaps[allmaps['ReleaseY'] > 0]
        elif bowler_type[0] == 'L' and bowler_side == 'Round':
            allmaps = allmaps[allmaps['ReleaseY'] < 0]
        else:
            allmaps = allmaps
        # Scatter plot for ReleaseY vs ReleaseZ
        ax_release = fig.add_subplot(gs[5:7, 2:])
        ax_release.imshow(stumps, extent=[-0.1143, 0.1143, 0, 0.72], aspect='auto')
        ax_release.scatter(allmaps['PastY'], allmaps['PastZ'], alpha=0.7, s=5, color='green')
        ax_release.set_ylim(bottom=0, top=2.5)
        ax_release.set_xlim(left=-1.525, right=1.525)
        ax_release.set_xticks([])  # Turn off x-axis tick labels
        ax_release.set_yticks([])  # Turn off y-axis tick labels
        ax_release.set_title('PastY vs PastZ',fontsize=10)
    elif batting_hand == 'Both':
        if bowler_type[0] == 'R' and bowler_side == 'Over':
            allmaps = allmaps[allmaps['ReleaseY'] < 0]
        elif bowler_type[0] == 'R' and bowler_side == 'Round':
            allmaps = allmaps[allmaps['ReleaseY'] > 0]
        elif bowler_type[0] == 'L' and bowler_side == 'Over':
            allmaps = allmaps[allmaps['ReleaseY'] > 0]
        elif bowler_type[0] == 'L' and bowler_side == 'Round':
            allmaps = allmaps[allmaps['ReleaseY'] < 0]
        else:
            allmaps = allmaps
        ax_release = fig.add_subplot(gs[5:7, 2:])
        ax_release.imshow(stumps, extent=[-0.1143, 0.1143, 0, 0.72], aspect='auto')
        ax_release.scatter(allmaps['PastY'], allmaps['PastZ'], alpha=0.7, s=5, color='green')
        ax_release.set_ylim(bottom=0, top=2.5)
        ax_release.set_xlim(left=-1.525, right=1.525)
        ax_release.set_xticks([])  # Turn off x-axis tick labels
        ax_release.set_yticks([])  # Turn off y-axis tick labels
        ax_release.set_title('PastY vs PastZ',fontsize=10)
    plt.tight_layout()
    return fig



# Streamlit interface
st.title("Bowler Cards Web App")
bowler_name = st.selectbox("Select a Bowler", player_info['Player Names'].unique())
batter_hand = st.selectbox("Batter Hand", ['Both', 'Right', 'Left'])
bowler_side = st.selectbox("Over or Round", ['Both','Over', 'Round'])
average_lines = st.checkbox("Toggle Average Releases", value=True)

if st.button("Generate Bowler Card"):
    fig = bowler_cards(bowler_name, batter_hand, bowler_side, average_lines)
    st.pyplot(fig)
    

