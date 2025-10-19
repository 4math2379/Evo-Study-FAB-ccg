"""
Data Analytics Pipeline for Teklovossen Card Balance Analysis
Advanced data processing, metrics calculation, and visualization tools
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import json
from datetime import datetime, timedelta
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

# Statistical and ML libraries
from scipy import stats
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score
from sklearn.metrics import mean_squared_error, r2_score

# Local imports
try:
    from card_feature_extractor import CardFeatureExtractor
except ImportError:
    # For relative imports when used as module
    from .card_feature_extractor import CardFeatureExtractor


class TekloDataAnalyzer:
    """Comprehensive data analysis pipeline for Teklovossen simulations"""
    
    def __init__(self, data_path: str = "../data", card_csv_path: str = "../notebooks/card.csv"):
        self.data_path = Path(data_path)
        self.simulation_data: Optional[pd.DataFrame] = None
        self.ml_data: Optional[pd.DataFrame] = None
        self.card_performance_metrics: Dict[str, Any] = {}
        
        # Initialize card feature extractor
        self.card_extractor = CardFeatureExtractor(card_csv_path)
        
        # Plotting configuration
        plt.style.use('seaborn-v0_8')
        sns.set_palette('husl')
        
    def load_simulation_data(self, filename: Optional[str] = None) -> pd.DataFrame:
        """Load simulation data from CSV files"""
        sim_path = self.data_path / "simulations"
        
        if filename:
            file_path = sim_path / filename
        else:
            # Load the most recent simulation file
            csv_files = list(sim_path.glob("batch_simulation_*.csv"))
            if not csv_files:
                raise FileNotFoundError("No simulation data files found")
            file_path = max(csv_files, key=lambda x: x.stat().st_mtime)
        
        self.simulation_data = pd.read_csv(file_path)
        print(f"Loaded simulation data: {len(self.simulation_data)} games from {file_path.name}")
        return self.simulation_data
    
    def load_ml_data(self, filename: Optional[str] = None) -> pd.DataFrame:
        """Load processed ML training data"""
        ml_path = self.data_path / "processed"
        
        if filename:
            file_path = ml_path / filename
        else:
            # Load the most recent ML data file
            csv_files = list(ml_path.glob("ml_training_data_*.csv"))
            if not csv_files:
                raise FileNotFoundError("No ML training data files found")
            file_path = max(csv_files, key=lambda x: x.stat().st_mtime)
        
        self.ml_data = pd.read_csv(file_path)
        print(f"Loaded ML training data: {len(self.ml_data)} deck configurations from {file_path.name}")
        return self.ml_data
    
    def calculate_advanced_metrics(self) -> Dict[str, Any]:
        """Calculate advanced performance metrics beyond basic win rates"""
        if self.simulation_data is None:
            raise ValueError("No simulation data loaded")
        
        df = self.simulation_data
        metrics = {}
        
        # Deck-specific metrics
        deck_metrics = {}
        for deck_name in df['deck_name'].unique():
            deck_data = df[df['deck_name'] == deck_name]
            
            deck_metrics[deck_name] = {
                # Performance metrics
                'win_rate': deck_data['win_rate'].mean(),
                'win_rate_confidence_interval': self._calculate_confidence_interval(deck_data['win_rate']),
                'average_game_length': deck_data['turns_played'].mean(),
                'game_length_std': deck_data['turns_played'].std(),
                'consistency_index': 1.0 - (deck_data['turns_played'].std() / deck_data['turns_played'].mean()),
                
                # Resource efficiency
                'resource_generation_rate': (
                    deck_data['teklo_energy_generated'].sum() +
                    deck_data['nanite_counters_generated'].sum() +
                    deck_data['quantum_charges_generated'].sum()
                ) / deck_data['turns_played'].sum(),
                
                'evo_deployment_rate': deck_data['evos_equipped'].sum() / len(deck_data),
                'survivability_index': deck_data['teklovossen_final_life'].mean() / 20.0,
                
                # Theme focus analysis
                'theme_specialization_score': max([
                    deck_data['ai_theme_synergy'].mean(),
                    deck_data['nano_theme_synergy'].mean(),
                    deck_data['quantum_theme_synergy'].mean()
                ]),
                
                # Statistical significance
                'sample_size': len(deck_data),
                'win_rate_std_error': deck_data['win_rate'].std() / np.sqrt(len(deck_data)),
                
                # Performance distribution
                'win_rate_percentiles': {
                    '25th': deck_data['win_rate'].quantile(0.25),
                    '50th': deck_data['win_rate'].quantile(0.5),
                    '75th': deck_data['win_rate'].quantile(0.75)
                }
            }
        
        metrics['deck_performance'] = deck_metrics
        
        # Cross-deck statistical tests
        deck_groups = [df[df['deck_name'] == deck]['win_rate'] for deck in df['deck_name'].unique()]
        f_stat, p_value = stats.f_oneway(*deck_groups)
        
        metrics['statistical_tests'] = {
            'anova_f_statistic': f_stat,
            'anova_p_value': p_value,
            'significant_difference': p_value < 0.05
        }
        
        # Overall meta-analysis
        metrics['meta_analysis'] = {
            'total_games': len(df),
            'overall_win_rate': df['win_rate'].mean(),
            'average_game_duration': df['turns_played'].mean(),
            'most_successful_strategy': max(deck_metrics.keys(), 
                                          key=lambda x: deck_metrics[x]['win_rate']),
            'most_consistent_strategy': max(deck_metrics.keys(), 
                                         key=lambda x: deck_metrics[x]['consistency_index'])
        }
        
        self.card_performance_metrics = metrics
        return metrics
    
    def _calculate_confidence_interval(self, data: pd.Series, confidence: float = 0.95) -> Tuple[float, float]:
        """Calculate confidence interval for a data series"""
        n = len(data)
        mean = data.mean()
        std_err = stats.sem(data)
        interval = stats.t.interval(confidence, n-1, loc=mean, scale=std_err)
        return interval
    
    def generate_comprehensive_report(self, save_path: Optional[str] = None) -> Dict[str, Any]:
        """Generate comprehensive analysis report"""
        if self.card_performance_metrics == {}:
            self.calculate_advanced_metrics()
        
        report = {
            'analysis_timestamp': datetime.now().isoformat(),
            'data_summary': {
                'total_simulations': len(self.simulation_data),
                'deck_types': list(self.simulation_data['deck_name'].unique()),
                'analysis_period': 'Single batch simulation'
            },
            'performance_metrics': self.card_performance_metrics,
            'recommendations': self._generate_balance_recommendations()
        }
        
        if save_path:
            with open(save_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"Comprehensive report saved to {save_path}")
        
        return report
    
    def _generate_balance_recommendations(self) -> Dict[str, List[str]]:
        """Generate automated balance recommendations based on analysis"""
        recommendations = {
            'overpowered_cards': [],
            'underpowered_cards': [],
            'balance_adjustments': [],
            'design_insights': []
        }
        
        deck_metrics = self.card_performance_metrics.get('deck_performance', {})
        
        # Identify overpowered strategies
        win_rates = {deck: metrics['win_rate'] for deck, metrics in deck_metrics.items()}
        avg_win_rate = np.mean(list(win_rates.values()))
        std_win_rate = np.std(list(win_rates.values()))
        
        for deck, win_rate in win_rates.items():
            if win_rate > avg_win_rate + 2 * std_win_rate:
                recommendations['overpowered_cards'].append(f"{deck} deck (win rate: {win_rate:.2%})")
                recommendations['balance_adjustments'].append(
                    f"Consider increasing costs for {deck} key cards by 1 Teklo Energy"
                )
            elif win_rate < avg_win_rate - 2 * std_win_rate:
                recommendations['underpowered_cards'].append(f"{deck} deck (win rate: {win_rate:.2%})")
                recommendations['balance_adjustments'].append(
                    f"Consider reducing costs or adding card draw effects for {deck} theme"
                )
        
        # Resource efficiency analysis
        for deck, metrics in deck_metrics.items():
            resource_rate = metrics['resource_generation_rate']
            evo_rate = metrics['evo_deployment_rate']
            
            if resource_rate > 2.0 and metrics['win_rate'] > 0.6:
                recommendations['design_insights'].append(
                    f"{deck}: High resource generation may enable overpowered combos"
                )
            
            if evo_rate < 0.5 and metrics['win_rate'] < 0.4:
                recommendations['design_insights'].append(
                    f"{deck}: Low evo deployment suggests transformation costs too high"
                )
        
        return recommendations
    
    def create_advanced_visualizations(self, save_plots: bool = True) -> None:
        """Create comprehensive visualization suite"""
        if self.simulation_data is None:
            raise ValueError("No simulation data loaded")
        
        # Create figure with multiple subplots
        fig = plt.figure(figsize=(20, 16))
        gs = fig.add_gridspec(4, 3, height_ratios=[1, 1, 1, 1], width_ratios=[1, 1, 1])
        
        # 1. Win Rate Distribution by Deck
        ax1 = fig.add_subplot(gs[0, 0])
        sns.boxplot(data=self.simulation_data, x='deck_name', y='win_rate', ax=ax1)
        ax1.set_title('Win Rate Distribution by Deck Type', fontsize=14, fontweight='bold')
        ax1.set_xticklabels(ax1.get_xticklabels(), rotation=45)
        ax1.axhline(y=0.5, color='red', linestyle='--', alpha=0.7, label='50% Win Rate')
        ax1.legend()
        
        # 2. Resource Generation Efficiency
        ax2 = fig.add_subplot(gs[0, 1])
        resource_cols = ['teklo_energy_generated', 'nanite_counters_generated', 'quantum_charges_generated']
        resource_data = self.simulation_data.groupby('deck_name')[resource_cols].mean()
        resource_data.plot(kind='bar', ax=ax2)
        ax2.set_title('Resource Generation by Deck Type', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Deck Type')
        ax2.set_ylabel('Average Resources Generated')
        ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # 3. Game Length vs Win Rate Scatter
        ax3 = fig.add_subplot(gs[0, 2])
        for deck in self.simulation_data['deck_name'].unique():
            deck_data = self.simulation_data[self.simulation_data['deck_name'] == deck]
            ax3.scatter(deck_data['turns_played'], deck_data['win_rate'], 
                       label=deck, alpha=0.6, s=30)
        ax3.set_xlabel('Game Length (Turns)')
        ax3.set_ylabel('Win Rate')
        ax3.set_title('Game Length vs Win Rate', fontsize=14, fontweight='bold')
        ax3.legend()
        
        # 4. Evo Equipment Usage Patterns
        ax4 = fig.add_subplot(gs[1, 0])
        sns.violinplot(data=self.simulation_data, x='deck_name', y='evos_equipped', ax=ax4)
        ax4.set_title('Evo Equipment Usage Distribution', fontsize=14, fontweight='bold')
        ax4.set_xticklabels(ax4.get_xticklabels(), rotation=45)
        
        # 5. Theme Synergy Heatmap
        ax5 = fig.add_subplot(gs[1, 1])
        theme_data = self.simulation_data.groupby('deck_name')[['ai_theme_synergy', 'nano_theme_synergy', 'quantum_theme_synergy']].mean()
        sns.heatmap(theme_data.T, annot=True, cmap='YlOrRd', ax=ax5, fmt='.1f')
        ax5.set_title('Theme Synergy Heatmap', fontsize=14, fontweight='bold')
        
        # 6. Performance Correlation Matrix
        ax6 = fig.add_subplot(gs[1, 2])
        perf_cols = ['win_rate', 'turns_played', 'evos_equipped', 'teklo_energy_generated', 'teklovossen_final_life']
        corr_matrix = self.simulation_data[perf_cols].corr()
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, ax=ax6, fmt='.2f')
        ax6.set_title('Performance Metrics Correlation', fontsize=14, fontweight='bold')
        
        # 7. Statistical Significance Tests
        ax7 = fig.add_subplot(gs[2, 0])
        deck_win_rates = [self.simulation_data[self.simulation_data['deck_name'] == deck]['win_rate'] 
                         for deck in self.simulation_data['deck_name'].unique()]
        ax7.boxplot(deck_win_rates, labels=self.simulation_data['deck_name'].unique())
        ax7.set_title('Win Rate Statistical Distribution', fontsize=14, fontweight='bold')
        ax7.set_ylabel('Win Rate')
        plt.setp(ax7.get_xticklabels(), rotation=45)
        
        # 8. Resource Efficiency Scatter Plot
        ax8 = fig.add_subplot(gs[2, 1])
        for deck in self.simulation_data['deck_name'].unique():
            deck_data = self.simulation_data[self.simulation_data['deck_name'] == deck]
            total_resources = (deck_data['teklo_energy_generated'] + 
                             deck_data['nanite_counters_generated'] + 
                             deck_data['quantum_charges_generated'])
            resource_efficiency = total_resources / deck_data['turns_played']
            ax8.scatter(resource_efficiency, deck_data['win_rate'], label=deck, alpha=0.6)
        ax8.set_xlabel('Resource Efficiency (Resources/Turn)')
        ax8.set_ylabel('Win Rate')
        ax8.set_title('Resource Efficiency vs Performance', fontsize=14, fontweight='bold')
        ax8.legend()
        
        # 9. Survivability Analysis
        ax9 = fig.add_subplot(gs[2, 2])
        sns.barplot(data=self.simulation_data, x='deck_name', y='teklovossen_final_life', ax=ax9)
        ax9.set_title('Average Survivability by Deck', fontsize=14, fontweight='bold')
        ax9.set_ylabel('Average Final Life')
        ax9.set_xticklabels(ax9.get_xticklabels(), rotation=45)
        ax9.axhline(y=10, color='orange', linestyle='--', alpha=0.7, label='50% Health')
        ax9.legend()
        
        # 10. Performance Trends Over Games
        ax10 = fig.add_subplot(gs[3, :])
        # Create rolling averages for trend analysis
        window_size = max(5, len(self.simulation_data) // 20)
        for deck in self.simulation_data['deck_name'].unique():
            deck_data = self.simulation_data[self.simulation_data['deck_name'] == deck].reset_index(drop=True)
            if len(deck_data) > window_size:
                rolling_win_rate = deck_data['win_rate'].rolling(window=window_size).mean()
                ax10.plot(range(len(deck_data)), rolling_win_rate, label=f'{deck} (trend)', linewidth=2)
        ax10.set_xlabel('Game Number')
        ax10.set_ylabel('Rolling Average Win Rate')
        ax10.set_title(f'Performance Trends (Rolling {window_size}-game Average)', fontsize=14, fontweight='bold')
        ax10.legend()
        ax10.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_plots:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            plot_path = self.data_path / "processed" / f"comprehensive_analysis_{timestamp}.png"
            plt.savefig(plot_path, dpi=300, bbox_inches='tight')
            print(f"Comprehensive visualization saved to {plot_path}")
        
        plt.show()
    
    def perform_clustering_analysis(self) -> Dict[str, Any]:
        """Perform clustering analysis on deck archetypes"""
        if self.ml_data is None:
            self.load_ml_data()
        
        # Prepare feature matrix
        feature_cols = ['AI', 'Nano', 'Quantum', 'Base', 
                       'avg_win_rate', 'avg_turns', 'avg_evos',
                       'resource_efficiency', 'consistency_score']
        
        # Create resource efficiency if not present
        if 'resource_efficiency' not in self.ml_data.columns:
            self.ml_data['resource_efficiency'] = (
                self.ml_data['avg_teklo_energy'] + 
                self.ml_data['avg_nanite_counters'] + 
                self.ml_data['avg_quantum_charges']
            ) / self.ml_data['avg_turns']
        
        available_features = [col for col in feature_cols if col in self.ml_data.columns]
        X = self.ml_data[available_features]
        
        # Standardize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Perform K-means clustering
        optimal_clusters = self._find_optimal_clusters(X_scaled)
        kmeans = KMeans(n_clusters=optimal_clusters, random_state=42)
        clusters = kmeans.fit_predict(X_scaled)
        
        # PCA for visualization
        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(X_scaled)
        
        # Create clustering visualization
        plt.figure(figsize=(12, 8))
        scatter = plt.scatter(X_pca[:, 0], X_pca[:, 1], c=clusters, cmap='viridis', alpha=0.7, s=100)
        plt.colorbar(scatter)
        
        # Add deck labels
        for i, deck_name in enumerate(self.ml_data['deck_name']):
            plt.annotate(deck_name, (X_pca[i, 0], X_pca[i, 1]), 
                        xytext=(5, 5), textcoords='offset points', fontsize=10)
        
        plt.xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.1%} variance)')
        plt.ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.1%} variance)')
        plt.title('Deck Archetype Clustering Analysis')
        plt.grid(True, alpha=0.3)
        plt.show()
        
        # Analyze cluster characteristics
        cluster_analysis = {}
        self.ml_data['cluster'] = clusters
        
        for cluster_id in range(optimal_clusters):
            cluster_data = self.ml_data[self.ml_data['cluster'] == cluster_id]
            cluster_analysis[f'cluster_{cluster_id}'] = {
                'decks': cluster_data['deck_name'].tolist(),
                'avg_win_rate': cluster_data['avg_win_rate'].mean(),
                'dominant_theme': cluster_data[['AI', 'Nano', 'Quantum']].mean().idxmax(),
                'characteristics': self._describe_cluster(cluster_data, available_features)
            }
        
        return {
            'optimal_clusters': optimal_clusters,
            'cluster_analysis': cluster_analysis,
            'pca_variance_explained': pca.explained_variance_ratio_.tolist(),
            'feature_importance': dict(zip(available_features, 
                                         np.abs(pca.components_[0]) + np.abs(pca.components_[1])))
        }
    
    def _find_optimal_clusters(self, X: np.ndarray) -> int:
        """Find optimal number of clusters using elbow method"""
        inertias = []
        k_range = range(2, min(8, len(X)))
        
        for k in k_range:
            kmeans = KMeans(n_clusters=k, random_state=42)
            kmeans.fit(X)
            inertias.append(kmeans.inertia_)
        
        # Find elbow point (simplified)
        diffs = np.diff(inertias)
        elbow = np.argmax(diffs) + 2  # +2 because we start from k=2 and np.diff reduces length by 1
        return min(elbow, 4)  # Cap at 4 clusters for interpretability
    
    def _describe_cluster(self, cluster_data: pd.DataFrame, features: List[str]) -> Dict[str, float]:
        """Describe cluster characteristics"""
        return {feature: cluster_data[feature].mean() for feature in features if feature in cluster_data.columns}
    
    def enrich_with_card_features(self, deck_cards_dict: Optional[Dict[str, List[str]]] = None) -> pd.DataFrame:
        """Enrich ML data with card features from card.csv
        
        Args:
            deck_cards_dict: Dictionary mapping deck names to list of card names.
                           If None, will attempt to extract from ml_data.
        
        Returns:
            DataFrame with enriched features
        """
        if self.ml_data is None:
            self.load_ml_data()
        
        print("\n=== Enriching Data with Card Features ===")
        
        # If deck_cards_dict not provided, create sample enrichment with aggregated stats
        if deck_cards_dict is None:
            print("No deck card lists provided. Adding aggregated card database statistics...")
            
            # Load card data if not already loaded
            if self.card_extractor.card_data is None:
                self.card_extractor.load_card_data()
            
            # Calculate global card statistics for Mechanologist cards
            mech_cards = self.card_extractor.card_data[
                self.card_extractor.card_data['Types'].str.contains('Mechanologist', na=False)
            ]
            
            # Add global statistics as features
            enriched_data = self.ml_data.copy()
            
            # Average stats for Mechanologist cards
            enriched_data['mech_avg_pitch'] = mech_cards['Pitch'].mean()
            enriched_data['mech_avg_cost'] = pd.to_numeric(mech_cards['Cost'], errors='coerce').mean()
            enriched_data['mech_avg_power'] = pd.to_numeric(mech_cards['Power'], errors='coerce').mean()
            enriched_data['mech_avg_defense'] = pd.to_numeric(mech_cards['Defense'], errors='coerce').mean()
            
            # Count of card types
            enriched_data['mech_equipment_count'] = (mech_cards['Types'].str.contains('Equipment', na=False)).sum()
            enriched_data['mech_action_count'] = (mech_cards['Types'].str.contains('Action', na=False)).sum()
            enriched_data['mech_attack_count'] = (mech_cards['Types'].str.contains('Attack', na=False)).sum()
            
            # Count of common keywords
            enriched_data['mech_boost_cards'] = (mech_cards['Card Keywords'].str.contains('Boost', na=False)).sum()
            enriched_data['mech_go_again_cards'] = (mech_cards['Card Keywords'].str.contains('Go again', na=False)).sum()
            
            print(f"Added {len([c for c in enriched_data.columns if c.startswith('mech_')])} card feature columns")
            
        else:
            # Use provided deck card lists to extract specific features
            print(f"Processing {len(deck_cards_dict)} decks with specific card lists...")
            
            enriched_data = self.ml_data.copy()
            
            # Extract features for each deck
            for deck_name, card_list in deck_cards_dict.items():
                if deck_name not in enriched_data['deck_name'].values:
                    continue
                
                # Get aggregated features for this deck
                deck_features = self.card_extractor.aggregate_deck_features(card_list)
                
                # Add features to the row for this deck
                for feature_name, feature_value in deck_features.items():
                    enriched_data.loc[enriched_data['deck_name'] == deck_name, feature_name] = feature_value
            
            print(f"Added deck-specific card features")
        
        # Fill any NaN values with 0
        enriched_data = enriched_data.fillna(0)
        
        print(f"Enriched dataset shape: {enriched_data.shape}")
        print(f"Total features: {len(enriched_data.columns)}")
        
        return enriched_data
    
    def export_for_sagemaker(self, target_column: str = 'avg_win_rate', 
                            include_card_features: bool = True,
                            deck_cards_dict: Optional[Dict[str, List[str]]] = None) -> str:
        """Export processed data in format suitable for AWS SageMaker
        
        Args:
            target_column: The target variable to predict
            include_card_features: Whether to include card features from card.csv
            deck_cards_dict: Optional dictionary mapping deck names to card lists
        
        Returns:
            Path to exported CSV file
        """
        if self.ml_data is None:
            self.load_ml_data()
        
        # Enrich with card features if requested
        if include_card_features:
            ml_data_enriched = self.enrich_with_card_features(deck_cards_dict)
        else:
            ml_data_enriched = self.ml_data.copy()
        
        # Prepare features for ML
        base_feature_columns = [
            'AI', 'Nano', 'Quantum', 'Base',
            '0_cost', '1_cost', '2_cost', '3_cost', '4_plus_cost',
            'equipment', 'item', 'action',
            'avg_turns', 'avg_evos', 'avg_teklo_energy',
            'avg_nanite_counters', 'avg_quantum_charges',
            'consistency_score', 'avg_expert_balance_score'
        ]
        
        # Add card features if they exist
        card_feature_columns = [col for col in ml_data_enriched.columns 
                               if col.startswith('mech_') or 
                                  col.startswith('avg_') or 
                                  col.startswith('max_') or 
                                  col.startswith('count_')]
        
        # Combine all features
        all_feature_columns = base_feature_columns + card_feature_columns
        available_features = [col for col in all_feature_columns if col in ml_data_enriched.columns]
        
        # Remove duplicate columns
        available_features = list(dict.fromkeys(available_features))
        
        # Create final dataset with target first (SageMaker convention)
        ml_export = ml_data_enriched[[target_column] + available_features].copy()
        
        # Handle missing values
        ml_export = ml_export.fillna(ml_export.mean())
        
        # Save for SageMaker
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_path = self.data_path / "processed" / f"sagemaker_training_data_{timestamp}.csv"
        ml_export.to_csv(export_path, index=False, header=False)  # SageMaker expects no headers
        
        print(f"\n=== SageMaker Export Complete ===")
        print(f"Export path: {export_path}")
        print(f"Target: {target_column}")
        print(f"Total features: {len(available_features)}")
        print(f"  - Base features: {len([f for f in available_features if f in base_feature_columns])}")
        print(f"  - Card features: {len([f for f in available_features if f not in base_feature_columns])}")
        print(f"Dataset shape: {ml_export.shape}")
        
        return str(export_path)


# Usage example and testing functions
def run_comprehensive_analysis(data_path: str = "../data") -> None:
    """Run complete analysis pipeline"""
    analyzer = TekloDataAnalyzer(data_path)
    
    try:
        # Load data
        print("Loading simulation data...")
        analyzer.load_simulation_data()
        analyzer.load_ml_data()
        
        # Calculate metrics
        print("\nCalculating advanced metrics...")
        metrics = analyzer.calculate_advanced_metrics()
        
        # Generate report
        print("\nGenerating comprehensive report...")
        report_path = analyzer.data_path / "processed" / f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        analyzer.generate_comprehensive_report(str(report_path))
        
        # Create visualizations
        print("\nCreating advanced visualizations...")
        analyzer.create_advanced_visualizations()
        
        # Clustering analysis
        print("\nPerforming clustering analysis...")
        cluster_results = analyzer.perform_clustering_analysis()
        
        # Export for SageMaker
        print("\nExporting data for AWS SageMaker...")
        sagemaker_path = analyzer.export_for_sagemaker()
        
        print("\n=== ANALYSIS COMPLETE ===")
        print(f"Report saved to: {report_path}")
        print(f"SageMaker data ready at: {sagemaker_path}")
        print("Ready for ML model training!")
        
    except Exception as e:
        print(f"Analysis failed: {e}")
        print("Make sure to run the gameplay simulator first to generate data.")


if __name__ == "__main__":
    # Run comprehensive analysis
    run_comprehensive_analysis()
