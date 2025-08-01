import pandas as pd
import re
import requests
from bs4 import BeautifulSoup

# Load data
merged_df = pd.read_excel(r'C:\Users\mnguyen\Downloads\columns_removed_DIGITIZED-LEGAL-COMPENDIUM-V2019.xlsx')
unmatched_df = pd.read_excel(r'C:\Users\mnguyen\Downloads\Unmatched Section List(Statute_text).xlsx')

# --- Extract section code and subsection from merged file ---
def extract_section_and_subsection(s):
    if pd.isna(s):
        return None, None
    # E.g., "{SS}: 13A-9-71(f)(4)" --> ("13A-9-71", "(f)(4)")
    match = re.match(r"\{SS\}:\s*([\dA-Za-z\-\.\:]+)(\([^)]+\))?", str(s))
    if match:
        section = match.group(1)
        subsection = match.group(2) if match.lastindex > 1 else None
        return section, subsection
    # Fallback: Just extract a main code
    main_match = re.search(r'([\dA-Za-z\-\.\:]+)', str(s))
    return (main_match.group(1), None) if main_match else (None, None)

merged_df[['section_code', 'section_subsection']] = merged_df['statute_section'].apply(
    lambda s: pd.Series(extract_section_and_subsection(s))
)

# Prepare lookup for unmatched
unmatched_df['Subsection'] = unmatched_df['Subsection'].fillna("").astype(str).str.replace(" ", "")
unmatched_df['Primary Section'] = unmatched_df['Primary Section'].astype(str)

# --- Custom function to find statute text ---
def get_statute_text(row):
    code = row['section_code']
    subsection = row['section_subsection']
    
    # 1. Exact match: section and subsection
    m = unmatched_df[
        (unmatched_df['Primary Section'] == code) &
        (unmatched_df['Subsection'].str.contains(subsection.replace(" ", "") if subsection else "", na=False))
    ]
    if not m.empty:
        return m.iloc[0]['Statute Text']

    # 2. Fallback: Only section match (ignore subsection)
    m = unmatched_df[unmatched_df['Primary Section'] == code]
    if not m.empty:
        # Try to extract only the relevant subsection if possible
        statute_text = m.iloc[0]['Statute Text']
        # If subsection requested, extract from the statute text
        if subsection:
            sub_pattern = re.escape(subsection)
            # Find the subsection text, from the start of the match to the next subsection or end of text
            match = re.search(rf'({sub_pattern})(.*?)(?=\(\w+\)|$)', statute_text, re.DOTALL)
            if match:
                return match.group(0).strip()
        return statute_text

    # 3. No match in Excel: Try to fetch from Source URL
    m = unmatched_df[unmatched_df['Primary Section'] == code]
    if not m.empty and 'Source' in m.columns:
        url = m.iloc[0]['Source']
        try:
            resp = requests.get(url, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            # Try to get the main content block, e.g. for Justia law
            text = soup.get_text(separator="\n")
            # Heuristic: Grab everything after "Section <section_code>" for that section
            pattern = rf"Section {re.escape(code)}(.*?)(?=Section|\Z)"
            section_match = re.search(pattern, text, re.DOTALL)
            if section_match:
                text_block = section_match.group(0).strip()
                # If subsection requested, extract only that
                if subsection:
                    sub_match = re.search(rf'({re.escape(subsection)}.*?)(?=\(\w+\)|$)', text_block, re.DOTALL)
                    if sub_match:
                        return sub_match.group(0).strip()
                return text_block
        except Exception as e:
            print(f"Could not fetch from {url}: {e}")
    return None

# --- Main logic: Update statute_text where missing ---
merged_df['statute_text'] = merged_df.apply(
    lambda row: get_statute_text(row) if pd.isna(row['statute_text']) or not row['statute_text'] else row['statute_text'],
    axis=1
)

# Save output
merged_df.drop(columns=['section_code', 'section_subsection'], inplace=True)
merged_df.to_excel(r'C:\Users\mnguyen\Downloads\columns_merged_DIGITIZED-LEGAL-COMPENDIUM-V2019.xlsx', index=False)
