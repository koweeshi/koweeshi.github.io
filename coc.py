import requests
import pandas as pd
from datetime import date, datetime
import os
import numpy as np
import time
import json

# API_KEY = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6IjgwZjU1YmQ3LTliMzMtNDA1YS1iMWM0LTUzMDM2NDA1YThjMiIsImlhdCI6MTY5NjI5NjkzOCwic3ViIjoiZGV2ZWxvcGVyL2ZkNTIzYmZhLTQyZDEtOWU1OC05OWJhLWI2MTQ2YmYyZGNmZCIsInNjb3BlcyI6WyJjbGFzaCJdLCJsaW1pdHMiOlt7InRpZXIiOiJkZXZlbG9wZXIvc2lsdmVyIiwidHlwZSI6InRocm90dGxpbmcifSx7ImNpZHJzIjpbIjI3LjU0LjU5LjE0Il0sInR5cGUiOiJjbGllbnQifV19.VZNruIGMPXpT7tB-9_15-IRLmLiq4hKxZjpJFQXlrh-grzXTOzjJSN8Kenx72qRVZlfJxd2VJsM9V5OQmQI8ug'

# "Home Key"
API_KEY ='eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6ImVkZGNlNmEzLWExYmMtNDVjYi04NjUxLWRmYWVhMGMzYzkwMiIsImlhdCI6MTY5NjE2NzE5Miwic3ViIjoiZGV2ZWxvcGVyL2ZkNTIzYmZhLTQyZDEtOWU1OC05OWJhLWI2MTQ2YmYyZGNmZCIsInNjb3BlcyI6WyJjbGFzaCJdLCJsaW1pdHMiOlt7InRpZXIiOiJkZXZlbG9wZXIvc2lsdmVyIiwidHlwZSI6InRocm90dGxpbmcifSx7ImNpZHJzIjpbIjExNS42Ni4xNzEuMzIiXSwidHlwZSI6ImNsaWVudCJ9XX0._iPGDZXfKStoBH0rDZpn9039OZqr2WRpQVJR2Y0XWgiv84cdvB0hPG2dzTQ593r9rM0OlPuWAcSKZ2MaUyBZTA'

headers = {
    'Authorization': f'Bearer {API_KEY}'
}

CLAN_TAG = '2G9LC8JLG'

MONTH = date.today().strftime("%b-%Y")

# Get the current cwl rounds war tags
def get_cwl_clans():
    while True:
        try:
            response = requests.get(f'https://api.clashofclans.com/v1/clans/%23{CLAN_TAG}/currentwar/leaguegroup', headers = headers)
            response.raise_for_status()
            clan_data = response.json()
            rounds = []
            for round in clan_data.get('rounds',[]):
                if round['warTags'] != ['#0', '#0', '#0', '#0']:
                    rounds.append(round['warTags'])
            print(f'{len(rounds)} rounds retrieved')
            break
        
        except requests.exceptions.HTTPError as e:
            # Print the exception message when the status code is not in the 200-299 range
            print(f"HTTP error occurred: {e}")
            # print(response.json())
        
        except Exception as e:
            print(f'An error has occured: {e}')
        
        time.sleep(300)

    return rounds

# Get the data for each round
def get_round_matchup(rounds, month):
  round_no = 0
  for round in rounds:
    round_no += 1
    for matchup in round:
        war_tag = matchup[1:]

        while True:
            try:
                response = requests.get(f'https://api.clashofclans.com/v1/clanwarleagues/wars/%23{war_tag}', headers = headers)
                response.raise_for_status()
                war = response.json()
                
                break
            
            except requests.exceptions.HTTPError as e:
                # Print the exception message when the status code is not in the 200-299 range
                print(f"HTTP error occurred: {e}")
                # print(response.json())
            
            except Exception as e:
                print(f'An error has occured: {e}')
            
            time.sleep(300)
        
        # Determine which data belongs to which clan
        clan1 = war.get('clan', [])
        clan2 = war.get('opponent', [])
        if clan1['name'] != 'GianMarco Army':
            if clan2['name'] != 'GianMarco Army':
                continue
        if clan1['name'] == 'GianMarco Army':
            our_clan = clan1
            enemy_clan = clan2
        else:
            our_clan = clan2
            enemy_clan = clan1

        # If the first round is preparation stage, flag as false to avoid score calculation
        if war.get('state') == 'preparation':
            if round_no == 1:
                return False, False
            else:
                continue
        
        # If war has ended skip data storage
        if war.get('state') == 'warEnded':
            print(f'Round {round_no} ended')
            if not os.path.exists(f'data/{month}_round{round_no}.csv'):
                pass

            else:
                if round_no < 7:
                    continue


        # Storing our clan's data
        clan_data = []
        our_columns = ['Position','Tag', 'Name', 'Townhall','Stars','Percentage','Opponent']
        for member in our_clan['members']:
            name = member['name']
            tag = member['tag']
            townhall = member['townhallLevel']
            position = member['mapPosition']
            stars, percentage, opponent = store_attacks(member)
            clan_data.append((position, tag, name, townhall, stars, percentage, opponent))
        our_clan = pd.DataFrame(clan_data, columns = our_columns).sort_values('Position', ignore_index=True)

        # Enemy clan data
        clan_data = []
        enemy_columns = ['Position','Tag', 'Name', 'Townhall']
        for member in enemy_clan['members']:
            name = member['name']
            tag = member['tag']
            townhall = member['townhallLevel']
            position = member['mapPosition']
            clan_data.append((position,tag, name, townhall))
        enemy_clan = pd.DataFrame(clan_data, columns = enemy_columns).sort_values('Position', ignore_index=True)

        clans = pd.concat([our_clan, enemy_clan], axis = 1)
        filename = f'data/{month}_round{round_no}.csv'
        clans.to_csv(filename, index=False)
        print(f'Round {round_no} successfully saved at {filename}')

        if round_no == 7:
            print('CWL has ended')
            return True, True

  return True, False

# Function to store the member's attack
def store_attacks(member):
    attack = member.get('attacks')
    if attack:
        stars = attack[0]['stars']
        percentage = attack[0]['destructionPercentage']
        opponent = attack[0]['defenderTag']
    else:
        stars = 0
        percentage = 0
        opponent = None
    
    return stars, percentage, opponent

# Create base csv for clan data
def get_clan_data(month):
    filename = f'data/BASE_{month}_Summary.csv'
    if not os.path.exists(filename):
        print(f'Creating base csv for clan data at {filename}')
        while True:
            try:
                response = requests.get(f'https://api.clashofclans.com/v1/clans/%23{CLAN_TAG}', headers = headers)
                response.raise_for_status()
                clan_data = response.json()
                break     
            
            except requests.exceptions.HTTPError as e:
                # Print the exception message when the status code is not in the 200-299 range
                print(f"HTTP error occurred: {e}")
                # print(response.json())
            
            except Exception as e:
                print(f'An error has occured: {e}')
            
            time.sleep(300)
        
        data = []
        columns = ['Tag', 'Name', 'Total Stars', 'Total Percentage', 'Bonus Awarded', 'Demerit', 'Attacks']
        attacks = []

        for member in clan_data.get('memberList', []):
            tag = member['tag']
            name = member['name']
            total_stars = 0
            total_percent = 0
            bonus = 0
            demerit = 0
            attacks = 0
            data.append((tag, name, total_stars, total_percent, bonus, demerit, attacks))
        clan_data = pd.DataFrame(data, columns=columns)
        
        clan_data.to_csv(filename, index=False)
        print(f'Clan data successfully retrieved and saved at {filename}')
    
    else:
        print(f'Base file exists at {filename}')

def create_json():
    directory = 'data'
    
    try:
        filename = os.path.join(directory, f'BASE_{MONTH}_Summary.csv')
        summary = pd.read_csv(filename)
        print(f'File {filename} opened successfully')

    except Exception as e:
        print(f'An error has occured: {e}')

    template = {
        'Attack 1': [],
        'Attack 2': [],
        'Attack 3': [],
        'Attack 4': [],
        'Attack 5': [],
        'Attack 6': [],
        'Attack 7': []
    }
    data = {}
    for _, member in summary.iterrows():
        name = member['Name']
        data[f'{name}'] = template
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Calculate score for each member each round
def calculate_score():
    directory = 'data'
    
    try:
        filename = os.path.join(directory, f'BASE_{MONTH}_Summary.csv')
        summary = pd.read_csv(filename)
        print(f'File {filename} opened successfully')
    
    except Exception as e:
        print(f'An error has occured: {e}')
    
    try:
        filename = 'data.json'
        with open('data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f'File {filename} opened successfully')
    
    except Exception as e:
        print(f'An error has occured: {e}')

    round = 0
    for file in os.listdir(directory):
        filename = os.path.join(directory, file)

        if not file.endswith('.csv'):
            continue
        elif file[:8] != MONTH:
            continue

        try:
            round_data = pd.read_csv(filename)
            print(f'File {file} opened successfully')
            
        except Exception as e:
            print(f'An error has occured: {e}')
        
        round += 1
        
        for _, member in round_data.iterrows():
            name = member['Name']
            tag = member['Tag']
            stars = member['Stars']
            townhall = member['Townhall']
            percentage = member['Percentage']
            opponent = member['Opponent']
            
            if type(opponent) == str:
                opp_th = round_data.loc[round_data['Tag.1']==opponent, 'Townhall.1'].values[0]
            else:
                opp_th = None

            if opp_th:
                bonus = 0
                demerit = 0

                if opp_th > townhall and stars >= 1:
                    bonus += 1
                elif opp_th < townhall and stars < 3:
                    demerit += 1

                # Create a new player_data dictionary for each player
                player_data = {}
                
                # Store number of attacks
                num_attack = summary.loc[summary['Tag']==tag, 'Attacks'].values[0]
                new_attack = num_attack + 1
                summary.loc[summary['Tag']==tag, 'Attacks'] = new_attack

                # Retrieve current values
                current_stars = summary.loc[summary['Tag']==tag, 'Total Stars'].values[0]
                current_percentage = summary.loc[summary['Tag']==tag, 'Total Percentage'].values[0]
                current_bonus = summary.loc[summary['Tag']==tag, 'Bonus Awarded'].values[0]
                current_demerit = summary.loc[summary['Tag']==tag, 'Demerit'].values[0]

                # Store attacks into player_data
                attack = {}
                attack['Stars'] = str(stars)
                attack['Percentage'] = str(percentage)
                attack['Opp Townhall'] = str(opp_th)
                player_data[f'Attack {round}'] = attack

                # Add player_data to the data dictionary with the player's name as the key
                data[f'{name}'][f'Attack {round}'] = player_data

                # Replace with new values
                stars = stars + bonus - demerit
                new_stars = stars + current_stars
                new_percentage = percentage + current_percentage
                new_bonus = bonus + current_bonus
                new_demerit = demerit + current_demerit

                summary.loc[summary['Tag']==tag, 'Total Stars'] = new_stars
                summary.loc[summary['Tag']==tag, 'Total Percentage'] = new_percentage
                summary.loc[summary['Tag']==tag, 'Bonus Awarded'] = new_bonus
                summary.loc[summary['Tag']==tag, 'Demerit'] = new_demerit
                
    merge = []
    round = [round for i in range(0,len(summary)+1)]
    position = np.arange(1,len(summary)+1,1,dtype=int).tolist()
    for i in range(len(round)-1):
        merge.append((round[i],position[i]))
    merge = pd.DataFrame(merge, columns=['Round','Position'])
    summary = summary.sort_values(by=['Total Stars', 'Total Percentage'], ascending=False, ignore_index=True)
    summary = pd.concat([merge, summary],axis=1)
    update = datetime.now().strftime("%H:%M %d-%b-%Y")
    summary['Update'] = update
    summary.to_csv(f'{MONTH}_Summary.csv', index=False)
    # summary.to_csv(f'C:/Users/Khosy/Documents/coc_cwl_scoreboard/{MONTH}_Summary.csv', index=False)
    # summary.to_csv(f'/media/mind04/E98B-58F3/coc_cwl_scoreboard/{MONTH}_Summary.csv', index=False)
    summary.to_csv(f'e:/coc_cwl_scoreboard/{MONTH}_Summary.csv', index=False)
    print(f'File {MONTH}_Summary.csv has been updated')
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# rounds = get_cwl_clans()
# flag = get_round_matchup(rounds, MONTH)
# # if not os.path.exists(f'{MONTH}_Summary.csv'):
# #     get_clan_data(MONTH)
# get_clan_data(MONTH)
# if flag:
#     calculate_score()
# create_json()
# calculate_score()