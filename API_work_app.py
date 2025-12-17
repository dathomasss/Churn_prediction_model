from flask import Flask, jsonify, request
import pandas as pd
import math

app = Flask(__name__)

# --- DATA LOADING AND PREPARATION ---

DATA_PATH = "/Users/thomas/Documents/Ironhack_final_project/Churn_Modelling.csv" 

try:
    df = pd.read_csv(DATA_PATH)
    df.columns = df.columns.str.lower()
    
    full_customer_data = df.copy()
    
   # Separate dimension tables (as requested by user)
    customer_dim = df[["customerid", "surname"]]
    demographic_dim = df[["customerid", "gender", "geography", "age"]]
    bank_report = df[["customerid", "tenure", "exited"]]
    fin_report = df[["customerid", "estimatedsalary", "balance", "isactivemember", "numofproducts", "hascrcard", "creditscore"]]

except FileNotFoundError:
    print(f"\nFATAL ERROR: Data file not found at path: {DATA_PATH}")
    print("Please check the file path and ensure the file exists.")
    raise # Force l'arrêt du Kernel avec une erreur claire si le fichier est manquant
except Exception as e:
    print(f"General data loading error: {e}")
    raise
    
# ==========================================
# RESOURCE 1: CUSTOMERS (RESTful Resource)
# ==========================================

# Endpoint 1: Collection with Pagination & Filters
@app.route('/api/customers', methods=['GET'])
def get_customers():
    """Returns a paginated list of customers with optional demographic/churn filters."""
    if full_customer_data is None: return jsonify({"error": "No data loaded"}), 500

    # 1. Filtering (e.g., ?geography=France&exited=1)
    filtered_df = full_customer_data.copy()
    
    geo_filter = request.args.get('geography')
    if geo_filter:
        filtered_df = filtered_df[filtered_df['geography'] == geo_filter]
        
    exited_filter = request.args.get('exited')
    if exited_filter:
        # Note: 'exited' is an integer column
        filtered_df = filtered_df[filtered_df['exited'] == int(exited_filter)]

    # 2. Pagination (e.g., ?page=1&per_page=10)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    total_items = len(filtered_df)
    # Calculate total pages, handle division by zero safely
    total_pages = math.ceil(total_items / per_page) if per_page > 0 else 0
    
    start = (page - 1) * per_page
    end = start + per_page
    
    # Slicing the data for the current page
    paginated_data = filtered_df.iloc[start:end]

    return jsonify({
        "resource": "customers",
        "total_items": total_items,
        "total_pages": total_pages,
        "current_page": page,
        "per_page": per_page,
        "data": paginated_data.to_dict(orient='records')
    })

# Endpoint 2: Single Object with Nested Details
@app.route('/api/customers/<int:customer_id>', methods=['GET'])
def get_one_customer(customer_id):
    """Returns detailed information for a single customer, combining data from all dimension tables (Nesting)."""
    
    # Basic search
    cust = customer_dim[customer_dim['customerid'] == customer_id]
    if cust.empty: return jsonify({"error": "Customer not found"}), 404
    
    # Retrieve scattered info (Manual Nesting)
    # .iloc[0] is safe because customerid is unique
    demo = demographic_dim[demographic_dim['customerid'] == customer_id].iloc[0]
    bank = bank_report[bank_report['customerid'] == customer_id].iloc[0]
    fin = fin_report[fin_report['customerid'] == customer_id].iloc[0]
    
    # JSON construction with data type casting for clean output
    response = {
        "identity": {
            "id": int(cust.iloc[0]['customerid']),
            "surname": cust.iloc[0]['surname']
        },
        "demographics": {
            "age": int(demo['age']),
            "gender": demo['gender'],
            "geography": demo['geography']
        },
        "financial_status": {
            "balance": float(fin['balance']),
            "salary": float(fin['estimatedsalary']),
            "products_count": int(fin['numofproducts']),
            "credit_score": int(fin['creditscore'])
        },
        "bank_relation": {
            "churned": bool(bank['exited']),
            "tenure": int(bank['tenure'])
        }
    }
    return jsonify(response)

# ==========================================
# RESOURCE 2: ANALYTICS (Report Queries)
# ==========================================

# Endpoint 3: Collection (List of available reports/Documentation)
@app.route('/api/analytics', methods=['GET'])
def get_analytics_list():
    """Returns a list of the 5 available analysis reports."""
    return jsonify({
        "resource": "analytics",
        "available_reports": [
            {"id": 1, "name": "Churn Rate by Demographics", "description": "Calculate churn rate grouped by Geography and Gender (Query 1)"},
            {"id": 2, "name": "Churn vs Active Profile", "description": "Compare avg age and avg products for churned vs active (Query 2)"},
            {"id": 3, "name": "Active Members Financials", "description": "Compare salary and balance for active vs non-active members (Query 3)"},
            {"id": 4, "name": "Multi-Product Analysis", "description": "Avg balance/tenure for customers with >1 product (Query 4)"},
            {"id": 5, "name": "Churn Age Range", "description": "Max and Min age of churned customers (Query 5)"}
        ]
    })

# Endpoint 4: Single Analysis (Execution of the 5 Pandas queries)
@app.route('/api/analytics/<int:report_id>', methods=['GET'])
def get_analysis_report(report_id):
    """Executes a specific analytical query based on the report_id."""
    
    if full_customer_data is None: return jsonify({"error": "No data loaded"}), 500
    
    data = []
    meta = {}
    res = pd.DataFrame() # Initialize res for type safety

    if report_id == 1:
        # Query 1: Churn Rate by Demographics (Geo & Gender)
        merged = pd.merge(customer_dim, demographic_dim, on="customerid")
        merged = pd.merge(merged, bank_report, on="customerid")
        res = merged.groupby(["geography", "gender"]).agg(
            churn_rate=("exited", "mean"), 
            total_customers=("customerid", "count")
        ).reset_index().sort_values("churn_rate", ascending=False)
        meta = {"description": "Churn rate by geography and gender"}

    elif report_id == 2:
        # Query 2: Avg age and products for churned vs active
        merged = pd.merge(customer_dim, bank_report, on="customerid")
        merged = pd.merge(merged, demographic_dim, on="customerid")
        merged = pd.merge(merged, fin_report, on="customerid")
        res = merged.groupby("exited").agg(
            avg_age=("age", "mean"), 
            avg_num_products=("numofproducts", "mean"),
            total_customers=("customerid", "count")
        ).reset_index()
        meta = {"description": "Avg age and products for churned (1) vs active (0) customers"}

    elif report_id == 3:
        # Query 3: Active Members Financials
        merged = pd.merge(customer_dim, fin_report, on="customerid")
        res = merged.groupby("isactivemember").agg(
            avg_estimated_salary=("estimatedsalary", "mean"),
            avg_balance=("balance", "mean"),
            total_customers=("customerid", "count")
        ).reset_index()
        meta = {"description": "Avg salary and balance for active (1) vs non-active (0) members"}

    elif report_id == 4:
        # Query 4: Multi-Product Analysis
        merged = pd.merge(customer_dim, fin_report, on="customerid")
        merged = pd.merge(merged, bank_report, on="customerid")
        
        # WHERE numofproducts > 1
        filtered = merged[merged["numofproducts"] > 1]
        
        res = filtered.groupby("numofproducts").agg(
            avg_balance=("balance", "mean"),
            avg_tenure=("tenure", "mean"),
            total_customers=("customerid", "count")
        ).reset_index()
        
        # ORDER BY avg_balance DESC
        res = res.sort_values(by="avg_balance", ascending=False)
        meta = {"description": "Balance and Tenure for customers with >1 product, ordered by balance"}

    elif report_id == 5:
        # Query 5: Churn Age Range
        merged = pd.merge(customer_dim, demographic_dim, on="customerid")
        merged = pd.merge(merged, bank_report, on="customerid")
        
        # WHERE exited = 1
        filtered = merged[merged["exited"] == 1]
        
        result_series = filtered.agg(
            max_age_churned=("age", "max"),
            min_age_churned=("age", "min")
        )
        # Convert result Series to DataFrame for consistent output structure
        res = pd.DataFrame([result_series]) 
        meta = {"description": "Min and Max age of churned customers"}
    
    else:
        return jsonify({"error": "Report ID must be between 1 and 5"}), 404

    # Final conversion to list of dicts for JSON output
    data = res.to_dict(orient='records')

    return jsonify({
        "report_id": report_id,
        "meta": meta,
        "results": data
    })

if __name__ == '__main__':
    # Utiliser '0.0.0.0' pour écouter toutes les interfaces réseau
    app.run(debug=True, use_reloader=False, port=5001, host='0.0.0.0')
