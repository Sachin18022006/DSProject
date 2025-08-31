import streamlit as st
from PIL import Image
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import base64
from bs4 import BeautifulSoup
import requests
import json
from cryptocmd import CmcScraper
import datetime as dt


# Set Page to expand to full width
st.set_page_config(layout="wide")

# Image
image = Image.open('logo.png')
st.image(image, width=500)

# Title
st.title('Crypto Web App')
st.markdown("""
This app retrieves prices along with other information regarding different cryptocurrencies from **CoinMarketCap**!
""")

# About
expander_bar = st.expander('About')
expander_bar.markdown("""
* **Made By:** <Your Name>
* **Data source:** [CoinMarketCap](http://coinmarketcap.com).
* **Credit:** Web scraper adapted from the Medium article *[Web Scraping Crypto Prices With Python](https://towardsdatascience.com/web-scraping-crypto-prices-with-python-41072ea5b5bf)* written by [Bryan Feng](https://medium.com/@bryanf).
""")

# Divide Page into columns
col1 = st.sidebar
col2, col3 = st.columns((1,1))

col1.header('Input Options')

## Sidebar - Select currency price unit
currency_price_unit = col1.selectbox('Select currency for price',
                                     ('USD', 'BTC'))

#---------------------------------#

def load_data():
    cmc = requests.get('https://coinmarketcap.com')
    soup = BeautifulSoup(cmc.content, 'html.parser')

    data = soup.find('script', id='__NEXT_DATA__', type='application/json')
    coin_data = json.loads(data.contents[0])

    global_metrics = coin_data['props']['pageProps']['globalMetrics']
    total_marketcap = global_metrics['marketCap']
    btc_market_share = global_metrics['btcDominance']
    eth_market_share = global_metrics['ethDominance']

    initialState = coin_data['props']['initialState']
    latest_listing_data = json.loads(initialState)['cryptocurrency']['listingLatest']['data']
    
    
    keysArr = latest_listing_data[0]['keysArr']
    listings = latest_listing_data[1:]

    query = 'quote.' + currency_price_unit + '.'

    coin_name = []
    coin_symbol = []
    market_cap = []
    percent_change_1h = []
    percent_change_24h = []
    percent_change_7d = []
    price = []
    volume_24h = []

    for i in listings:

      i = {key : value for key, value in zip(keysArr, i)}

      coin_name.append(i['slug'])
      coin_symbol.append(i['symbol'])
      price.append(i[query+'price'])
      percent_change_1h.append(i[query+'percentChange1h'])
      percent_change_24h.append(i[query+'percentChange24h'])
      percent_change_7d.append(i[query+'percentChange7d'])
      market_cap.append(i[query+'marketCap'])
      volume_24h.append(i[query+'volume24h'])

    df = pd.DataFrame(columns=['coin_name', 'coin_symbol', 'market_cap', 'percent_change_1h', 'percent_change_24h', 'percent_change_7d', 'price', 'volume_24h'])
    df['coin_name'] = coin_name
    df['coin_symbol'] = coin_symbol
    df['price'] = price
    df['percent_change_1h'] = percent_change_1h
    df['percent_change_24h'] = percent_change_24h
    df['percent_change_7d'] = percent_change_7d
    df['market_cap'] = market_cap
    df['volume_24h'] = volume_24h

    return df, total_marketcap, btc_market_share, eth_market_share

df, total_marketcap, btc_market_share, eth_market_share = load_data()

#---------------------------------#

# Sidebar - Select cryptocurrencies
sorted_coin = sorted(df['coin_symbol'])
selected_coin = col1.multiselect('Cryptocurrency', sorted_coin,
                                 ['BTC', 'ETH', 'ADA', 'DOGE', 'BNB'])

# Filtering data
selected_coin_df = df[(df['coin_symbol'].isin(selected_coin))] 

# Sidebar - Select Percent change timeframe
percent_timeframe = col1.selectbox('Percent change time frame',
                                   ['7d','24h', '1h'])

#---------------------------------#

percent_dict = {"7d":'percent_change_7d',
                "24h":'percent_change_24h',
                "1h":'percent_change_1h'}
selected_percent_timeframe = percent_dict[percent_timeframe]

# Preparing data for plotting
top_5_positive_change = df.nlargest(5, selected_percent_timeframe)
top_5_negative_change = df.nsmallest(5, selected_percent_timeframe)

positive_change_selected_coins = \
    selected_coin_df[selected_coin_df[selected_percent_timeframe] > 0]
negative_change_selected_coins = \
    selected_coin_df[selected_coin_df[selected_percent_timeframe] < 0]

bar_chart_df = pd.concat([top_5_positive_change,
                         positive_change_selected_coins,
                         top_5_negative_change,
                         negative_change_selected_coins], axis=0)
bar_chart_df['positive_percent_change'] = \
    bar_chart_df[selected_percent_timeframe] > 0

# Heading for Horizontal Bar Chart
col2.subheader(f'Bar plot of % Price Change')
col2.write(f'*Last {percent_timeframe} period*')

# Plotting Horizontal Bar Chart
plt.style.use('seaborn')

fig, ax = plt.subplots()
ax.barh(bar_chart_df['coin_symbol'],
        bar_chart_df[selected_percent_timeframe], 
        color=bar_chart_df.positive_percent_change\
        .map({True: 'lightblue', False: 'pink'}))

ax.set_xlabel('Percent Change', fontsize=17, labelpad=15)
ax.tick_params(axis='both', labelsize=13)

fig.tight_layout()

# Display figure
col2.pyplot(fig)

#---------------------------------#

def get_unit(max_market_cap):
  
  unit = 'less than ten million'
  number_of_digits = len(str(int(max_market_cap)))

  if number_of_digits == 8:
    unit = 'tens of millions'
  elif number_of_digits == 9:
    unit = 'hundreds of millions'
  elif number_of_digits == 10:
    unit = 'billions'
  elif number_of_digits == 11:
    unit = 'tens of billions'
  elif number_of_digits == 12:
    unit = 'hundreds of billions'
  
  return unit

# Heading for Bar Chart
col3.subheader(f'Bar plot of Market Cap (Selected Cryptos)')
col3.write(f'*Last {percent_timeframe} period*')

# Plotting Bar Chart
fig, ax = plt.subplots()
ax.bar(selected_coin_df['coin_symbol'],
        selected_coin_df['market_cap'])
ax.tick_params(axis='both', labelsize=15)

# Increasing size of exponenet
exponent = ax.yaxis.get_offset_text()
exponent.set_size(16)

# Changing y-axis label based on the number of digits
max_market_cap = selected_coin_df['market_cap'].max()
unit = get_unit(max_market_cap)
if unit == 'less than ten million':
    ax.set_ylabel(f'Market Cap', fontsize=15, labelpad=15)
else:
    ax.set_ylabel(f'Market Cap ({unit})', fontsize=15, labelpad=15)

fig.tight_layout()

# Display figure
col3.pyplot(fig)

#---------------------------------#

col2.markdown("""
_________________________
""")

# Heading for Pie Chart
col2.header('**Market Share of Cryptos**')

# Preparing data for plotting
alt_coins_market_share = 100 - (btc_market_share + eth_market_share)

percentages = [btc_market_share, eth_market_share, alt_coins_market_share]
labels = ['Bitcoin', 'Ethereum', 'Alt Coins']

# Plot Pie Chart
fig, ax = plt.subplots()
colors = ['#80dfff', 'pink', '#ffe699']
ax.pie(percentages, labels=labels, colors=colors, autopct='%.1f%%')
plt.legend(loc="upper right", bbox_to_anchor=(1.2, 1), fontsize=10)

# Display figure
col2.pyplot(fig)

#---------------------------------#

col3.markdown("""
_________________________
""")

# Getting Historical Time Series Data
# Using cryptocmd - Cryptocurrency historical market price data scrapper
@st.cache(max_entries=25, ttl=86400)
def get_historical_time_series_data(crypto_symbol, startdate, endate):

  # initialise scraper with time interval
  scraper = CmcScraper(crypto_symbol, startdate, endate)

  # get dataframe for the data
  historical_timeseries_df = scraper.get_dataframe()

  return historical_timeseries_df

# Select crypto
selected_crypto = col3.selectbox('Select crypto', (df['coin_symbol']))

# Heading for Line Graph
col3.header(f'{selected_crypto} over the last 30 days')

today = dt.date.today()
month_ago = today - dt.timedelta(days=30)

# Convert to '%d-%m-%Y' string format
today = today.strftime('%d-%m-%Y')
month_ago = month_ago.strftime('%d-%m-%Y')

historical_timeseries_df =\
   get_historical_time_series_data(selected_crypto, month_ago, today)         

# Plot Line Graph
fig, ax = plt.subplots()
ax.plot(historical_timeseries_df['Date'],
       historical_timeseries_df['Close'], color='green')

ax.set_xlabel('Date', fontsize=15, labelpad=13)
ax.set_ylabel('Closing Price ($)', fontsize=15, labelpad=15)
ax.tick_params(axis='x', rotation=45)

# Display figure
col3.pyplot(fig)

#---------------------------------#

col2.markdown("""
_________________________
""")

col2.header('**Tables**')

# Price Data Table

# Select columns
columns = ['coin_name', 'coin_symbol', 'market_cap', 'price', 'volume_24h']
selected_coin_price_info_df = selected_coin_df[columns]

col2.subheader('Price Data of Selected Cryptocurrencies')
col2.write(selected_coin_price_info_df)

# Download CSV data
# https://discuss.streamlit.io/t/how-to-download-file-in-streamlit/1806
def filedownload(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # strings <-> bytes conversions
    href = f'<a href="data:file/csv;base64,{b64}" download="crypto.csv">Download CSV File</a>'
    return href

col2.markdown(filedownload(selected_coin_price_info_df),
              unsafe_allow_html=True)

# Table of Percentage Change

# Drop columns not related to Percentage Change
selected_coin_percent_change_df =\
   selected_coin_df.drop(columns=['market_cap', 'price', 'volume_24h'])

col2.subheader('Percent Change Data of Select Cryptocurrencies')
col2.write(selected_coin_percent_change_df)
