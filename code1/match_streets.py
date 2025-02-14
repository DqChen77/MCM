import pandas as pd
import re
from tqdm import tqdm
from difflib import get_close_matches

def standardize_street_name(name):
    if pd.isna(name):
        return ""
    
    # Convert to uppercase
    name = str(name).upper()
    
    # Common abbreviations mapping
    abbreviations = {
        'STREET': 'ST',
        'AVENUE': 'AVE',
        'ROAD': 'RD',
        'BOULEVARD': 'BLVD',
        'DRIVE': 'DR',
        'LANE': 'LA',
        'COURT': 'CT',
        'CIRCLE': 'CIR',
        'PLACE': 'PL',
        'HIGHWAY': 'HWY',
        'PARKWAY': 'PKWY',
        'NORTH': 'N',
        'SOUTH': 'S',
        'EAST': 'E',
        'WEST': 'W',
        'TERRACE': 'TER',
        'EXPRESSWAY': 'EXPY',
        'FREEWAY': 'FWY',
        'TURNPIKE': 'TPKE',
        'ROUTE': 'RT',
        'SQUARE': 'SQ',
        'TRAIL': 'TRL',
        'WAY': 'WY',
        'ALLEY': 'ALY',
        'NORTHEAST': 'NE',
        'NORTHWEST': 'NW',
        'SOUTHEAST': 'SE',
        'SOUTHWEST': 'SW',
        'BALTIMORE': 'BALTO',
        'HEIGHTS': 'HTS',
        'EXTENSION': 'EXT',
        'CENTER': 'CTR',
        'MOUNT': 'MT',
        'SAINT': 'ST',
        'NORTHBOUND': 'NB',
        'SOUTHBOUND': 'SB',
        'EASTBOUND': 'EB',
        'WESTBOUND': 'WB'
    }
    
    # Special handling for ramps
    if name.startswith('RAMP'):
        # Extract the main road names from ramp description
        parts = name.split(' TO ')
        if len(parts) > 1:
            # Get the destination road name
            dest = parts[-1].split()[-1]  # Take the last word as the main road
            return f"RAMP TO {dest}"
    
    # Handle couplets
    if '(NB COUPLET)' in name or '(SB COUPLET)' in name:
        # Remove the couplet designation but keep the base street name
        name = name.replace('(NB COUPLET)', '').replace('(SB COUPLET)', '').strip()
    
    # Common prefixes to remove or standardize
    highway_prefixes = {
        'IS': 'I',  # Interstate
        'US': 'US',  # US Route
        'MD': 'MD',  # Maryland Route
        'CO': 'CO',  # County Route
        'SR': 'SR'   # State Route
    }
    
    # Standardize highway references
    for prefix, std_prefix in highway_prefixes.items():
        if name.startswith(prefix + ' '):
            # Keep standardized highway references
            parts = name.split()
            if len(parts) > 1 and parts[1].isdigit():
                return f"{std_prefix}-{parts[1]}"
    
    # Remove special characters and extra spaces
    name = re.sub(r'[^\w\s-]', ' ', name)
    name = ' '.join(name.split())
    
    # Remove directional indicators in parentheses
    name = re.sub(r'\s*\([NS][BW]\s*(?:COUPLET)?\)\s*', ' ', name)
    name = re.sub(r'\s*\([^)]*\)\s*', ' ', name)  # Remove any parenthetical content
    
    # Apply abbreviations
    for full, abbr in abbreviations.items():
        # Replace full word with abbreviation
        name = re.sub(r'\b' + full + r'\b', abbr, name)
        # Also try to match the abbreviated form to standardize existing abbreviations
        if full != abbr:  # Avoid replacing abbreviation with itself
            name = re.sub(r'\b' + abbr + r'\b', abbr, name)
    
    # Clean up any remaining multiple spaces
    name = ' '.join(name.split())
    
    return name.strip()

def extract_base_name(name, description):
    """Extract base name from road name and description"""
    if pd.isna(name) or pd.isna(description):
        return standardize_street_name(name)
    
    # If description contains " - ", try to get the base name from before it
    if ' - ' in description:
        base_name = description.split(' - ')[0]
        # Check if the base name contains route information
        if any(prefix in base_name for prefix in ['MD', 'US', 'IS']):
            return standardize_street_name(name)
        return standardize_street_name(base_name)
    
    return standardize_street_name(name)

def find_best_match(name, valid_names, cutoff=0.85):
    """Find the best matching street name using fuzzy matching"""
    # Try exact match first
    if name in valid_names:
        return name
        
    # For ramps, try matching with more flexible criteria
    if name.startswith('RAMP'):
        ramp_matches = [vn for vn in valid_names if vn.startswith('RAMP')]
        if ramp_matches:
            matches = get_close_matches(name, ramp_matches, n=1, cutoff=0.7)  # Lower cutoff for ramps
            if matches:
                return matches[0]
    
    # For regular streets, use stricter matching
    matches = get_close_matches(name, valid_names, n=1, cutoff=cutoff)
    return matches[0] if matches else None

def main():
    print("Loading data files...")
    
    # Load MDOT data
    mdot_df = pd.read_csv('MDOT_SHA_Annual_Average_Daily_Traffic_Baltimore.csv')
    edge_names_df = pd.read_csv('Edge_Names_With_Nodes.csv')
    
    print(f"\nTotal MDOT streets: {len(mdot_df)}")
    print(f"Total Edge streets: {len(edge_names_df)}")
    
    print("\nStandardizing MDOT street names...")
    mdot_df['Standardized_Name'] = mdot_df.progress_apply(
        lambda x: extract_base_name(x['Road Name'], x['Station Description']), 
        axis=1
    )
    
    print("\nStandardizing Edge street names...")
    edge_names_df['Standardized_Name'] = edge_names_df['Street_Name'].progress_apply(standardize_street_name)
    
    # Create matching dictionary from edge_names
    edge_names_dict = dict(zip(edge_names_df['Standardized_Name'], edge_names_df['Nodes']))
    valid_names = set(edge_names_dict.keys())
    
    # Create a mapping for highway numbers
    highway_mapping = {}
    for name in valid_names:
        if re.match(r'^(I|US|MD|SR|CO)-\d+', name):
            prefix, number = name.split('-')
            alt_name = f"{prefix} {number}"
            highway_mapping[alt_name] = name
    
    # Perform matching
    print("\nMatching streets...")
    matches = []
    unmatched = []
    
    for idx, row in tqdm(mdot_df.iterrows(), total=len(mdot_df)):
        std_name = row['Standardized_Name']
        matched = False
        
        # Try exact match first
        if std_name in edge_names_dict:
            matches.append({
                'Original_MDOT_Name': row['Road Name'],
                'Standardized_Name': std_name,
                'Edge_Nodes': edge_names_dict[std_name],
                'AADT_Current': row['AADT (Current)'],
                'Station_Description': row['Station Description'],
                'Match_Type': 'exact'
            })
            matched = True
        # Try highway number mapping
        elif std_name in highway_mapping:
            mapped_name = highway_mapping[std_name]
            matches.append({
                'Original_MDOT_Name': row['Road Name'],
                'Standardized_Name': mapped_name,
                'Edge_Nodes': edge_names_dict[mapped_name],
                'AADT_Current': row['AADT (Current)'],
                'Station_Description': row['Station Description'],
                'Match_Type': 'highway_mapped'
            })
            matched = True
        else:
            # Try fuzzy matching
            best_match = find_best_match(std_name, valid_names)
            if best_match:
                matches.append({
                    'Original_MDOT_Name': row['Road Name'],
                    'Standardized_Name': best_match,
                    'Edge_Nodes': edge_names_dict[best_match],
                    'AADT_Current': row['AADT (Current)'],
                    'Station_Description': row['Station Description'],
                    'Match_Type': 'fuzzy'
                })
                matched = True
        
        if not matched:
            unmatched.append({
                'Original_MDOT_Name': row['Road Name'],
                'Standardized_Name': std_name,
                'Station_Description': row['Station Description']
            })
    
    # Convert results to DataFrames
    matches_df = pd.DataFrame(matches)
    unmatched_df = pd.DataFrame(unmatched)
    
    # Print statistics
    print("\nMatching Results:")
    print(f"Total matched streets: {len(matches)}")
    print(f"Total unmatched streets: {len(unmatched)}")
    print(f"Match rate: {len(matches)/len(mdot_df)*100:.2f}%")
    
    if len(matches) > 0:
        print("\nMatch types:")
        print(matches_df['Match_Type'].value_counts())
    
    # Save results
    print("\nSaving results...")
    matches_df.to_csv('matched_streets.csv', index=False)
    unmatched_df.to_csv('unmatched_streets.csv', index=False)
    
    print("\nResults have been saved to 'matched_streets.csv' and 'unmatched_streets.csv'")
    
    # Display some examples
    print("\nExample of matched streets (first 5):")
    print(matches_df[['Original_MDOT_Name', 'Standardized_Name', 'AADT_Current', 'Match_Type']].head().to_string())
    
    if len(unmatched) > 0:
        print("\nExample of unmatched streets (first 5):")
        print(unmatched_df[['Original_MDOT_Name', 'Standardized_Name', 'Station_Description']].head().to_string())

if __name__ == "__main__":
    # Enable tqdm for pandas
    tqdm.pandas()
    main() 