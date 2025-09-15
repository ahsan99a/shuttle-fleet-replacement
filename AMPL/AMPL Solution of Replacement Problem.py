# -*- coding: utf-8 -*-
"""
Created on Mon Dec  9 00:58:30 2024

@author: Mukit Emon
"""

from amplpy import AMPL, Environment
import time


# Start timing the program
start_time = time.time()

# Initialize AMPL environment
ampl = AMPL(Environment('C:/Users/Tanbi/AMPL'))  # Adjust the path to your AMPL installation

# Define the AMPL model inline
ampl.eval(r"""
    set YEARS;
    set BUSES;
    set ARCS within {YEARS, YEARS, BUSES};

    param cost {ARCS} >= 0;         # Replacement cost for each arc
    param fleet_size {BUSES} > 0;  # Fleet size for each bus type
    param budget >= 0;             # Single annual budget for all years

    var x {ARCS} binary;           # Replacement decision (binary: 0 or 1)

    minimize Total_Cost:
        sum {i in YEARS, j in YEARS, k in BUSES : (i, j, k) in ARCS} cost[i, j, k] * x[i, j, k] * fleet_size[k];

    subject to Start_Flow {k in BUSES}:
        sum {j in YEARS : (1, j, k) in ARCS} x[1, j, k] = 1;

    subject to End_Flow {k in BUSES}:
        sum {i in YEARS : (i, card(YEARS), k) in ARCS} x[i, card(YEARS), k] = 1;

    subject to Intermediate_Flow {t in YEARS diff {1, card(YEARS)}, k in BUSES}:
        sum {i in YEARS : (i, t, k) in ARCS} x[i, t, k] =
        sum {j in YEARS : (t, j, k) in ARCS} x[t, j, k];

    subject to Budget_Constraint:
        sum {t in YEARS, j in YEARS, k in BUSES : (t, j, k) in ARCS} cost[t, j, k] * x[t, j, k] <= budget;
""")

# Data generation using Pandas
years = [1, 2, 3, 4, 5, 6]
buses = [1, 2, 3]

arcs = [
    (1, 2, 1), (1, 3, 1), (1, 4, 1), (1, 5, 1), (1, 6, 1),
    (2, 3, 1), (2, 4, 1), (2, 5, 1), (2, 6, 1),
    (3, 4, 1), (3, 5, 1), (3, 6, 1),
    (4, 5, 1), (4, 6, 1), (5, 6, 1),
    (1, 2, 2), (1, 3, 2), (1, 4, 2), (1, 5, 2), (1, 6, 2),
    (2, 3, 2), (2, 4, 2), (2, 5, 2), (2, 6, 2),
    (3, 4, 2), (3, 5, 2), (3, 6, 2),
    (4, 5, 2), (4, 6, 2), (5, 6, 2),
    (1, 2, 3), (1, 3, 3), (1, 4, 3), (1, 5, 3), (1, 6, 3),
    (2, 3, 3), (2, 4, 3), (2, 5, 3), (2, 6, 3),
    (3, 4, 3), (3, 5, 3), (3, 6, 3),
    (4, 5, 3), (4, 6, 3), (5, 6, 3)
]

cost_data = {
    (1, 2, 1): 80, (1, 3, 1):130 , (1, 4, 1): 190, (1, 5, 1): 280, (1, 6, 1): 400,
    (2, 3, 1): 80, (2, 4, 1): 130, (2, 5, 1): 190, (2, 6, 1): 280,
    (3, 4, 1): 80, (3, 5, 1): 130, (3, 6, 1): 190,
    (4, 5, 1): 80, (4, 6, 1): 130, (5, 6, 1): 80,
    (1, 2, 2): 105, (1, 3, 2):181, (1, 4, 2):272, (1, 5, 2): 373, (1, 6, 2): 505,
    (2, 3, 2): 105, (2, 4, 2): 181, (2, 5, 2): 272, (2, 6, 2): 373,
    (3, 4, 2): 105, (3, 5, 2): 181, (3, 6, 2): 272,
    (4, 5, 2): 105, (4, 6, 2): 181, (5, 6, 2): 105,
    (1, 2, 3): 155, (1, 3, 3):270, (1, 4, 3):405, (1, 5, 3):475, (1, 6, 3):735,
    (2, 3, 3): 155, (2, 4, 3): 270, (2, 5, 3): 405, (2, 6, 3): 475,
    (3, 4, 3): 155, (3, 5, 3): 270, (3, 6, 3): 405,
    (4, 5, 3): 155, (4, 6, 3):270, (5, 6, 3): 155
}

fleet_size = {1: 8, 2: 4, 3: 37}
annual_budget = 28000

# Load data into AMPL
ampl.set['YEARS'] = years
ampl.set['BUSES'] = buses
ampl.set['ARCS'] = arcs
ampl.param['cost'] = cost_data
ampl.param['fleet_size'] = fleet_size
ampl.param['budget'] = annual_budget

# Solve the model with Gurobi solver
ampl.setOption('solver', 'gurobi')
ampl.solve()

# Extracting and printing results
total_cost = ampl.getObjective('Total_Cost').value()
replacement_decisions = ampl.getVariable('x').getValues().toPandas()

# Print results
print(f"\nOptimal Replacement Schedule for Bus Fleet:\n{'=' * 50}")
print(f"Total Cost of the Optimal Fleet Replacement Plan: {total_cost:.2f}")
print("\nReplacement Decisions (Year-to-Year Assignments):")
print(replacement_decisions[replacement_decisions['x.val'] > 0.5])  # Filter only active decisions
print(f"\nProgram completed in {time.time() - start_time:.2f} seconds.")
