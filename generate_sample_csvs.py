#!/usr/bin/env python3
"""
Generate sample CSV files for testing the bulk upload feature in Practus AI.
This script creates 5 sample CSV files with appropriate naming for auto-detection.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

# Create sample data directory
os.makedirs('sample_data', exist_ok=True)

# 1. Deals Archive CSV
deals_data = {
    'Deal_ID': range(1, 101),
    'Deal_Name': [f'Deal_{i}' for i in range(1, 101)],
    'Deal_Amount': np.random.randint(10000, 500000, 100),
    'Stage': np.random.choice(['Prospecting', 'Qualification', 'Proposal', 'Negotiation', 'Closed Won', 'Closed Lost'], 100),
    'Close_Date': [(datetime.now() + timedelta(days=random.randint(-365, 365))).strftime('%Y-%m-%d') for _ in range(100)],
    'Sales_Rep': [f'Rep_{i%10}' for i in range(100)],
    'Region': np.random.choice(['North', 'South', 'East', 'West'], 100)
}
pd.DataFrame(deals_data).to_csv('sample_data/deals_archive.csv', index=False)
print("✓ Created: deals_archive.csv")

# 2. Stage History CSV
stage_history_data = {
    'Deal_ID': np.random.randint(1, 101, 500),
    'Stage': np.random.choice(['Prospecting', 'Qualification', 'Proposal', 'Negotiation', 'Closed Won', 'Closed Lost'], 500),
    'Stage_Date': [(datetime.now() - timedelta(days=random.randint(0, 365))).strftime('%Y-%m-%d') for _ in range(500)],
    'Days_in_Stage': np.random.randint(1, 60, 500),
    'Previous_Stage': np.random.choice(['Prospecting', 'Qualification', 'Proposal', 'Negotiation', None], 500),
    'Stage_Notes': [f'Note_{i}' for i in range(500)]
}
pd.DataFrame(stage_history_data).to_csv('sample_data/stage_history_data.csv', index=False)
print("✓ Created: stage_history_data.csv")

# 3. Whizible Data CSV
whizible_data = {
    'Employee_ID': [f'EMP{i:03d}' for i in range(1, 151)],
    'Employee_Name': [f'Employee_{i}' for i in range(1, 151)],
    'Project': np.random.choice(['Project_A', 'Project_B', 'Project_C', 'Project_D', 'Project_E'], 150),
    'Hours_Logged': np.random.uniform(4, 12, 150).round(2),
    'Date': [(datetime.now() - timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d') for _ in range(150)],
    'Task_Type': np.random.choice(['Development', 'Testing', 'Documentation', 'Meetings', 'Research'], 150),
    'Billable': np.random.choice(['Yes', 'No'], 150)
}
pd.DataFrame(whizible_data).to_csv('sample_data/whizible_timesheet.csv', index=False)
print("✓ Created: whizible_timesheet.csv")

# 4. Plotting Tool Data CSV
plotting_data = {
    'Metric_ID': range(1, 201),
    'Metric_Name': [f'Metric_{i}' for i in range(1, 201)],
    'Value': np.random.uniform(50, 150, 200).round(2),
    'Category': np.random.choice(['Revenue', 'Cost', 'Efficiency', 'Quality', 'Customer'], 200),
    'Date': [(datetime.now() - timedelta(days=random.randint(0, 90))).strftime('%Y-%m-%d') for _ in range(200)],
    'Department': np.random.choice(['Sales', 'Marketing', 'Operations', 'IT', 'HR'], 200),
    'Target_Value': np.random.uniform(60, 140, 200).round(2)
}
pd.DataFrame(plotting_data).to_csv('sample_data/plotting_metrics.csv', index=False)
print("✓ Created: plotting_metrics.csv")

# 5. Skill Mapping CSV
skills_data = {
    'Employee_ID': [f'EMP{i:03d}' for i in range(1, 101)],
    'Employee_Name': [f'Employee_{i}' for i in range(1, 101)],
    'Primary_Skill': np.random.choice(['Python', 'Java', 'JavaScript', 'SQL', 'React', 'AWS', 'Docker'], 100),
    'Skill_Level': np.random.choice(['Beginner', 'Intermediate', 'Advanced', 'Expert'], 100),
    'Years_Experience': np.random.randint(1, 15, 100),
    'Certifications': np.random.randint(0, 5, 100),
    'Department': np.random.choice(['Engineering', 'Data Science', 'DevOps', 'QA', 'Product'], 100),
    'Last_Training_Date': [(datetime.now() - timedelta(days=random.randint(30, 365))).strftime('%Y-%m-%d') for _ in range(100)]
}
pd.DataFrame(skills_data).to_csv('sample_data/skill_mapping_report.csv', index=False)
print("✓ Created: skill_mapping_report.csv")

print(f"\n✅ All 5 sample CSV files created in the 'sample_data' directory!")
print("\nFile names are optimized for auto-detection:")
print("  • deals_archive.csv → Deals Archive")
print("  • stage_history_data.csv → Stage History Archive") 
print("  • whizible_timesheet.csv → Whizible Data")
print("  • plotting_metrics.csv → Plotting Tool Data")
print("  • skill_mapping_report.csv → Skill Mapping")
print("\n📁 You can now select all 5 files at once using the 'Select All Files' button in the Data Source page!")

