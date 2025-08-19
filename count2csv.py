# about:
# 1) gets count of budgets, budget alert rules, budget queries/schedules, and quotas
# 2) prints to console
# 3) outputs to simple csv 
# usage:
# python3 count2csv.py --t ocid1.tenancy.oc1..abcd1234
# python3 count2csv.py --c ocid1.compartment.oc1..abcd1234
# known issues:
# most stable if run in home region, with root/tenancy as target. need to make it cleanly handle

import argparse
import os
import subprocess
import json
import csv
import sys

def run_oci_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError:
        return None

def count_budgets(compartment_id):
    data = run_oci_command(f"oci budgets budget list --compartment-id {compartment_id}")
    budgets = data.get("data", []) if data else []
    return len(budgets), budgets

def count_budget_alerts(budgets):
    total_alerts = 0
    for b in budgets:
        budget_id = b.get("id")
        if not budget_id:
            continue
        data = run_oci_command(f"oci budgets budget alert-rule list --budget-id {budget_id}")
        alerts = data.get("data", []) if data else []
        total_alerts += len(alerts)
    return total_alerts

def count_usage_configurations(tenancy_id):
    data = run_oci_command(f"oci usage-api configuration request-summarized --tenant-id {tenancy_id}")
    configs = data.get("data", []) if data else []
    if isinstance(configs, dict):
        configs = [configs]
    return len(configs)

def count_usage_queries(compartment_id):
    data = run_oci_command(f"oci usage-api query list --compartment-id {compartment_id}")
    queries = data.get("data", []) if data else []
    return len(queries)

def count_usage_schedules(compartment_id):
    data = run_oci_command(f"oci usage-api schedule list --compartment-id {compartment_id}")
    schedules = data.get("data", []) if data else []
    return len(schedules)

def count_quotas(compartment_id):
    data = run_oci_command(f"oci limits quota list --compartment-id {compartment_id}")
    quotas = data.get("data", []) if data else []
    return len(quotas)

def print_table(counts):
    # Find column widths
    resource_col_width = max(len("Resource"), max(len(k) for k in counts)) + 2
    count_col_width = max(len("Count"), max(len(str(v)) for v in counts.values())) + 2
    # Header
    print(f"{'Resource'.ljust(resource_col_width)}{'Count'.ljust(count_col_width)}")
    print('-' * (resource_col_width + count_col_width))
    # Rows
    for k, v in counts.items():
        print(f"{k.ljust(resource_col_width)}{str(v).ljust(count_col_width)}")
    print('-' * (resource_col_width + count_col_width))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--c", "--compartment-id", dest="compartment_id", help="Compartment OCID", required=False)
    parser.add_argument("--t", "--tenancy-id", dest="tenancy_id", help="Tenancy OCID", required=False)
    parser.add_argument("--outfile", default="resource_counts.csv", help="CSV filename")
    args = parser.parse_args()

    compartment_id = (
        args.compartment_id
        or os.environ.get("COMPARTMENT_ID")
        or args.tenancy_id
        or os.environ.get("TENANCY_ID")
    )
    tenancy_id = (
        args.tenancy_id
        or os.environ.get("TENANCY_ID")
        or args.compartment_id
        or os.environ.get("COMPARTMENT_ID")
    )

    if not compartment_id:
        print("Error: You must provide either a tenancy-id or a compartment-id (via --t or --c, or environment variables).", file=sys.stderr)
        sys.exit(1)

    counts = {}
    # Budgets and Budget Alerts
    budget_count, budgets = count_budgets(compartment_id)
    counts["budgets"] = budget_count
    counts["budget_alert_rules"] = count_budget_alerts(budgets) if budget_count > 0 else 0

    # Usage configurations (normally just 1 per tenancy)
    counts["usage_configurations"] = count_usage_configurations(tenancy_id)
    counts["usage_queries"] = count_usage_queries(compartment_id)
    counts["usage_schedules"] = count_usage_schedules(compartment_id)
    counts["quotas"] = count_quotas(compartment_id)

    # Write CSV
    with open(args.outfile, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Resource", "Count"])
        for key, value in counts.items():
            writer.writerow([key, value])

    print("\nResource Counts:\n")
    print_table(counts)
    print(f"Wrote counts to {args.outfile}\n")

if __name__ == "__main__":
    main()
