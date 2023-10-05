import requests
import pandas as pd
from datetime import date
import os
import numpy as np

API_KEY = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6IjgwZjU1YmQ3LTliMzMtNDA1YS1iMWM0LTUzMDM2NDA1YThjMiIsImlhdCI6MTY5NjI5NjkzOCwic3ViIjoiZGV2ZWxvcGVyL2ZkNTIzYmZhLTQyZDEtOWU1OC05OWJhLWI2MTQ2YmYyZGNmZCIsInNjb3BlcyI6WyJjbGFzaCJdLCJsaW1pdHMiOlt7InRpZXIiOiJkZXZlbG9wZXIvc2lsdmVyIiwidHlwZSI6InRocm90dGxpbmcifSx7ImNpZHJzIjpbIjI3LjU0LjU5LjE0Il0sInR5cGUiOiJjbGllbnQifV19.VZNruIGMPXpT7tB-9_15-IRLmLiq4hKxZjpJFQXlrh-grzXTOzjJSN8Kenx72qRVZlfJxd2VJsM9V5OQmQI8ug'

headers = {
    'Authorization': f'Bearer {API_KEY}'
}

CLAN_TAG = '2G9LC8JLG'

MONTH = date.today().strftime("%b-%Y")

def get_cwl_clans():
  try:
    response = requests.get(f'https://api.clashofclans.com/v1/clans/%23{CLAN_TAG}/currentwar/leaguegroup', headers = headers)
    clan_data = response.json()
    rounds = []
    for round in clan_data.get('rounds',[]):
        if round['warTags'] != ['#0', '#0', '#0', '#0']:
            rounds.append(round['warTags'])
  except Exception as e:
      print(f'An error has occured: {e}')
  finally:
      print(f'{len(rounds)} rounds retrieved')
  return rounds

def get_round_matchup(rounds, month):
  round_no = 0
  for round in rounds:
    round_no += 1
    for matchup in round:
        war_tag = matchup[1:]
        try:
            response = requests.get(f'https://api.clashofclans.com/v1/clanwarleagues/wars/%23{war_tag}', headers = headers)
            war = response.json()
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
            if war.get('state') == 'preparation':
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
        
        except Exception as e:
            print(f'An error has occured: {e}')
  
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

def get_clan_data(month):
    try:
        response = requests.get(f'https://api.clashofclans.com/v1/clans/%23{CLAN_TAG}', headers = headers)
        clan_data = response.json()
        data = []
        columns = ['Tag', 'Name', 'Total Stars', 'Total Percentage', 'Bonus Awarded', 'Demerit']
        for member in clan_data.get('memberList', []):
            tag = member['tag']
            name = member['name']
            total_stars = 0
            total_percent = 0
            bonus = 0
            demerit = 0
            data.append((tag, name, total_stars, total_percent, bonus, demerit))
        clan_data = pd.DataFrame(data, columns=columns)
        filename = f'{month}_Summary.csv'
        clan_data.to_csv(filename, index=False)
        print(f'Clan data successfully retrieved and saved at {filename}')
        return clan_data
    except Exception as e:
        print(f'An error has occured: {e}')

def calculate_score():
    directory = 'data'
    
    try:
        summary = pd.read_csv(f'{MONTH}_Summary.csv')
        print(f'File {MONTH}_Summary.csv opened successfully')
    except Exception as e:
        print(f'An error has occured: {e}')

    round = 0
    for file in os.listdir(directory):
        filename = os.path.join(directory, file)
        if file == '.gitkeep':
            continue
        try:
            round_data = pd.read_csv(filename)
            print(f'File {file} opened successfully')
        except Exception as e:
            print(f'An error has occured: {e}')
        round += 1
        for _, member in round_data.iterrows():
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

                # Retrieve current values
                current_stars = summary.loc[summary['Tag']==tag, 'Total Stars'].values[0]
                current_percentage = summary.loc[summary['Tag']==tag, 'Total Percentage'].values[0]
                current_bonus = summary.loc[summary['Tag']==tag, 'Bonus Awarded'].values[0]
                current_demerit = summary.loc[summary['Tag']==tag, 'Demerit'].values[0]

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
    summary.to_csv(f'{MONTH}_Summary.csv', index=False)
    print(f'File {MONTH}_Summary.csv has been updated')


# rounds = get_cwl_clans()
# get_round_matchup(rounds, MONTH)
# get_clan_data(MONTH)
# calculate_score()
