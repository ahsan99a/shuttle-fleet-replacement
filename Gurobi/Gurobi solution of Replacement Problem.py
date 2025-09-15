# -*- coding: utf-8 -*-
"""
Created on Mon Dec  9 00:52:42 2024

@author: Ahsanul
"""

from gurobipy import Model, GRB, quicksum
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font

# Number of years
years = 6

# Bus types
buses = [1, 2, 3]

# Bus names mapping
bus_names = {
    1: "40-inch Flyers",
    2: "60-inch Flyers",
    3: "El-Dorado"
}

# Cost data
cost = {
    1: {(1, 2): 80, (1, 3): 130, (1, 4): 190, (1, 5): 280, (1, 6): 400, (2, 3): 80, (2, 4): 130, (2, 5): 190, (2, 6): 280,
        (3, 4): 80, (3, 5): 130, (3, 6): 190, (4, 5): 80, (4, 6): 130, (5, 6): 80},
    2: {(1, 2): 105, (1, 3): 181, (1, 4): 272, (1, 5): 373, (1, 6): 505, (2, 3): 105, (2, 4): 181, (2, 5): 272, (2, 6): 373,
        (3, 4): 105, (3, 5): 181, (3, 6): 272, (4, 5): 105, (4, 6): 181, (5, 6): 105},
    3: {(1, 2): 155, (1, 3): 270, (1, 4): 405, (1, 5): 475, (1, 6): 735, (2, 3): 155, (2, 4): 270, (2, 5): 405, (2, 6): 475,
        (3, 4): 155, (3, 5): 270, (3, 6): 405, (4, 5): 155, (4, 6): 270, (5, 6): 155}
}

# Fleet size
fleet_size = {1: 8, 2: 4, 3: 37}

# Total budget
total_budget = 28000

# Initialize the model
model = Model("BusReplacement")

# Decision variables
Binary_decision = model.addVars(
    [(i, j, k) for k in buses for i in range(1, years) for j in range(i + 1, years + 1)],
    vtype=GRB.BINARY, name="x"
)

# Objective: Minimize total cost
model.setObjective(
    quicksum(cost[k][(i, j)] * Binary_decision[i, j, k] * fleet_size[k] for k in buses for i in range(1, years) for j in range(i + 1, years + 1)),
    GRB.MINIMIZE
)

# Constraints
for k in buses:
    model.addConstr(quicksum(Binary_decision[1, j, k] for j in range(2, years + 1)) == 1, name=f"StartFlow_{k}")
    model.addConstr(quicksum(Binary_decision[i, years, k] for i in range(1, years)) == 1, name=f"EndFlow_{k}")
    for t in range(2, years):
        model.addConstr(
            quicksum(Binary_decision[i, t, k] for i in range(1, t)) == quicksum(Binary_decision[t, j, k] for j in range(t + 1, years + 1)),
            name=f"FlowBalance_{t}_{k}"
        )

for t in range(1, years):
    total_cost_in_year = quicksum(cost[k][(t, j)] * Binary_decision[t, j, k] for k in buses for j in range(t + 1, years + 1))
    model.addConstr(total_cost_in_year <= total_budget, name=f"Budget_Constraint_Year_{t}")

# Solve the model
model.optimize()

# Prepare data structures for results
replacement_details = []
cost_breakdown = []
year_data = []
total_cost_per_year = {t: 0 for t in range(1, years)}

if model.status == GRB.OPTIMAL:
    total_cost = round(model.objVal, 2)
    total_replacements = 0

    print("\nOptimal solution found!")
    print(f"Total Optimal Cost: {total_cost}\n")

    # Replacement details
    print("Replacement Details:")
    for k in buses:
        for i in range(1, years):
            for j in range(i + 1, years + 1):
                if Binary_decision[i, j, k].x > 0.5:
                    bus_name = bus_names[k]
                    replacement_details.append({"Bus Name": bus_name, "From Year": i, "To Year": j})
                    total_arc_cost = cost[k][(i, j)] * fleet_size[k]
                    total_cost_per_year[i] += total_arc_cost
                    total_replacements += 1
                    cost_breakdown.append({
                        "Bus Name": bus_name, "From Year": i, "To Year": j, "Total Cost": total_arc_cost
                    })
                    print(f"  {bus_name}: Replace from year {i} to year {j} (Cost: {total_arc_cost})")

    print("\nYearly Summary:")
    for t in range(1, years):
        year_data.append({
            "Year": t,
            "Total Replacements": sum(1 for d in replacement_details if d["From Year"] == t),
            "Total Cost": total_cost_per_year[t]
        })
        print(f"  Year {t}: Total Replacements = {year_data[-1]['Total Replacements']}, Total Cost = {year_data[-1]['Total Cost']}")

    # Prepare DataFrames
    df_replacement_details = pd.DataFrame(replacement_details)
    df_year_summary = pd.DataFrame(year_data)
    df_total_cost = pd.DataFrame([{"Total Optimal Cost": total_cost, "Total Replacements": total_replacements}])
    df_cost_breakdown = pd.DataFrame(cost_breakdown)

    # Save to Excel
    file_name = "Bus_Replacement_Results with gurobi.xlsx"
    with pd.ExcelWriter(file_name, engine="openpyxl") as writer:
        df_total_cost.to_excel(writer, sheet_name="Total Summary", index=False, startrow=1)
        df_year_summary.to_excel(writer, sheet_name="Yearly Summary", index=False, startrow=1)
        df_replacement_details.to_excel(writer, sheet_name="Replacement Details", index=False, startrow=1)
        df_cost_breakdown.to_excel(writer, sheet_name="Cost Breakdown", index=False, startrow=1)

    # Add titles and formatting
    wb = load_workbook(file_name)
    def add_title(sheet_name, title):
        sheet = wb[sheet_name]
        sheet["A1"] = title
        sheet["A1"].font = Font(bold=True, size=14)

    add_title("Total Summary", "Total Summary of Optimal Cost and Replacements")
    add_title("Yearly Summary", "Yearly Summary of Replacements and Costs")
    add_title("Replacement Details", "Detailed Replacement Plan")
    add_title("Cost Breakdown", "Cost Breakdown of Replacements")
    wb.save(file_name)

    print(f"\nResults saved to {file_name}")
else:
    print("No optimal solution found.")
