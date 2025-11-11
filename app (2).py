import pandas as pd
import streamlit as st

# Specify the path to your file
file_path = "Données.xlsx"

try:
    # Read all sheets from the Excel file into a dictionary of DataFrames
    excel_data = pd.read_excel(file_path, sheet_name=None)

    print("Onglets disponibles et aperçu des données :")
    # Iterate through the dictionary and display the head of each DataFrame
    for sheet_name, df in excel_data.items():
        print(f"\nOnglet : {sheet_name}")
        display(df.head())

except FileNotFoundError:
    print(f"Error: File not found at {file_path}")
except Exception as e:
    print(f"An error occurred: {e}")
