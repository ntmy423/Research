import pandas as pd

# File paths
dig_path = r'C:\Users\mnguyen\Downloads\DIGITIZED-LEGAL-COMPENDIUM-V2019.xlsx'
unmatched_path = r'C:\Users\mnguyen\Downloads\Unmatched Section List(Statute_text).xlsx'

# Read in the files
dig = pd.read_excel(dig_path, sheet_name=0)
unmatched = pd.read_excel(unmatched_path, sheet_name=0)

# Improved function for multi-letter columns
def colname_from_letter(df, letter):
    letter = letter.upper()
    idx = 0
    for char in letter:
        idx = idx * 26 + (ord(char) - ord('A') + 1)
    return df.columns[idx - 1]  # zero-based

cols_to_keep = ['F', 'G', 'AK', 'AO']
dig_cols = [colname_from_letter(dig, c) for c in cols_to_keep]
dig_small = dig[dig_cols].copy()

dig_small = dig_small.merge(
    unmatched[['Primary Section', 'Statute Text']],
    left_on=colname_from_letter(dig, 'AK'),
    right_on='Primary Section',
    how='left'
)

ao_col = colname_from_letter(dig, 'AO')
dig_small[ao_col] = dig_small['Statute Text'].combine_first(dig_small[ao_col])

dig_small = dig_small.drop(['Primary Section', 'Statute Text'], axis=1)
dig_small.to_excel("columns_removed_DIGITIZED-LEGAL-COMPENDIUM-V2019.xlsx", index=False)
