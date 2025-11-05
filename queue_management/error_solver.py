from pathlib import Path
import pandas as pd
import json
from typing import Optional, Tuple


class ErrorSolver:
    def __init__(self):
        self.fixed_files_dir = Path("Fixed-files")
        self.fixed_files_dir.mkdir(exist_ok=True)
    
    def attempt_fix(self, filepath: Path, error_message: str) -> Tuple[bool, Optional[Path], str]:
        if not filepath.exists():
            return False, None, "File not found - cannot fix"
        
        print(f"\nATTEMPTING TO FIX: {filepath.name}")
        print(f"Original error: {error_message}")


        error_lower = error_message.lower()
 
        if "empty" in error_lower or "no columns" in error_lower:
            return self._fix_empty_file(filepath)
        

        if filepath.suffix == '.json' and ("json" in error_lower or "parse" in error_lower or "expecting" in error_lower):
            return self._fix_json_structure(filepath)
        
  
        if "delimiter" in error_lower or "only 1 column" in error_lower:
            return self._fix_delimiter(filepath)
        
        if "invalid" in error_lower or "could not convert" in error_lower or "coerce" in error_lower:
            return self._general_csv_repair(filepath)  
        

        if filepath.suffix == '.csv':
            return self._general_csv_repair(filepath)
        
        return False, None, "No automatic fix available for this error type"
    
    def _fix_empty_file(self, filepath: Path) -> Tuple[bool, Optional[Path], str]:
       
        try:
            print("Creating dummy record for empty file...")
            
            dummy_data = {
                'User ID': [9999],
                'Product ID': [99999],
                'Product Name': ['Placeholder Product'],
                'Brand': ['Unknown'],
                'Category': ["Men's Fashion"],
                'Price': [50],
                'Rating': [4.0],
                'Color': ['Various'],
                'Size': ['Standard']
            }
            
            df = pd.DataFrame(dummy_data)
            
            fixed_path = self.fixed_files_dir / f"fixed_{filepath.name}"
            df.to_csv(fixed_path, index=False)
            
            message = "Created dummy record for empty file"
            print(f"{message}")
            print(f"Saved to: {fixed_path}")
            
            return True, fixed_path, message
            
        except Exception as e:
            return False, None, f"Failed to fix empty file: {str(e)}"
    
    def _fix_json_structure(self, filepath: Path) -> Tuple[bool, Optional[Path], str]:
        """Fix broken JSON structure"""
        try:
            print("Analyzing JSON structure...")
            
            with open(filepath, 'r') as f:
                content = f.read()
            
            fixed_content = content
            fixes_applied = []
            
            open_braces = content.count('{')
            close_braces = content.count('}')
            if open_braces > close_braces:
                fixed_content += '}' * (open_braces - close_braces)
                fixes_applied.append("Added missing closing braces")
            
            open_brackets = content.count('[')
            close_brackets = content.count(']')
            if open_brackets > close_brackets:
                fixed_content += ']' * (open_brackets - close_brackets)
                fixes_applied.append("Added missing closing brackets")
            
            try:

                data = json.loads(fixed_content)
                
                fixed_path = self.fixed_files_dir / f"fixed_{filepath.name}"
                with open(fixed_path, 'w') as f:
                    json.dump(data, f, indent=2)
                
                message = "Fixed JSON structure: " + ", ".join(fixes_applied)
                print(f"{message}")
                print(f"Saved to: {fixed_path}")
                
                return True, fixed_path, message
                
            except json.JSONDecodeError:

                print(" JSON still invalid, creating minimal structure...")
                minimal_json = {
                    "products": [
                        {
                            "User ID": 9999,
                            "Product ID": 99999,
                            "Product Name": "Recovered Data",
                            "Brand": "Unknown",
                            "Category": "Men's Fashion",
                            "Price": 50,
                            "Rating": 4.0,
                            "Color": "Various",
                            "Size": "Standard"
                        }
                    ]
                }
                
                fixed_path = self.fixed_files_dir / f"fixed_{filepath.name}"
                with open(fixed_path, 'w') as f:
                    json.dump(minimal_json, f, indent=2)
                
                message = "Created minimal valid JSON (original data lost)"
                print(f"{message}")
                print(f" Saved to: {fixed_path}")
                
                return True, fixed_path, message
            
        except Exception as e:
            return False, None, f"Failed to fix JSON: {str(e)}"
    
    def _fix_delimiter(self, filepath: Path) -> Tuple[bool, Optional[Path], str]:
        """Fix delimiter issues by trying different delimiters"""
        try:
            print(" Detecting delimiter...")
            

            with open(filepath, 'r') as f:
                first_lines = [f.readline() for _ in range(3)]
            

            delimiters = [';', '\t', '|', ',']
            best_delimiter = None
            max_columns = 0
            
            for delim in delimiters:
                try:
     
                    test_df = pd.read_csv(filepath, sep=delim, nrows=1)
                    col_count = len(test_df.columns)
                    
                    print(f"   Delimiter '{delim}' → {col_count} columns")
        
                    if col_count > max_columns and col_count >= 5:
                        max_columns = col_count
                        best_delimiter = delim
                except:
                    continue
            
            if best_delimiter and best_delimiter != ',':
                print(f" Best delimiter detected: '{best_delimiter}' ({max_columns} columns)")
                

                df = pd.read_csv(filepath, sep=best_delimiter)
                

                fixed_path = self.fixed_files_dir / f"fixed_{filepath.name}"
                df.to_csv(fixed_path, index=False)
                
                delim_names = {';': 'semicolon', '\t': 'tab', '|': 'pipe'}
                message = f"Fixed delimiter: {delim_names.get(best_delimiter, best_delimiter)} → comma ({max_columns} columns)"
                print(f" {message}")
                print(f" Saved to: {fixed_path}")
                
                return True, fixed_path, message
            
            print(" No better delimiter found, trying general repair...")
            return self._general_csv_repair(filepath)
            
        except Exception as e:
            print(f"Delimiter fix failed: {str(e)}")
            return self._general_csv_repair(filepath)
    
    def _general_csv_repair(self, filepath: Path) -> Tuple[bool, Optional[Path], str]:
  
        try:
            print("Applying general CSV repair...")
            df = None
            detected_delimiter = None
 
            for delim in [',', ';', '\t', '|']:
                try:
                    test_df = pd.read_csv(filepath, sep=delim, nrows=5)
           
                    if len(test_df.columns) > 1:
                        df = pd.read_csv(filepath, sep=delim)
                        detected_delimiter = delim
                        print(f" Detected delimiter: '{delim}' ({len(df.columns)} columns)")
                        break
                except:
                    continue
            

            if df is None:
                try:
                    df = pd.read_csv(filepath, on_bad_lines='skip')
                    print("Loaded with bad lines skipped")
                except:
                    pass
            
            if df is None or len(df) == 0:
                return False, None, "Could not read CSV file with any method"
            
            print(f"Read {len(df)} rows, {len(df.columns)} columns")
            

            required_columns = {
                'User ID': 9999,
                'Product ID': None, 
                'Product Name': 'Unknown Product',
                'Brand': 'Unknown Brand',
                'Category': "Men's Fashion",
                'Price': 50,
                'Rating': 4.0,
                'Color': 'Various',
                'Size': 'Standard'
            }
            
       
            added_cols = []
            for col, default_value in required_columns.items():
                if col not in df.columns:
                    if col == 'Product ID':
                        df[col] = range(90000, 90000 + len(df))
                    else:
                        df[col] = default_value
                    added_cols.append(col)
            
            if added_cols:
                print(f" Added missing columns: {', '.join(added_cols)}")

            if 'Price' in df.columns:
                original = df['Price'].copy()
                df['Price'] = pd.to_numeric(df['Price'], errors='coerce').fillna(50).astype(int)
                if not df['Price'].equals(original):
                    print(f" Fixed invalid Price values")
            
            if 'Rating' in df.columns:
                original = df['Rating'].copy()
                df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce').fillna(4.0).clip(1.0, 5.0)
                if not df['Rating'].equals(original):
                    print(f"Fixed invalid Rating values")
            
            if 'User ID' in df.columns:
                df['User ID'] = pd.to_numeric(df['User ID'], errors='coerce').fillna(9999).astype(int)
            
            if 'Product ID' in df.columns:
                df['Product ID'] = pd.to_numeric(df['Product ID'], errors='coerce')
                mask = df['Product ID'].isna()
                if mask.any():
                    df.loc[mask, 'Product ID'] = range(90000, 90000 + mask.sum())
                df['Product ID'] = df['Product ID'].astype(int)
       
            fixed_path = self.fixed_files_dir / f"fixed_{filepath.name}"
            df.to_csv(fixed_path, index=False)
            
            fixes = []
            if detected_delimiter and detected_delimiter != ',':
                fixes.append(f"delimiter")
            if added_cols:
                fixes.append(f"{len(added_cols)} columns")
            fixes.append("data types")
            
            message = f"Applied CSV repairs: {', '.join(fixes)}"
            print(f"{message}")
            print(f" Saved to: {fixed_path}")
            
            return True, fixed_path, message
            
        except Exception as e:
            return False, None, f"General repair failed: {str(e)}"

    
        
        


        