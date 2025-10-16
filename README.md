# Data Ingestion ETL Pipeline

## What It Does

### Task 1 — Continuous CSV Ingestion (`continuous-files-T4`)
- Automatically finds new CSV files in `Incoming-data/`
- Cleans and transforms them into a consistent format
- Adds new products and updates existing ones in PostgreSQL
- Moves processed files to `Archived-data/`
- Updates the report each time new data is added

**In short:** Drop a new CSV file → the pipeline picks it up → PostgreSQL stays up-to-date 


### Task 2 — JSON / Heterogeneous Sources (`json-ingestion-T5`)
- Handles data from other formats like JSON
- Converts it to the same schema as the CSV data
- Avoids duplicates when inserting into PostgreSQL
- Can use a mock JSON file for testing

**In short:** Different file format, same pipeline — all data ends up clean and consistent 

