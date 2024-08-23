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

def bowler_cards(bowler_name):
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
    
    heatmaps = heatmaps[heatmaps['Bowler'] == bowler_name]
    release = release[release['Bowler'] == bowler_name]
    
    img_path = 'cricketpitch.png'
    pitch = mpimg.imread(img_path)
    # Scatter plot for PitchX vs PitchY
    ax_pitch = fig.add_subplot(gs[5, 0:2])
    ax_pitch.imshow(pitch, extent=[0, 21, -1.525, 1.525], aspect='auto')
    ax_pitch.scatter(heatmaps['PitchX'], heatmaps['PitchY'], alpha=0.7, s=5)
    ax_pitch.set_xlim(left=0, right=21)
    ax_pitch.set_ylim(top=1.525, bottom=-1.525)
    ax_pitch.set_xticks([])  # Turn off x-axis tick labels
    ax_pitch.set_yticks([])  # Turn off y-axis tick labels
    ax_pitch.set_title('PitchX vs PitchY',fontsize=10)
    
    pitchX = heatmaps['PitchX']
    pitchY = heatmaps['PitchY']
    runs = heatmaps['Runs']
    
    # Define bins for PitchX and PitchY
    x_bins = np.linspace(0, 21, 50)  # Adjust the number of bins if necessary
    y_bins = np.linspace(-1.525, 1.525, 50)  # Adjust the number of bins if necessary
    
    # Create a 2D histogram with the sum of runs in each bin
    hist, xedges, yedges = np.histogram2d(pitchX, pitchY, bins=[x_bins, y_bins], weights=runs)
    
    # Create a subplot for the zonal heatmap
    ax_runs = fig.add_subplot(gs[6, 0:2])
    
    # Plot the heatmap using imshow
    cax = ax_runs.imshow(hist.T, origin='lower', cmap='RdYlGn_r', extent=[0, 21, -3.5, 3.5])
    
    # Set the title
    ax_runs.set_title('Zonal Heatmap of Runs', fontsize=10)
    
    # Hide x and y ticks
    ax_runs.set_xticks([])
    ax_runs.set_yticks([])
    
    stumps_path = 'stumps.png'
    stumps = mpimg.imread(stumps_path)
    
    # Scatter plot for ReleaseY vs ReleaseZ
    ax_release = fig.add_subplot(gs[5:7, 2:])
    ax_release.imshow(stumps, extent=[-0.1143, 0.1143, 0, 0.72], aspect='auto')
    ax_release.scatter(release['ReleaseY'], release['ReleaseZ'], alpha=0.7, s=5)
    ax_release.set_ylim(bottom=0, top=2.5)
    ax_release.set_xlim(left=-1.525, right=1.525)
    ax_release.set_xticks([])  # Turn off x-axis tick labels
    ax_release.set_yticks([])  # Turn off y-axis tick labels
    ax_release.set_title('ReleaseY vs ReleaseZ',fontsize=10)
    plt.tight_layout()
    return fig


# Streamlit interface
st.title("Bowler Cards Web App")
bowler_name = st.selectbox("Select a Bowler", player_info['Player Names'].unique())

if st.button("Generate Bowler Card"):
    fig = bowler_cards(bowler_name)
    st.pyplot(fig)
