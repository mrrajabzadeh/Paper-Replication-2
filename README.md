# Mood Beta and Seasonalities in Stock Returns: Table 1 Replication

This repository contains the Python code for replicating Table 1 of the paper "Mood Beta and Seasonalities in Stock Returns" by David Hirshleifer, Danling Jiang, and Yuting Meng DiGiovanni. The paper, published in the Journal of Financial Economics in July 2020, explores the relationship between investor mood variability and stock market returns.

## Project Description

The replication focuses on assessing seasonal mood effects on stock returns using data from the CRSP database. This involves examining the seasonality in stock returns and how they might correlate with investor mood variations throughout the year.

## Key Features

- **Data Extraction**: Utilizes WRDS to fetch detailed monthly stock return data from the CRSP database.
- **Statistical Analysis**: Employs descriptive statistical methods to analyze the returns data, focusing on months identified in previous studies as having significant investor mood variations.
- **Seasonal Analysis**: Identifies and analyzes the returns during specific months to understand the mood-related seasonality in stock market behavior.

## Requirements

To run this code, you'll need:
- Python 3.x
- pandas
- numpy
- matplotlib
- statsmodels
- wrds
- linearmodels

## Usage

1. **Configuration**: Setup your environment with the required Python libraries and access credentials for the WRDS database.
2. **Execution**: Run the script to perform data fetching, processing, and execute the analytical steps.
3. **Output**: Review the outputs which include statistical summaries and comparisons of stock returns in specified mood-sensitive months.

## File Descriptions

- **`mood_beta_seasonality_table1.py`**: Contains all the necessary code for the data processing and analysis for replicating Table 1 from the study.

## Contributing

Feel free to fork this repository, make changes, and submit pull requests if you have suggestions or improvements.

## License

This project is open-sourced under the MIT License.

## Acknowledgments

This project was inspired by the insightful analysis conducted by David Hirshleifer, Danling Jiang, and Yuting Meng DiGiovanni on the impact of mood variations on the financial market.




# Mood Beta and Seasonalities in Stock Returns: Table 2 Replication

This repository contains the Python code for replicating Table 2 of the paper "Mood Beta and Seasonalities in Stock Returns" by David Hirshleifer, Danling Jiang, and Yuting Meng DiGiovanni. The study, published in the Journal of Financial Economics in July 2020, explores the impact of mood beta and seasonal patterns on stock returns.

## Project Description

The replication focuses on the application of Fama-MacBeth regression analysis to investigate the predictability of returns based on mood-driven seasonal variations. The dataset includes monthly-level stock return data from the CRSP database and Fama-French factors.

## Key Features

- **Data Extraction**: Retrieves detailed monthly stock return data and associated characteristics from the CRSP database using WRDS.
- **Data Preparation**: Filters and processes the dataset to focus on common stocks traded on NYSE, AMEX, and NASDAQ.
- **Statistical Analysis**: Conducts regressions to analyze the mood congruence and reversal effects on stock returns.

## Requirements

To run this code, ensure the following dependencies are installed:
- Python 3.x
- pandas
- numpy
- matplotlib
- statsmodels
- wrds
- linearmodels

## Usage

1. **Configuration**: Set up your environment with the necessary Python libraries and ensure access to the WRDS database.
2. **Execution**: Run the script to fetch data, perform data processing, and execute the regression analyses.
3. **Output**: Review the output from the Fama-MacBeth regressions to analyze the mood beta and seasonal effects.

## File Descriptions

- **`mood_beta_seasonality_table2.py`**: Contains all the code necessary for the replication of Table 2 from the aforementioned study.

## Contributing

Contributions to this replication project are welcome. Please fork the repository, make your suggested changes, and submit a pull request for review.

## License

This project is open-sourced under the MIT License.

## Acknowledgments

This replication effort was inspired by the work of David Hirshleifer, Danling Jiang, and Yuting Meng DiGiovanni in their exploration of mood beta in financial markets.


