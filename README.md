# Slay the Spire run data

Repo containing run history data for [vmService](https://www.twitch.tv/vmservice),
and other streamers (with permissions).
And the associated code used to generate the reports.

TL;DR: If you are only looking for the run history data, see [Data sets](#data-sets).

Otherwise, you can use the code provided to generate similar reports on your own run history files.

## Data sets

- [200 run rotating sample](./results/200-rotating-sample)
- [Lose all gold for max HP sample](./results/lose-all-gold-max-hp-sample)
- [50 games of Bad Silent](./results/bad-silent)
- [panacea108](https://www.twitch.tv/panacea108) [Ironclad Sample](./results/panacea-ironclad-sample)
- [Robit (50 Defect runs)](./results/robit)

## How to use on your own run history files

### Requirements

- Python 3.10
- [Run history plus](https://steamcommunity.com/sharedfiles/filedetails/?id=2802958032) (might work
  without, untested)

### Instructions

```shell
# Create a Python virtual environment (only needed to do this once)
python -m venv venv

# Activate the venv (need to do every time)
source ./venv/bin/activate

# Install dependencies (only need to to this once)
pip install -U pip
pip install poetry
poetry install

# View Program help text (optional)
python analyze/analyze.py  --help

# Example usage
python analyze/analyze.py <path to run history folder> <path to results output folder>
```
