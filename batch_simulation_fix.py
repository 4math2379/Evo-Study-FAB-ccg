# Fix for the batch simulation KeyError in gameplay_simulator.ipynb
# This code should replace the flattened_result dictionary construction

def run_batch_simulation_fixed(games_per_deck: int = 50) -> pd.DataFrame:
    """Run multiple simulations across different deck configurations"""
    
    all_results = []
    
    print(f"Running batch simulation: {games_per_deck} games per deck type...")
    
    for deck_name in deck_presets.keys():
        print(f"  Simulating {deck_name}...")
        
        for game_num in range(games_per_deck):
            if game_num % 10 == 0:
                print(f"    Game {game_num + 1}/{games_per_deck}")
            
            game_result = simulate_single_game(deck_name, max_turns=15)
            
            # Flatten results for DataFrame with SAFE dictionary access
            flattened_result = {
                'game_id': f"{deck_name}_{game_num}",
                'deck_name': game_result['deck_name'],
                'turns_played': game_result['turns_played'],
                'winner': game_result['winner'],
                'teklovossen_final_life': game_result['final_life']['teklovossen'],
                'opponent_final_life': game_result['final_life']['opponent'],
                'evos_equipped': game_result['evos_equipped'],
                'teklo_energy_generated': game_result['resources_generated'].get('teklo_energy', 0),
                'nanite_counters_generated': game_result['resources_generated'].get('nanite_counters', 0),
                'quantum_charges_generated': game_result['resources_generated'].get('quantum_charges', 0),
                'ai_theme_synergy': game_result['theme_synergies'].get('AI', 0),
                'nano_theme_synergy': game_result['theme_synergies'].get('Nano', 0),
                'quantum_theme_synergy': game_result['theme_synergies'].get('Quantum', 0),
                'mechanologist_theme_synergy': game_result['theme_synergies'].get('Mechanologist', 0),
                'win_rate': 1 if game_result['winner'] == 'Teklovossen' else 0
            }
            
            all_results.append(flattened_result)
    
    results_df = pd.DataFrame(all_results)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_df.to_csv(f"../data/simulations/batch_simulation_{timestamp}.csv", index=False)
    
    print(f"Batch simulation completed! Results saved to data/simulations/")
    return results_df
