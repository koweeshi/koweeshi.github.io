import pandas as pd
from flask import Flask, render_template
import coc
from datetime import datetime
import time
import threading
import os

app = Flask(__name__)
app.config['STATIC_FOLDER'] = 'static'

def refresh():
    time.sleep(30)
    while True:
        print('Retrieving data...')
        rounds = coc.get_cwl_clans()
        coc.get_round_matchup(rounds, coc.MONTH)
        coc.get_clan_data(coc.MONTH)
        coc.calculate_score()
        df = pd.read_csv(f"{coc.MONTH}_Summary.csv")
        print('Data refreshed')
        last = datetime.now().strftime('%c')
        print(f'Last Update: {last}')
        time.sleep(1800)

refresh_thread = threading.Thread(target=refresh)
refresh_thread.daemon = True
refresh_thread.start()

@app.route('/') 
def scoreboard():
    df = pd.read_csv(f"{coc.MONTH}_Summary.csv")
    limited_data = df.head(10).to_dict(orient='records')  # First 15 rows
    full_data = df.to_dict(orient='records')  # All rows
    return render_template('scoreboard.html', limited_data=limited_data, full_data=full_data)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5500, threaded = True)