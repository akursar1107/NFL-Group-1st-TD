import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from league_webapp.app.data_loader import load_data_with_cache_web
season = 2025
_, _, roster_df = load_data_with_cache_web(season, use_cache=True)
print('Columns:', roster_df.columns)
# Filter entries where first_name matches targets
targets = ['T.J.', 'Ladd']
for t in targets:
    try:
        mask = (roster_df['first_name'] == t) | (roster_df['full_name'] == t)
        subset = roster_df.filter(mask)
        print(f'--- Entries for {t} ({len(subset)} rows) ---')
        if len(subset):
            print(subset.select(['full_name','first_name','last_name','football_name']).head(10))
    except Exception as e:
        print(f'Error filtering for {t}: {e}')
# Also attempt fuzzy search for last names
try:
    mask_hock = roster_df['last_name'].str.contains('Hock', literal=True)
    subset_hock = roster_df.filter(mask_hock)
    print(f'--- Entries last_name contains Hock ({len(subset_hock)} rows) ---')
    print(subset_hock.select(['full_name','first_name','last_name']).head(10))
except Exception as e:
    print('Error searching Hock:', e)
try:
    mask_ladd = roster_df['first_name'] == 'Ladd'
    subset_ladd = roster_df.filter(mask_ladd)
    print(f'--- Entries first_name=Ladd ({len(subset_ladd)} rows) ---')
    print(subset_ladd.select(['full_name','first_name','last_name']).head(10))
except Exception as e:
    print('Error searching Ladd:', e)
