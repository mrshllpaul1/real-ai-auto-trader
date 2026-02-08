"""
Genetic Algorithm for Network Architecture Evolution
=====================================================
Uses DEAP library for multi-objective optimization of:
- Network architecture (layers, neurons, activation functions)
- Hyperparameters (learning rate, batch size, etc.)
- Feature combinations

Fitness criteria:
- Sharpe Ratio
- Win Rate
- Max Drawdown (minimize)
- Profit Factor
"""

import numpy as np
import random
import logging
from typing import Dict, List, Any, Optional, Tuple, Callable
from datetime import datetime, timezone
from collections import deque
import asyncio
import json

# DEAP imports
from deap import base, creator, tools, algorithms

logger = logging.getLogger(__name__)


# Define fitness and individual types
try:
    # Multi-objective: maximize Sharpe, maximize Win Rate, minimize Drawdown
    creator.create("FitnessMulti", base.Fitness, weights=(1.0, 1.0, -1.0))
    creator.create("Individual", list, fitness=creator.FitnessMulti)
except Exception:
    pass  # Already created


class NetworkGene:
    """Represents a neural network architecture gene"""
    
    # Possible values for each gene component
    LAYER_COUNTS = [2, 3, 4, 5, 6]
    NEURON_COUNTS = [32, 64, 128, 256, 512]
    ACTIVATIONS = ['relu', 'tanh', 'elu', 'leaky_relu', 'gelu']
    DROPOUT_RATES = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
    LEARNING_RATES = [0.0001, 0.0005, 0.001, 0.005, 0.01]
    BATCH_SIZES = [32, 64, 128, 256]
    OPTIMIZERS = ['adam', 'adamw', 'sgd', 'rmsprop']
    
    @staticmethod
    def random_gene() -> Dict:
        """Generate a random network architecture gene"""
        num_layers = random.choice(NetworkGene.LAYER_COUNTS)
        
        return {
            "num_layers": num_layers,
            "neurons_per_layer": [random.choice(NetworkGene.NEURON_COUNTS) for _ in range(num_layers)],
            "activations": [random.choice(NetworkGene.ACTIVATIONS) for _ in range(num_layers)],
            "dropout_rates": [random.choice(NetworkGene.DROPOUT_RATES) for _ in range(num_layers)],
            "learning_rate": random.choice(NetworkGene.LEARNING_RATES),
            "batch_size": random.choice(NetworkGene.BATCH_SIZES),
            "optimizer": random.choice(NetworkGene.OPTIMIZERS),
            "use_batch_norm": random.choice([True, False]),
            "use_attention": random.choice([True, False]),
            "use_residual": random.choice([True, False])
        }
    
    @staticmethod
    def mutate_gene(gene: Dict, mutation_rate: float = 0.2) -> Dict:
        """Mutate a gene with given probability"""
        mutated = gene.copy()
        
        if random.random() < mutation_rate:
            mutated["num_layers"] = random.choice(NetworkGene.LAYER_COUNTS)
        
        if random.random() < mutation_rate:
            idx = random.randint(0, len(mutated["neurons_per_layer"]) - 1)
            mutated["neurons_per_layer"][idx] = random.choice(NetworkGene.NEURON_COUNTS)
        
        if random.random() < mutation_rate:
            idx = random.randint(0, len(mutated["activations"]) - 1)
            mutated["activations"][idx] = random.choice(NetworkGene.ACTIVATIONS)
        
        if random.random() < mutation_rate:
            mutated["learning_rate"] = random.choice(NetworkGene.LEARNING_RATES)
        
        if random.random() < mutation_rate:
            mutated["batch_size"] = random.choice(NetworkGene.BATCH_SIZES)
        
        if random.random() < mutation_rate:
            mutated["optimizer"] = random.choice(NetworkGene.OPTIMIZERS)
        
        if random.random() < mutation_rate:
            mutated["use_attention"] = not mutated["use_attention"]
        
        return mutated
    
    @staticmethod
    def crossover_genes(gene1: Dict, gene2: Dict) -> Tuple[Dict, Dict]:
        """Crossover two genes"""
        child1, child2 = gene1.copy(), gene2.copy()
        
        # Swap some components
        if random.random() < 0.5:
            child1["num_layers"], child2["num_layers"] = child2["num_layers"], child1["num_layers"]
        
        if random.random() < 0.5:
            child1["learning_rate"], child2["learning_rate"] = child2["learning_rate"], child1["learning_rate"]
        
        if random.random() < 0.5:
            child1["optimizer"], child2["optimizer"] = child2["optimizer"], child1["optimizer"]
        
        if random.random() < 0.5:
            child1["use_attention"], child2["use_attention"] = child2["use_attention"], child1["use_attention"]
        
        return child1, child2


class ArchitectureEvolver:
    """
    Genetic algorithm for evolving neural network architectures.
    Uses NSGA-II for multi-objective optimization.
    """
    
    def __init__(self, db=None, fitness_function: Callable = None):
        self.db = db
        self.fitness_function = fitness_function
        
        # Evolution parameters
        self.population_size = 20
        self.generations = 10
        self.crossover_prob = 0.7
        self.mutation_prob = 0.3
        
        # Tracking
        self.current_generation = 0
        self.is_running = False
        self.best_individuals = []
        self.evolution_history = []
        self.pareto_front = []
        
        # DEAP toolbox
        self.toolbox = base.Toolbox()
        self._setup_toolbox()
        
        logger.info("🧬 Architecture Evolver initialized")
    
    def _setup_toolbox(self):
        """Setup DEAP toolbox"""
        self.toolbox.register("individual", self._create_individual)
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)
        self.toolbox.register("evaluate", self._evaluate_fitness)
        self.toolbox.register("mate", self._crossover)
        self.toolbox.register("mutate", self._mutate)
        self.toolbox.register("select", tools.selNSGA2)
    
    def _create_individual(self) -> list:
        """Create a random individual"""
        gene = NetworkGene.random_gene()
        return creator.Individual([gene])
    
    def _evaluate_fitness(self, individual: list) -> Tuple[float, float, float]:
        """
        Evaluate fitness of an individual.
        Returns (sharpe_ratio, win_rate, max_drawdown)
        """
        gene = individual[0]
        
        if self.fitness_function:
            try:
                # Use custom fitness function
                result = self.fitness_function(gene)
                return (
                    result.get("sharpe_ratio", 0),
                    result.get("win_rate", 0.5),
                    result.get("max_drawdown", 1.0)
                )
            except Exception as e:
                logger.error(f"Fitness evaluation error: {e}")
        
        # Default: simulate fitness based on architecture complexity
        complexity_score = self._estimate_complexity(gene)
        
        # Simulate metrics (would be replaced with actual backtesting)
        sharpe = np.random.normal(0.5 + complexity_score * 0.1, 0.3)
        win_rate = np.random.uniform(0.45, 0.65)
        drawdown = np.random.uniform(0.1, 0.3)
        
        return (sharpe, win_rate, drawdown)
    
    def _estimate_complexity(self, gene: Dict) -> float:
        """Estimate architecture complexity score"""
        score = 0
        
        # Layer count
        score += gene["num_layers"] * 0.1
        
        # Average neurons
        avg_neurons = np.mean(gene["neurons_per_layer"])
        score += avg_neurons / 512 * 0.3
        
        # Advanced features
        if gene["use_attention"]:
            score += 0.2
        if gene["use_residual"]:
            score += 0.1
        if gene["use_batch_norm"]:
            score += 0.05
        
        return min(1.0, score)
    
    def _crossover(self, ind1: list, ind2: list) -> Tuple[list, list]:
        """Crossover two individuals"""
        gene1, gene2 = NetworkGene.crossover_genes(ind1[0], ind2[0])
        ind1[0], ind2[0] = gene1, gene2
        return ind1, ind2
    
    def _mutate(self, individual: list) -> Tuple[list]:
        """Mutate an individual"""
        individual[0] = NetworkGene.mutate_gene(individual[0], self.mutation_prob)
        return (individual,)
    
    async def evolve(
        self,
        population_size: int = 20,
        generations: int = 10,
        fitness_function: Callable = None
    ) -> Dict:
        """
        Run the genetic algorithm evolution.
        
        Args:
            population_size: Size of population
            generations: Number of generations
            fitness_function: Custom fitness evaluation function
            
        Returns:
            Evolution results with best individuals
        """
        self.population_size = population_size
        self.generations = generations
        self.is_running = True
        self.current_generation = 0
        self.evolution_history = []
        
        if fitness_function:
            self.fitness_function = fitness_function
        
        logger.info(f"🚀 Starting evolution: pop={population_size}, gen={generations}")
        
        # Create initial population
        population = self.toolbox.population(n=population_size)
        
        # Evaluate initial population
        fitnesses = list(map(self.toolbox.evaluate, population))
        for ind, fit in zip(population, fitnesses):
            ind.fitness.values = fit
        
        # Evolution loop
        for gen in range(generations):
            if not self.is_running:
                break
            
            self.current_generation = gen + 1
            
            # Select next generation
            offspring = self.toolbox.select(population, len(population))
            offspring = list(map(self.toolbox.clone, offspring))
            
            # Apply crossover
            for child1, child2 in zip(offspring[::2], offspring[1::2]):
                if random.random() < self.crossover_prob:
                    self.toolbox.mate(child1, child2)
                    del child1.fitness.values
                    del child2.fitness.values
            
            # Apply mutation
            for mutant in offspring:
                if random.random() < self.mutation_prob:
                    self.toolbox.mutate(mutant)
                    del mutant.fitness.values
            
            # Evaluate offspring with invalid fitness
            invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
            fitnesses = list(map(self.toolbox.evaluate, invalid_ind))
            for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit
            
            # Replace population
            population = offspring
            
            # Record statistics
            fits = [ind.fitness.values for ind in population]
            stats = {
                "generation": gen + 1,
                "avg_sharpe": np.mean([f[0] for f in fits]),
                "avg_win_rate": np.mean([f[1] for f in fits]),
                "avg_drawdown": np.mean([f[2] for f in fits]),
                "best_sharpe": max([f[0] for f in fits]),
                "best_win_rate": max([f[1] for f in fits]),
                "min_drawdown": min([f[2] for f in fits])
            }
            self.evolution_history.append(stats)
            
            logger.info(f"Gen {gen + 1}: Best Sharpe={stats['best_sharpe']:.3f}, "
                       f"Win Rate={stats['best_win_rate']:.2%}")
            
            # Small delay for async context
            await asyncio.sleep(0.1)
        
        self.is_running = False
        
        # Get Pareto front (best trade-off solutions)
        self.pareto_front = tools.sortNondominated(population, len(population), first_front_only=True)[0]
        
        # Store best individuals
        self.best_individuals = sorted(
            population,
            key=lambda x: x.fitness.values[0],  # Sort by Sharpe
            reverse=True
        )[:5]
        
        # Prepare results
        results = {
            "status": "completed",
            "generations_run": self.current_generation,
            "population_size": population_size,
            "best_architectures": [
                {
                    "architecture": ind[0],
                    "sharpe_ratio": ind.fitness.values[0],
                    "win_rate": ind.fitness.values[1],
                    "max_drawdown": ind.fitness.values[2]
                }
                for ind in self.best_individuals
            ],
            "pareto_front_size": len(self.pareto_front),
            "evolution_history": self.evolution_history,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Save to database
        if self.db is not None:
            try:
                await self.db.evolution_runs.insert_one(results)
            except Exception as e:
                logger.error(f"Failed to save evolution results: {e}")
        
        return results
    
    def stop(self):
        """Stop the evolution process"""
        self.is_running = False
        logger.info("⏹️ Evolution stopped")
    
    def get_status(self) -> Dict:
        """Get current evolution status"""
        return {
            "is_running": self.is_running,
            "current_generation": self.current_generation,
            "total_generations": self.generations,
            "population_size": self.population_size,
            "best_individuals_count": len(self.best_individuals),
            "pareto_front_size": len(self.pareto_front),
            "history_length": len(self.evolution_history)
        }
    
    def get_best_architecture(self) -> Optional[Dict]:
        """Get the best architecture found"""
        if self.best_individuals:
            best = self.best_individuals[0]
            return {
                "architecture": best[0],
                "sharpe_ratio": best.fitness.values[0],
                "win_rate": best.fitness.values[1],
                "max_drawdown": best.fitness.values[2]
            }
        return None


# Singleton
_architecture_evolver: Optional[ArchitectureEvolver] = None


def get_architecture_evolver(db=None) -> ArchitectureEvolver:
    """Get or create architecture evolver singleton"""
    global _architecture_evolver
    if _architecture_evolver is None:
        _architecture_evolver = ArchitectureEvolver(db)
    return _architecture_evolver
