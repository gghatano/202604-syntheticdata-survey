# Datasets

## Adult (UCI)

Source: https://archive.ics.uci.edu/dataset/2/adult

Place the CSV at:

```
experiments/shared/data/raw/adult.csv
```

Expected columns (header row required, or `preprocessing.load_raw` will rename the 15 columns to the canonical Adult schema):

```
age, workclass, fnlwgt, education, education-num, marital-status,
occupation, relationship, race, sex, capital-gain, capital-loss,
hours-per-week, native-country, income
```

Missing values must be encoded as `?` (UCI default); `load_raw` converts them via `na_values=['?']`.

### Fetch manually

1. Download `adult.data` and `adult.names` from UCI.
2. Add the header row listed above.
3. Save as `adult.csv` under `experiments/shared/data/raw/`.

No automated fetcher is provided because the runtime has no network access.
