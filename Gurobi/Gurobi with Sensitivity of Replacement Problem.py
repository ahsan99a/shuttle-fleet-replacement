# -*- coding: utf-8 -*-
"""
Created on Mon Dec  9 00:47:41 2024

@author: Ahsanul
"""

from gurobipy import Model, GRB, quicksum
import pandas as pd

# Number of years
years = 6

# Bus types
buses = [1, 2, 3]

# Cost data
c = {
    1: {(1, 2): 80, (1, 3): 130, (1, 4): 190, (1, 5): 280, (1, 6): 400, (2, 3): 80, (2, 4): 130, (2, 5): 190, (2, 6): 280,
        (3, 4): 80, (3, 5): 130, (3, 6): 190, (4, 5): 80, (4, 6): 130, (5, 6): 80},
    2: {(1, 2): 105, (1, 3): 181, (1, 4): 272, (1, 5): 373, (1, 6): 505, (2, 3): 105, (2, 4): 181, (2, 5): 272, (2, 6): 373,
        (3, 4): 105, (3, 5): 181, (3, 6): 272, (4, 5): 105, (4, 6): 181, (5, 6): 105},
    3: {(1, 2): 155, (1, 3): 270, (1, 4): 405, (1, 5): 475, (1, 6): 735, (2, 3): 155, (2, 4): 270, (2, 5): 405, (2, 6): 475,
        (3, 4): 155, (3, 5): 270, (3, 6): 405, (4, 5): 155, (4, 6): 270, (5, 6): 155}
}

# Fleet size
fleet_size = {1: 8, 2: 4, 3: 37}

# Annual budget
annual_budget = 28000

# Initialize the model
model = Model("BusReplacement")

# Decision variables
x = model.addVars(
    [(i, j, k) for k in buses for i in range(1, years) for j in range(i + 1, years + 1)],
    vtype=GRB.CONTINUOUS, name="x"
)

# Objective: Minimize total cost
model.setObjective(
    quicksum(c[k][(i, j)] * x[i, j, k] * fleet_size[k] for k in buses for i in range(1, years) for j in range(i + 1, years + 1)),
    GRB.MINIMIZE
)

# Constraints
for k in buses:
    model.addConstr(quicksum(x[1, j, k] for j in range(2, years + 1)) == 1, name=f"StartFlow_{k}")
    model.addConstr(quicksum(x[i, years, k] for i in range(1, years)) == 1, name=f"EndFlow_{k}")
    for t in range(2, years):
        model.addConstr(
            quicksum(x[i, t, k] for i in range(1, t)) == quicksum(x[t, j, k] for j in range(t + 1, years + 1)),
            name=f"FlowBalance_{t}_{k}"
        )

for t in range(1, years):
    total_cost_in_year = quicksum(c[k][(t, j)] * x[t, j, k] for k in buses for j in range(t + 1, years + 1))
    model.addConstr(total_cost_in_year <= annual_budget, name=f"Budget_Constraint_Year_{t}")

# Solve the model
model.optimize()

# Prepare data for saving
replacement_details = []
year_summary = []
decision_var_sensitivity = []
constraint_sensitivity = []

if model.status == GRB.OPTIMAL:
    total_cost = round(model.objVal, 2)
    print("\nOptimal solution found!")
    print("=" * 50)
    print(f"Total Optimal Cost: {total_cost}")

    # Collect replacement details
    total_replacements = 0
    replacements_per_year = {t: {k: 0 for k in buses} for t in range(1, years)}

    print("\nReplacement Details:")
    for k in buses:
        for i in range(1, years):
            for j in range(i + 1, years + 1):
                if x[i, j, k].x > 0.5:
                    replacement_details.append({"Bus Type": k, "From Year": i, "To Year": j})
                    print(f"  Bus Type {k}: Replace from year {i} to year {j}")
                    total_replacements += 1
                    replacements_per_year[i][k] += 1

    print("\nYearly Summary:")
    for t in range(1, years):
        total_replacements_year = sum(replacements_per_year[t].values())
        year_summary.append({"Year": t, "Total Replacements": total_replacements_year})
        print(f"  Year {t}: Total Replacements = {total_replacements_year}, " +
              ", ".join([f"Bus Type {k} = {replacements_per_year[t][k]}" for k in buses]))

    print(f"\nTotal Optimal Cost: {total_cost}")
    print(f"Total Count of Bus Replacements: {total_replacements}")

    # Collect decision variable sensitivity
    print("\nSensitivity Analysis for Decision Variables:")
    print(f"{'Variable':<15}{'Value':<15}{'Reduced Cost':<15}{'Objective':<15}{'SAObjLow':<15}{'SAObjUp':<15}")
    for v in model.getVars():
        decision_var_sensitivity.append({
            "Variable": v.varName,
            "Value": round(v.x, 2),
            "Reduced Cost": round(v.RC, 2),
            "Objective": round(v.Obj, 2),
            "SAObjLow": round(v.SAObjLow, 2),
            "SAObjUp": round(v.SAObjUp, 2)
        })
        print(f"{v.varName:<15}{round(v.x, 2):<15}{round(v.RC, 2):<15}{round(v.Obj, 2):<15}{round(v.SAObjLow, 2):<15}{round(v.SAObjUp, 2):<15}")

    # Collect constraint sensitivity
    print("\nSensitivity Analysis for Constraints:")
    print(f"{'Constraint':<25}{'Sense':<10}{'Shadow Price':<15}{'Slack':<15}{'RHS':<15}{'SARHSLow':<15}{'SARHSUp':<15}")
    for c in model.getConstrs():
        constraint_sensitivity.append({
            "Constraint": c.constrName,
            "Sense": c.Sense,
            "Shadow Price": round(c.Pi, 2),
            "Slack": round(c.Slack, 2),
            "RHS": round(c.RHS, 2),
            "SARHSLow": round(c.SARHSLow, 2),
            "SARHSUp": round(c.SARHSUp, 2)
        })
        print(f"{c.constrName:<25}{c.Sense:<10}{round(c.Pi, 2):<15}{round(c.Slack, 2):<15}{round(c.RHS, 2):<15}{round(c.SARHSLow, 2):<15}{round(c.SARHSUp, 2):<15}")

    # Save to Excel
    file_name = "Bus_Replacement_Results_Sensitivity.xlsx"
    with pd.ExcelWriter(file_name, engine="openpyxl") as writer:
        pd.DataFrame(replacement_details).to_excel(writer, sheet_name="Replacement Details", index=False)
        pd.DataFrame(year_summary).to_excel(writer, sheet_name="Yearly Summary", index=False)
        pd.DataFrame(decision_var_sensitivity).to_excel(writer, sheet_name="Decision Sensitivity", index=False)
        pd.DataFrame(constraint_sensitivity).to_excel(writer, sheet_name="Constraint Sensitivity", index=False)

    print(f"\nResults saved to {file_name}")
else:
    print("No optimal solution found.")
