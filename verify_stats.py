#!/usr/bin/env python3
"""
Comprehensive Basketball Stats Verification Script
Verifies PDF content against raw_pdfs.json and parsed_games.json
"""

import json
import os
import re
from pathlib import Path
import fitz  # PyMuPDF

class StatsVerifier:
    def __init__(self):
        self.stats_dir = Path("/home/runner/work/Stats/Stats/Stat Sheets/Stats")
        self.raw_pdfs_path = Path("/home/runner/work/Stats/Stats/data/raw_pdfs.json")
        self.parsed_games_path = Path("/home/runner/work/Stats/Stats/data/parsed_games.json")
        self.errors = []
        self.warnings = []
        
    def load_json_files(self):
        """Load the JSON data files"""
        with open(self.raw_pdfs_path, 'r') as f:
            self.raw_pdfs = json.load(f)
        with open(self.parsed_games_path, 'r') as f:
            self.parsed_games = json.load(f)
        print(f"✓ Loaded {len(self.raw_pdfs)} entries from raw_pdfs.json")
        print(f"✓ Loaded {len(self.parsed_games)} entries from parsed_games.json")
    
    def extract_pdf_text(self, pdf_path):
        """Extract text from PDF using PyMuPDF"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            self.errors.append(f"ERROR: Failed to extract text from {pdf_path}: {e}")
            return None
    
    def normalize_text(self, text):
        """Normalize text for comparison"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters that might differ
        text = text.strip()
        return text
    
    def verify_pdf_against_raw(self, pdf_name):
        """Verify PDF content matches raw_pdfs.json"""
        print(f"\n{'='*80}")
        print(f"Verifying: {pdf_name}")
        print(f"{'='*80}")
        
        pdf_path = self.stats_dir / pdf_name
        
        if not pdf_path.exists():
            self.errors.append(f"ERROR: PDF file not found: {pdf_path}")
            return
        
        if pdf_name not in self.raw_pdfs:
            self.errors.append(f"ERROR: {pdf_name} not found in raw_pdfs.json")
            return
        
        # Extract text from PDF
        pdf_text = self.extract_pdf_text(pdf_path)
        if pdf_text is None:
            return
        
        # Get raw text from JSON
        raw_text = self.raw_pdfs[pdf_name]
        
        # Normalize both texts
        pdf_text_norm = self.normalize_text(pdf_text)
        raw_text_norm = self.normalize_text(raw_text)
        
        # Compare
        if pdf_text_norm == raw_text_norm:
            print(f"✓ PDF text matches raw_pdfs.json exactly")
        else:
            # Try to find differences
            if len(pdf_text_norm) != len(raw_text_norm):
                self.warnings.append(
                    f"WARNING: {pdf_name} - Length mismatch: "
                    f"PDF={len(pdf_text_norm)} chars, JSON={len(raw_text_norm)} chars"
                )
            
            # Check if one contains the other (might be formatting differences)
            if raw_text_norm in pdf_text_norm or pdf_text_norm in raw_text_norm:
                print(f"⚠ Minor text differences (likely formatting)")
            else:
                self.errors.append(f"ERROR: {pdf_name} - Significant text mismatch between PDF and raw_pdfs.json")
    
    def verify_parsing_logic(self, pdf_name):
        """Verify that parsed_games.json correctly parsed raw_pdfs.json"""
        if pdf_name not in self.raw_pdfs or pdf_name not in self.parsed_games:
            return
        
        raw_text = self.raw_pdfs[pdf_name]
        parsed_data = self.parsed_games[pdf_name]
        
        print(f"\n--- Verifying Parsing Logic ---")
        
        # Extract game info
        if 'game_info' in parsed_data:
            game_info = parsed_data['game_info']
            print(f"Date: {game_info.get('date', 'N/A')}")
            print(f"Opponent: {game_info.get('opponent', 'N/A')}")
            print(f"Final Score: {game_info.get('final_score', 'N/A')}")
        
        # Verify team stats
        if 'valley_catholic' in parsed_data:
            self.verify_team_stats(pdf_name, raw_text, parsed_data['valley_catholic'], 'Valley Catholic')
        
        if 'opponent' in parsed_data:
            opponent_name = parsed_data.get('game_info', {}).get('opponent', 'Opponent')
            self.verify_team_stats(pdf_name, raw_text, parsed_data['opponent'], opponent_name)
    
    def verify_team_stats(self, pdf_name, raw_text, team_data, team_name):
        """Verify team statistics for calculation errors"""
        print(f"\n--- {team_name} Stats ---")
        
        if 'players' not in team_data:
            self.errors.append(f"ERROR: {pdf_name} - No players data for {team_name}")
            return
        
        players = team_data['players']
        print(f"Players: {len(players)}")
        
        # Verify each player's stats
        for i, player in enumerate(players):
            self.verify_player_stats(pdf_name, player, team_name, i+1)
        
        # Verify team totals
        if 'totals' in team_data:
            self.verify_team_totals(pdf_name, players, team_data['totals'], team_name)
    
    def verify_player_stats(self, pdf_name, player, team_name, player_num):
        """Verify individual player statistics"""
        name = player.get('name', f'Player {player_num}')
        number = player.get('number', 'N/A')
        
        # Verify field goal percentage
        fg_made = player.get('fg_made', 0)
        fg_att = player.get('fg_att', 0)
        fg_pct = player.get('fg_pct', 0)
        
        if fg_att > 0:
            calculated_fg_pct = round((fg_made / fg_att) * 100, 1)
            if abs(calculated_fg_pct - fg_pct) > 0.1:
                self.errors.append(
                    f"ERROR: {pdf_name} - {team_name} - {name} (#{number}): "
                    f"FG% incorrect. Calculated: {calculated_fg_pct}%, Recorded: {fg_pct}% "
                    f"(FG: {fg_made}/{fg_att})"
                )
        elif fg_att == 0 and fg_pct != 0:
            self.errors.append(
                f"ERROR: {pdf_name} - {team_name} - {name} (#{number}): "
                f"FG% should be 0 when no attempts, but is {fg_pct}%"
            )
        
        # Verify 3-point percentage
        three_made = player.get('3pt_made', 0)
        three_att = player.get('3pt_att', 0)
        three_pct = player.get('3pt_pct', 0)
        
        if three_att > 0:
            calculated_three_pct = round((three_made / three_att) * 100, 1)
            if abs(calculated_three_pct - three_pct) > 0.1:
                self.errors.append(
                    f"ERROR: {pdf_name} - {team_name} - {name} (#{number}): "
                    f"3PT% incorrect. Calculated: {calculated_three_pct}%, Recorded: {three_pct}% "
                    f"(3PT: {three_made}/{three_att})"
                )
        elif three_att == 0 and three_pct != 0:
            self.errors.append(
                f"ERROR: {pdf_name} - {team_name} - {name} (#{number}): "
                f"3PT% should be 0 when no attempts, but is {three_pct}%"
            )
        
        # Verify free throw percentage
        ft_made = player.get('ft_made', 0)
        ft_att = player.get('ft_att', 0)
        ft_pct = player.get('ft_pct', 0)
        
        if ft_att > 0:
            calculated_ft_pct = round((ft_made / ft_att) * 100, 1)
            if abs(calculated_ft_pct - ft_pct) > 0.1:
                self.errors.append(
                    f"ERROR: {pdf_name} - {team_name} - {name} (#{number}): "
                    f"FT% incorrect. Calculated: {calculated_ft_pct}%, Recorded: {ft_pct}% "
                    f"(FT: {ft_made}/{ft_att})"
                )
        elif ft_att == 0 and ft_pct != 0:
            self.errors.append(
                f"ERROR: {pdf_name} - {team_name} - {name} (#{number}): "
                f"FT% should be 0 when no attempts, but is {ft_pct}%"
            )
        
        # Verify total points calculation
        points = player.get('points', 0)
        # Points = (FG_made * 2) - (3PT_made * 1) + (3PT_made * 3) + FT_made
        # Simplified: Points = (FG_made * 2) + 3PT_made + FT_made
        two_pt_made = fg_made - three_made
        calculated_points = (two_pt_made * 2) + (three_made * 3) + ft_made
        
        if calculated_points != points:
            self.errors.append(
                f"ERROR: {pdf_name} - {team_name} - {name} (#{number}): "
                f"Points incorrect. Calculated: {calculated_points}, Recorded: {points} "
                f"(FG: {fg_made}, 3PT: {three_made}, FT: {ft_made})"
            )
        
        # Verify rebounds
        off_reb = player.get('off_reb', 0)
        def_reb = player.get('def_reb', 0)
        total_reb = player.get('total_reb', 0)
        
        if off_reb + def_reb != total_reb:
            self.errors.append(
                f"ERROR: {pdf_name} - {team_name} - {name} (#{number}): "
                f"Total rebounds incorrect. Calculated: {off_reb + def_reb}, Recorded: {total_reb}"
            )
    
    def verify_team_totals(self, pdf_name, players, totals, team_name):
        """Verify team totals match sum of player stats"""
        print(f"\n--- Verifying {team_name} Team Totals ---")
        
        # Calculate totals from players
        calc_totals = {
            'fg_made': 0,
            'fg_att': 0,
            '3pt_made': 0,
            '3pt_att': 0,
            'ft_made': 0,
            'ft_att': 0,
            'off_reb': 0,
            'def_reb': 0,
            'total_reb': 0,
            'assists': 0,
            'steals': 0,
            'blocks': 0,
            'turnovers': 0,
            'fouls': 0,
            'points': 0
        }
        
        for player in players:
            for key in calc_totals.keys():
                calc_totals[key] += player.get(key, 0)
        
        # Compare with recorded totals
        for key, calc_val in calc_totals.items():
            recorded_val = totals.get(key, 0)
            if calc_val != recorded_val:
                self.errors.append(
                    f"ERROR: {pdf_name} - {team_name} - Team total {key}: "
                    f"Calculated: {calc_val}, Recorded: {recorded_val}"
                )
        
        # Verify team percentages
        fg_made = totals.get('fg_made', 0)
        fg_att = totals.get('fg_att', 0)
        fg_pct = totals.get('fg_pct', 0)
        
        if fg_att > 0:
            calculated_fg_pct = round((fg_made / fg_att) * 100, 1)
            if abs(calculated_fg_pct - fg_pct) > 0.1:
                self.errors.append(
                    f"ERROR: {pdf_name} - {team_name} - Team FG%: "
                    f"Calculated: {calculated_fg_pct}%, Recorded: {fg_pct}%"
                )
        
        three_made = totals.get('3pt_made', 0)
        three_att = totals.get('3pt_att', 0)
        three_pct = totals.get('3pt_pct', 0)
        
        if three_att > 0:
            calculated_three_pct = round((three_made / three_att) * 100, 1)
            if abs(calculated_three_pct - three_pct) > 0.1:
                self.errors.append(
                    f"ERROR: {pdf_name} - {team_name} - Team 3PT%: "
                    f"Calculated: {calculated_three_pct}%, Recorded: {three_pct}%"
                )
        
        ft_made = totals.get('ft_made', 0)
        ft_att = totals.get('ft_att', 0)
        ft_pct = totals.get('ft_pct', 0)
        
        if ft_att > 0:
            calculated_ft_pct = round((ft_made / ft_att) * 100, 1)
            if abs(calculated_ft_pct - ft_pct) > 0.1:
                self.errors.append(
                    f"ERROR: {pdf_name} - {team_name} - Team FT%: "
                    f"Calculated: {calculated_ft_pct}%, Recorded: {ft_pct}%"
                )
        
        print(f"✓ Team Totals: {calc_totals['points']} points")
    
    def check_pdf_coverage(self):
        """Check if all PDFs in directory are in JSON files"""
        print(f"\n{'='*80}")
        print("Checking PDF Coverage")
        print(f"{'='*80}")
        
        pdf_files = list(self.stats_dir.glob("*.pdf"))
        pdf_names = [f.name for f in pdf_files]
        
        print(f"\nTotal PDFs in directory: {len(pdf_files)}")
        print(f"PDFs in raw_pdfs.json: {len(self.raw_pdfs)}")
        print(f"PDFs in parsed_games.json: {len(self.parsed_games)}")
        
        # Check for missing PDFs in JSON
        missing_in_raw = [p for p in pdf_names if p not in self.raw_pdfs]
        missing_in_parsed = [p for p in pdf_names if p not in self.parsed_games]
        
        if missing_in_raw:
            print(f"\n⚠ PDFs not in raw_pdfs.json:")
            for pdf in missing_in_raw:
                print(f"  - {pdf}")
                self.warnings.append(f"WARNING: {pdf} not in raw_pdfs.json")
        
        if missing_in_parsed:
            print(f"\n⚠ PDFs not in parsed_games.json:")
            for pdf in missing_in_parsed:
                print(f"  - {pdf}")
                self.warnings.append(f"WARNING: {pdf} not in parsed_games.json")
        
        # Check for JSON entries without PDFs
        extra_in_raw = [p for p in self.raw_pdfs.keys() if p not in pdf_names]
        extra_in_parsed = [p for p in self.parsed_games.keys() if p not in pdf_names]
        
        if extra_in_raw:
            print(f"\n⚠ Entries in raw_pdfs.json without PDF files:")
            for pdf in extra_in_raw:
                print(f"  - {pdf}")
                self.warnings.append(f"WARNING: {pdf} in raw_pdfs.json but PDF not found")
        
        if extra_in_parsed:
            print(f"\n⚠ Entries in parsed_games.json without PDF files:")
            for pdf in extra_in_parsed:
                print(f"  - {pdf}")
                self.warnings.append(f"WARNING: {pdf} in parsed_games.json but PDF not found")
    
    def run_verification(self):
        """Run complete verification process"""
        print("="*80)
        print("BASKETBALL STATS VERIFICATION")
        print("="*80)
        
        # Load JSON files
        self.load_json_files()
        
        # Check PDF coverage
        self.check_pdf_coverage()
        
        # Verify each PDF in raw_pdfs.json
        for pdf_name in self.raw_pdfs.keys():
            self.verify_pdf_against_raw(pdf_name)
            self.verify_parsing_logic(pdf_name)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print verification summary"""
        print("\n" + "="*80)
        print("VERIFICATION SUMMARY")
        print("="*80)
        
        if not self.errors and not self.warnings:
            print("\n✓✓✓ ALL CHECKS PASSED! No errors or warnings found. ✓✓✓")
        else:
            if self.warnings:
                print(f"\n⚠ WARNINGS: {len(self.warnings)}")
                print("-" * 80)
                for warning in self.warnings:
                    print(warning)
            
            if self.errors:
                print(f"\n❌ ERRORS FOUND: {len(self.errors)}")
                print("-" * 80)
                for error in self.errors:
                    print(error)
        
        print("\n" + "="*80)
        print(f"Total Errors: {len(self.errors)}")
        print(f"Total Warnings: {len(self.warnings)}")
        print("="*80)

if __name__ == "__main__":
    verifier = StatsVerifier()
    verifier.run_verification()
