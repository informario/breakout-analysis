# Switch Breakout

## Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```
## Add real prices
app/database/price_lookup.csv
## Run all cases
1. run app/scatter_conf_vs_price.ipynb
2. html file located in app/nokia_vs_arista_vs_cisco_comparison_standalone.html

## Run single case
1. Edit custom single case /app/generated_ports_custom.csv
2. run app/config_custom.ipynb
3. html file located in app/nokia_vs_arista_vs_cisco_comparison_custom.html