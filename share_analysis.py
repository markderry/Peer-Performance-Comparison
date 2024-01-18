import pandas as pd
import yfinance as yf

# Define the list of ticker symbols
tickerSymbols = [
    'CVE',
    'APA',
    'DVN',
    'BP',
    'HES',
    'CNQ.TO',
    'IMO.TO',
    'CVX',
    'OVV',
    'COP',
    'SU.TO'
]

# Initialize a DataFrame to store all the historical data
priceData = pd.DataFrame()
dividendData = pd.DataFrame()

for tickerSymbol in tickerSymbols:
    # Get the data for the stock
    tickerData = yf.Ticker(tickerSymbol)

    # Get the historical prices for this ticker
    tickerDf = tickerData.history(period='1d', start='2020-01-01', end='2023-12-31')
    tickerDf['Symbol'] = tickerSymbol

    # Append the data to the priceData DataFrame
    priceData = pd.concat([priceData, tickerDf])

    # Get the dividend data for the stock
    tickerDividend = pd.DataFrame(tickerData.dividends)
    tickerDividend['Symbol'] = tickerSymbol
    dividendData = pd.concat([dividendData, tickerDividend])
    
# Truncate the index to remove the time
# Reset the index and make it a column
priceData = priceData.reset_index()
dividendData = dividendData.reset_index()

# Convert the 'Date' column to string
priceData['Date'] = priceData['Date'].astype(str)
dividendData['Date'] = dividendData['Date'].astype(str)

# Truncate the 'Date' column to only include the date (first 10 characters)
priceData['Date'] = priceData['Date'].str.slice(0, 10)
dividendData['Date'] = dividendData['Date'].str.slice(0, 10)

# Convert the 'Date' column to datetime
priceData['Date'] = pd.to_datetime(priceData['Date'])
dividendData['Date'] = pd.to_datetime(dividendData['Date'])

### 2023 Calcualtions ###
# Filter the price data to the first 30 days before the period
first_30 = priceData.loc[(priceData['Date'] >= '2022-12-01') & (priceData['Date'] <= '2022-12-31')]
# Filter the price data to the last 30 days of the period
last_30 = priceData.loc[(priceData['Date'] >= '2023-12-01') & (priceData['Date'] <= '2023-12-31')]

# Calculate the average closing price for the first 30 days
first_30_avg = first_30.groupby(['Symbol'])['Close'].mean()
last_30_avg = last_30.groupby(['Symbol'])['Close'].mean()

# Combine the average data frames into a single data frame
avg_data = pd.concat([first_30_avg, last_30_avg], axis=1)

# Rename the columns
avg_data.columns = ['First 30 Avg', 'Last 30 Avg']

# Filter the dividend data to the 2023 dividends
divs = dividendData.loc[(dividendData['Date'] >= '2023-01-01') & (dividendData['Date'] <= '2023-12-31')]
divs = divs.groupby(['Symbol'])['Dividends'].sum()

p_23 = pd.concat([avg_data, divs], axis=1)
p_23['TSR'] = (p_23['Last 30 Avg'] - p_23['First 30 Avg'] + p_23['Dividends'])/p_23['First 30 Avg']

### 2021-2023 Calcualtions ###
# Filter the price data to the first and last
first_30 = priceData.loc[(priceData['Date'] >= '2020-12-01') & (priceData['Date'] <= '2020-12-31')]
last_30 = priceData.loc[(priceData['Date'] >= '2023-12-01') & (priceData['Date'] <= '2023-12-31')]

# Calculate the average closing price for the first 30 days
first_30_avg = first_30.groupby(['Symbol'])['Close'].mean()
last_30_avg = last_30.groupby(['Symbol'])['Close'].mean()
avg_data = pd.concat([first_30_avg, last_30_avg], axis=1)
avg_data.columns = ['First 30 Avg', 'Last 30 Avg']

# Filter the dividend data to the dividends 2021-2023
divs = dividendData.loc[(dividendData['Date'] >= '2021-01-01') & (dividendData['Date'] <= '2023-12-31')]
divs = divs.groupby(['Symbol'])['Dividends'].sum()

p_all = pd.concat([avg_data, divs], axis=1)
p_all['TSR'] = (p_all['Last 30 Avg'] - p_all['First 30 Avg'] + p_all['Dividends'])/p_all['First 30 Avg']

# Calculate the percentile rank of 'TSR' for p_all
p_all['TSR_Percentile'] = p_all['TSR'].rank(pct=True)

# Calculate the percentile rank of 'TSR' for p_23
p_23['TSR_Percentile'] = p_23['TSR'].rank(pct=True)

# See your data
print(p_all.head())
print(p_23.head())

# 25 percentile or greater but less than 50 percentile	0.25
# 50 percentile or greater but less than 90 percentile	1.0
# 90 percentile or greater	2.0
# Between the 25th and 90th percentile, the score will be interpolated
def interpolate_tsr_score(x):
    if x < 0.25:
        return 0.0
    elif 0.25 <= x < 0.5:
        # Linear interpolation between 0.25 and 1.0
        return 0.25 + ((x - 0.25) * (1.0 - 0.25)) / (0.5 - 0.25)
    elif 0.5 <= x < 0.9:
        # Linear interpolation between 1 and 2
        return 1.0 + ((x - 0.5) * (2.0 - 1.0)) / (0.9 - 0.5)
    else:
        return 2.0

pm_21_23 = p_all.loc[(p_all.index == 'CVE')]['TSR_Percentile'].apply(interpolate_tsr_score)
pm_23 = p_23.loc[(p_23.index == 'CVE')]['TSR_Percentile'].apply(interpolate_tsr_score)
pm_22 = 1.6
pm_21 = 1.84
total_performance_mult = pm_21_23 *0.7 + pm_23 *0.1 + pm_22*0.1 + pm_21*0.1
