from code_substitution_tool import CodeSubstitutionTool

# Initialize tool
tool = CodeSubstitutionTool("/Users/jiawei/Downloads/Project/Data/OR-Instruct-Data-3K-Gurobipy.jsonl")

# View a specific record
record = tool.get_record_by_index(763)

# Extract code from completion
code = tool.extract_code_from_completion(record['completion'])

# Substitute code programmatically
new_code = """
import gurobipy as gp
from gurobipy import GRB

# Create a Gurobi environment
env = gp.Env()

# Create a Gurobi model
model = gp.Model("WasteHeatRecovery")

# Define cost constants for each factory
cost_A = 20
cost_B = 30
cost_C = 40

# Add variables
xA = model.addVar(lb=0, ub=30, vtype=GRB.CONTINUOUS, name="xA")
xB = model.addVar(lb=0, ub=40, vtype=GRB.CONTINUOUS, name="xB")
xC = model.addVar(lb=0, ub=50, vtype=GRB.CONTINUOUS, name="xC")

# Add efficiency variables and binary variables for piecewise efficiency function
# For factory A (efficiency tiers: 0.6 for x<=20, 0.7 for 20<x<=30)
yA1 = model.addVar(lb=0, ub=20, vtype=GRB.CONTINUOUS, name="yA1")  # x in [0,20] with efficiency 0.6
yA2 = model.addVar(lb=0, ub=10, vtype=GRB.CONTINUOUS, name="yA2")  # x in (20,30] with efficiency 0.7
model.addConstr(xA == yA1 + yA2, name="xA_decomposition")

# For factory B (efficiency tiers: 0.6 for x<=20, 0.7 for 20<x<=40)
yB1 = model.addVar(lb=0, ub=20, vtype=GRB.CONTINUOUS, name="yB1")  # x in [0,20] with efficiency 0.6
yB2 = model.addVar(lb=0, ub=20, vtype=GRB.CONTINUOUS, name="yB2")  # x in (20,40] with efficiency 0.7
model.addConstr(xB == yB1 + yB2, name="xB_decomposition")

# For factory C (efficiency tiers: 0.6 for x<=20, 0.7 for 20<x<=40, 0.8 for 40<x<=50)
yC1 = model.addVar(lb=0, ub=20, vtype=GRB.CONTINUOUS, name="yC1")  # x in [0,20] with efficiency 0.6
yC2 = model.addVar(lb=0, ub=20, vtype=GRB.CONTINUOUS, name="yC2")  # x in (20,40] with efficiency 0.7
yC3 = model.addVar(lb=0, ub=10, vtype=GRB.CONTINUOUS, name="yC3")  # x in (40,50] with efficiency 0.8
model.addConstr(xC == yC1 + yC2 + yC3, name="xC_decomposition")

# Add constraints
model.addConstr(xA <= 30, name="WasteHeatA")
model.addConstr(xB <= 40, name="WasteHeatB") 
model.addConstr(xC <= 50, name="WasteHeatC")

# Budget constraints (cost is constant per factory)
model.addConstr(cost_A <= 20, name="BudgetA")  # This is always satisfied (20 <= 20)
model.addConstr(cost_B <= 30, name="BudgetB")  # This is always satisfied (30 <= 30)
model.addConstr(cost_C <= 40, name="BudgetC")  # This is always satisfied (40 <= 40)

# Set the objective using piecewise linear efficiency
model.setObjective(0.6*yA1 + 0.7*yA2 + 0.6*yB1 + 0.7*yB2 + 0.6*yC1 + 0.7*yC2 + 0.8*yC3, sense=GRB.MAXIMIZE)

# Solve the model
model.optimize()

# Analyze the solution
if model.status == GRB.OPTIMAL:
    print("Maximum total waste heat recovery: {:.2f} gigajoules".format(model.ObjVal))
    print("Optimal planning scheme:")
    print("Factory A: {:.2f} gigajoules".format(xA.x))
    print("Factory B: {:.2f} gigajoules".format(xB.x))  
    print("Factory C: {:.2f} gigajoules".format(xC.x))
    
    # Calculate efficiency for each factory
    def get_efficiency(x_val):
        if x_val <= 20:
            return 0.6
        elif x_val <= 40:
            return 0.7
        else:
            return 0.8
    
    effA = get_efficiency(xA.x)
    effB = get_efficiency(xB.x)
    effC = get_efficiency(xC.x)
    
    print("Efficiency details:")
    print("Factory A efficiency: {:.1f}".format(effA))
    print("Factory B efficiency: {:.1f}".format(effB))
    print("Factory C efficiency: {:.1f}".format(effC))
    
    print("Total construction cost: {:.2f} million".format(cost_A + cost_B + cost_C))
    print("Individual costs - A: {:.2f}, B: {:.2f}, C: {:.2f} million".format(cost_A, cost_B, cost_C))
else:
    print("No optimal solution found.")
"""
tool.substitute_code_by_index(763, new_code)
tool.save_data()