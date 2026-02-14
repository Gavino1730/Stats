#!/usr/bin/env python3
"""
Fix Parsed Games Data - Corrects the parsing error where +/- was read as points.
This script re-parses raw_pdfs.json to correctly extract the 'pts' column.
"""

import json
import re
from pathlib import Path


def parse_stat_line_old_format(line):
    """
    Parse a single player stat line from the OLD raw PDF format (space-separated).
    
    Expected format:
    #20 H. Lomber 11-24 46% 3-9 33% 4-4 100% 0 3 3 7 4 3 0 30 29
    
    Columns: fg fg% 3pt 3pt% ft ft% oreb dreb foul stl to blk asst +/- pts
    The last two numbers are: +/- (second to last) and pts (last)
    """
    # Skip team total lines and empty players
    if not line.strip() or line.startswith('Valley Catholic') or line.startswith('Valiants') or '*Fg column' in line:
        return None
    
    # Check if this is a player line (starts with #)
    if not line.strip().startswith('#'):
        return None
    
    # Extract player number and name
    match = re.match(r'#(\d+)\s+([A-Z]\.\s+[A-Za-z]+)', line)
    if not match:
        return None
    
    number = int(match.group(1))
    name = match.group(2).strip()
    
    # Split the line into parts
    parts = line.split()
    
    # Find the stats - they come after the name
    # Format: #20 H. Lomber fg fg% 3pt 3pt% ft ft% oreb dreb foul stl to blk asst +/- pts
    # After name, we have: fg, fg%, 3pt, 3pt%, ft, ft%, then individual stats
    
    stats_start = 3  # After #, number initial, lastname
    
    try:
        # Extract shooting stats
        fg = parts[stats_start]  # e.g., "11-24"
        fg_pct = parts[stats_start + 1]  # e.g., "46%"
        three_pt = parts[stats_start + 2]  # e.g., "3-9"
        three_pt_pct = parts[stats_start + 3]  # e.g., "33%"
        ft = parts[stats_start + 4]  # e.g., "4-4"
        ft_pct = parts[stats_start + 5]  # e.g., "100%"
        
        # Individual stats start at index stats_start + 6
        # Column order after shooting stats (6 fields):
        # oreb(6) dreb(7) foul(8) stl(9) to(10) blk(11) asst(12) +/-(13) pts(14)
        individual_start = stats_start + 6
        
        # Handle case where player has no stats (shown as dashes)
        if parts[individual_start] == '-':
            return None
        
        oreb = int(parts[individual_start])      # Column 6: offensive rebounds
        dreb = int(parts[individual_start + 1])  # Column 7: defensive rebounds
        fouls = int(parts[individual_start + 2]) # Column 8: fouls
        stl = int(parts[individual_start + 3])   # Column 9: steals
        to = int(parts[individual_start + 4])    # Column 10: turnovers
        blk = int(parts[individual_start + 5])   # Column 11: blocks
        asst = int(parts[individual_start + 6])  # Column 12: assists
        
        # Last two columns: +/- (13) and pts (14)
        plus_minus_str = parts[individual_start + 7]  # Column 13: plus/minus (not used)
        pts = int(parts[individual_start + 8])        # Column 14: POINTS (actual scoring)
        
        return {
            'number': number,
            'name': name,
            'fg': fg,
            'fg_pct': fg_pct,
            '3pt': three_pt,
            '3pt_pct': three_pt_pct,
            'ft': ft,
            'ft_pct': ft_pct,
            'oreb': oreb,
            'dreb': dreb,
            'fouls': fouls,
            'stl': stl,
            'to': to,
            'blk': blk,
            'asst': asst,
            'pts': pts  # Using the LAST column, not +/-
        }
    except (IndexError, ValueError) as e:
        return None


def parse_stat_line_new_format(lines, start_idx):
    """
    Parse a single player stat line from the NEW raw PDF format (each field on its own line).
    
    Expected format (multiple lines):
    #20 H. Lomber
    10-13
    77%
    1-4
    25%
    5-6
    83%
    1
    5
    0
    6
    2
    0
    4
    38
    0 (optional: minutes)
    26 (points)
    
    Returns: (player_dict, next_line_index) or (None, start_idx)
    """
    try:
        # First line should have player number and name
        player_line = lines[start_idx].strip()
        if not player_line.startswith('#'):
            return None, start_idx
        
        # Extract player number and name
        match = re.match(r'#(\d+)\s+([A-Z]\.\s+[A-Za-z]+)', player_line)
        if not match:
            return None, start_idx
        
        number = int(match.group(1))
        name = match.group(2).strip()
        
        idx = start_idx + 1
        
        # Extract stats in order
        fg = lines[idx].strip(); idx += 1
        fg_pct = lines[idx].strip(); idx += 1
        three_pt = lines[idx].strip(); idx += 1
        three_pt_pct = lines[idx].strip(); idx += 1
        ft = lines[idx].strip(); idx += 1
        ft_pct = lines[idx].strip(); idx += 1
        oreb = int(lines[idx].strip()); idx += 1
        dreb = int(lines[idx].strip()); idx += 1
        fouls = int(lines[idx].strip()); idx += 1
        stl = int(lines[idx].strip()); idx += 1
        to = int(lines[idx].strip()); idx += 1
        blk = int(lines[idx].strip()); idx += 1
        asst = int(lines[idx].strip()); idx += 1
        plus_minus = lines[idx].strip(); idx += 1  # +/- (we don't use this)
        
        # Check if next line is minutes or points
        # Minutes are always shown (even 0), points are always > 0 for starters usually
        # But better way: check if there are TWO more numeric lines or ONE
        # Try to read next two lines as numbers
        try:
            val1 = int(lines[idx].strip())
            val2 = int(lines[idx + 1].strip())
            # If we successfully read two numbers, first is minutes, second is points
            minutes = val1
            pts = val2
            idx += 2
        except (ValueError, IndexError):
            # Only one number left, it's points (no minutes column)
            pts = int(lines[idx].strip())
            idx += 1
        
        return {
            'number': number,
            'name': name,
            'fg': fg,
            'fg_pct': fg_pct,
            '3pt': three_pt,
            '3pt_pct': three_pt_pct,
            'ft': ft,
            'ft_pct': ft_pct,
            'oreb': oreb,
            'dreb': dreb,
            'fouls': fouls,
            'stl': stl,
            'to': to,
            'blk': blk,
            'asst': asst,
            'pts': pts
        }, idx
        
    except (IndexError, ValueError, AttributeError) as e:
        return None, start_idx


def parse_game_header(text):
    """Extract game date, opponent, and scores from raw text."""
    lines = text.split('\n')
    
    # Detect format
    # OLD FORMAT: "Easy Stats\nDate\nScores\nTeams"
    # NEW FORMAT: "Date\nScore1\nScore2\nTeams"
    
    if lines[0].strip() == 'Easy Stats':
        # OLD FORMAT
        date = lines[1].strip() if len(lines) > 1 else ""
        score_line = lines[2].strip() if len(lines) > 2 else ""
        team_line = lines[3].strip() if len(lines) > 3 else ""
        
        scores = score_line.split()
        teams = team_line.split('Valley Catholic')
        
        # Determine which score is VC's
        if 'Valley Catholic' in team_line:
            if team_line.startswith('Valley Catholic'):
                # VC is listed first, so first score is theirs
                vc_score = int(scores[0]) if len(scores) > 0 else 0
                opp_score = int(scores[1]) if len(scores) > 1 else 0
                opponent = teams[1].strip() if len(teams) > 1 else ""
            else:
                # VC is listed second, so second score is theirs
                vc_score = int(scores[1]) if len(scores) > 1 else 0
                opp_score = int(scores[0]) if len(scores) > 0 else 0
                opponent = teams[0].strip() if len(teams) > 0 else ""
        else:
            vc_score = opp_score = 0
            opponent = ""
    else:
        # NEW FORMAT
        date = lines[0].strip() if len(lines) > 0 else ""
        score1 = int(lines[1].strip()) if len(lines) > 1 else 0
        score2 = int(lines[2].strip()) if len(lines) > 2 else 0
        
        # Find where "Valley Catholic" appears in the lines
        vc_line_idx = -1
        opponent_parts = []
        
        for i in range(3, min(8, len(lines))):
            line = lines[i].strip()
            if 'Valley Catholic' in line:
                vc_line_idx = i
                break
            elif line and line != 'Valiants' and line != '\xa0' and len(line) > 2:
                opponent_parts.append(line)
        
        opponent = ' '.join(opponent_parts)
        
        # Determine scores based on VC position
        # The teams are listed in order: first team, then second team
        # score1 is the first team's score, score2 is the second team's score
        # If opponent appears before VC (opponent_parts not empty and vc_line_idx > 3),
        # then opponent is first team
        if opponent_parts and vc_line_idx > 3:
            # Opponent listed first, VC listed second
            opp_score = score1
            vc_score = score2
        else:
            # VC listed first (or couldn't determine)
            vc_score = score1
            opp_score = score2
    
    return date, opponent, vc_score, opp_score


def parse_raw_pdf_text(filename, raw_text):
    """Parse the complete raw PDF text into structured game data."""
    lines = raw_text.split('\n')
    
    # Detect format by checking if first player line has all stats on one line
    is_old_format = False
    for line in lines:
        if line.strip().startswith('#'):
            # Old format has all stats on one line (should have 15+ parts)
            parts = line.split()
            is_old_format = len(parts) > 10
            break
    
    # Parse header info
    date, opponent, vc_score, opp_score = parse_game_header(raw_text)
    
    # Parse player stats based on format
    players = []
    
    if is_old_format:
        # OLD FORMAT: Space-separated on single lines
        for line in lines:
            player_data = parse_stat_line_old_format(line)
            if player_data:
                players.append(player_data)
    else:
        # NEW FORMAT: Each field on its own line
        idx = 0
        while idx < len(lines):
            line = lines[idx].strip()
            if line.startswith('#'):
                player_data, next_idx = parse_stat_line_new_format(lines, idx)
                if player_data:
                    players.append(player_data)
                    idx = next_idx
                else:
                    idx += 1
            else:
                idx += 1
    
    return {
        'filename': filename,
        'date': date,
        'opponent': opponent,
        'vc_score': vc_score,
        'opp_score': opp_score,
        'players': players
    }


def main():
    """Main function to re-parse all games from raw_pdfs.json."""
    print("=" * 70)
    print("FIXING PARSED GAMES DATA")
    print("=" * 70)
    print()
    
    # Load raw PDF data
    raw_pdfs_path = Path('/home/runner/work/Stats/Stats/data/raw_pdfs.json')
    parsed_games_path = Path('/home/runner/work/Stats/Stats/data/parsed_games.json')
    backup_path = Path('/home/runner/work/Stats/Stats/data/parsed_games.json.backup')
    
    print(f"Loading raw PDF data from: {raw_pdfs_path}")
    with open(raw_pdfs_path, 'r') as f:
        raw_pdfs = json.load(f)
    print(f"✓ Loaded {len(raw_pdfs)} raw PDF entries")
    print()
    
    # Backup existing parsed games
    if parsed_games_path.exists():
        print(f"Creating backup of existing data: {backup_path}")
        with open(parsed_games_path, 'r') as f:
            old_data = json.load(f)
        with open(backup_path, 'w') as f:
            json.dump(old_data, f, indent=2)
        print("✓ Backup created")
        print()
    
    # Re-parse all games
    print("Re-parsing all games with CORRECT points extraction...")
    print("-" * 70)
    
    parsed_games = {}
    total_players = 0
    
    for filename, raw_text in sorted(raw_pdfs.items()):
        print(f"\nParsing: {filename}")
        game_data = parse_raw_pdf_text(filename, raw_text)
        
        print(f"  Date: {game_data['date']}")
        print(f"  Opponent: {game_data['opponent']}")
        print(f"  Score: VC {game_data['vc_score']} - {game_data['opponent']} {game_data['opp_score']}")
        print(f"  Players parsed: {len(game_data['players'])}")
        
        # Show first player as example
        if game_data['players']:
            p = game_data['players'][0]
            print(f"  Example - #{p['number']} {p['name']}: {p['pts']} pts")
        
        parsed_games[filename] = game_data
        total_players += len(game_data['players'])
    
    print()
    print("-" * 70)
    print(f"✓ Successfully parsed {len(parsed_games)} games")
    print(f"✓ Total players: {total_players}")
    print()
    
    # Save corrected data
    print(f"Saving corrected data to: {parsed_games_path}")
    with open(parsed_games_path, 'w') as f:
        json.dump(parsed_games, f, indent=2)
    print("✓ Corrected data saved!")
    print()
    
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"✓ Processed {len(parsed_games)} games from raw_pdfs.json")
    print(f"✓ Extracted stats for {total_players} player records")
    print(f"✓ Backup of old data saved to: {backup_path.name}")
    print(f"✓ New corrected data saved to: {parsed_games_path.name}")
    print()
    print("All points data has been CORRECTED!")
    print("The 'pts' column is now correctly parsed (was reading '+/-' before)")
    print()


if __name__ == '__main__':
    main()
