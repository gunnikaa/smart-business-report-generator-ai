import os
import pandas as pd
import json
import logging

# Configure logging
logger = logging.getLogger(__name__)

def validate_file(filename, allowed_extensions):
    """
    Validate if the file has an allowed extension.
    
    Args:
        filename (str): The name of the file to validate
        allowed_extensions (set): Set of allowed file extensions
        
    Returns:
        bool: True if the file has an allowed extension, False otherwise
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def process_data_file(file_path, file_type):
    """
    Process the uploaded data file based on its type.
    
    Args:
        file_path (str): Path to the uploaded file
        file_type (str): Type of the file (csv, xlsx, etc.)
        
    Returns:
        list or dict: Processed data from the file
    """
    logger.debug(f"Processing file: {file_path} of type: {file_type}")
    
    try:
        if file_type == 'csv':
            # Read CSV file
            df = pd.read_csv(file_path)
            processed_data = df.to_dict(orient='records')
            
        elif file_type in ['xlsx', 'xls']:
            # Read Excel file
            df = pd.read_excel(file_path)
            processed_data = df.to_dict(orient='records')
            
        elif file_type == 'json':
            # Read JSON file
            with open(file_path, 'r') as json_file:
                processed_data = json.load(json_file)
                
            # If JSON is not in a list format, convert it to a list
            if isinstance(processed_data, dict):
                # Check if the JSON has a data field that contains a list
                if 'data' in processed_data and isinstance(processed_data['data'], list):
                    processed_data = processed_data['data']
                else:
                    # Convert to list with single dict
                    processed_data = [processed_data]
        
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        # Clean the data
        processed_data = clean_data(processed_data)
        
        # Detect financial data structure
        processed_data = detect_financial_structure(processed_data)
        
        return processed_data
    
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {str(e)}")
        raise

def clean_data(data):
    """
    Clean and normalize the data.
    
    Args:
        data (list or dict): Data to clean
        
    Returns:
        list or dict: Cleaned data
    """
    if not isinstance(data, list):
        return data
    
    cleaned_data = []
    
    for item in data:
        clean_item = {}
        
        for key, value in item.items():
            # Convert column names to snake_case and strip whitespace
            clean_key = key.strip().lower().replace(' ', '_')
            
            # Handle nan values
            if pd.isna(value):
                clean_item[clean_key] = None
            else:
                # Try to convert string numbers to float
                if isinstance(value, str) and value.replace('.', '', 1).isdigit():
                    clean_item[clean_key] = float(value)
                else:
                    clean_item[clean_key] = value
        
        cleaned_data.append(clean_item)
    
    return cleaned_data

def detect_financial_structure(data):
    """
    Detect and normalize financial data structure.
    
    Args:
        data (list): List of data records
        
    Returns:
        list: Data with normalized financial structure
    """
    if not isinstance(data, list) or not data:
        return data
    
    # Check for common financial fields
    financial_fields = {
        'revenue': ['revenue', 'sales', 'income', 'earnings', 'amt', 'amount', 'total'],
        'expenses': ['expenses', 'costs', 'expenditure', 'expense'],
        'profit': ['profit', 'net_income', 'net_profit', 'gross_profit'],
        'date': ['date', 'period', 'month', 'year', 'quarter'],
        'category': ['category', 'department', 'division', 'segment', 'product_line', 'product']
    }
    
    # Sample the first item to detect fields
    sample = data[0]
    field_mapping = {}
    
    for field_type, possible_names in financial_fields.items():
        for key in sample.keys():
            if any(name in key.lower() for name in possible_names):
                field_mapping[key] = field_type
                break
    
    # If we didn't detect enough financial fields, return the original data
    if len(field_mapping) < 2:
        return data
    
    # Normalize the data with the detected mapping
    normalized_data = []
    
    for item in data:
        normalized_item = {}
        
        for orig_key, normalized_key in field_mapping.items():
            if orig_key in item:
                normalized_item[normalized_key] = item[orig_key]
        
        # Copy any fields that weren't mapped
        for key, value in item.items():
            if key not in field_mapping:
                normalized_item[key] = value
        
        normalized_data.append(normalized_item)
    
    return normalized_data
