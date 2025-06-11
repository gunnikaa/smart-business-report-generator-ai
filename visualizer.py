import logging
import pandas as pd
from collections import defaultdict

# Configure logging
logger = logging.getLogger(__name__)

def create_visualizations(data):
    """
    Create visualization data from the processed financial data.
    
    Args:
        data (list): Processed financial data
        
    Returns:
        list: List of visualization data objects
    """
    visualizations = []
    
    if not isinstance(data, list) or not data:
        logger.warning("Invalid data for visualization")
        return visualizations
    
    try:
        # Convert data to DataFrame for easier analysis
        df = pd.DataFrame(data)
        
        # Add time series visualizations
        time_series = create_time_series_chart(df)
        if time_series:
            visualizations.append(time_series)
        
        # Add category comparison visualizations
        category_chart = create_category_comparison_chart(df)
        if category_chart:
            visualizations.append(category_chart)
        
        # Add distribution chart
        distribution_chart = create_distribution_chart(df)
        if distribution_chart:
            visualizations.append(distribution_chart)
        
        # Add pie chart for composition
        composition_chart = create_composition_chart(df)
        if composition_chart:
            visualizations.append(composition_chart)
        
        # If we have few visualizations, create more
        if len(visualizations) < 2:
            # Try to create correlation chart
            correlation_chart = create_correlation_chart(df)
            if correlation_chart:
                visualizations.append(correlation_chart)
    
    except Exception as e:
        logger.error(f"Error creating visualizations: {str(e)}")
    
    return visualizations

def create_time_series_chart(df):
    """
    Create a time series chart if time-based data is available.
    
    Args:
        df (DataFrame): Data as pandas DataFrame
        
    Returns:
        dict: Visualization data or None if not applicable
    """
    try:
        # Look for date/time columns
        date_columns = [col for col in df.columns if any(term in col.lower() for term in 
                                                     ['date', 'month', 'year', 'quarter', 'period'])]
        
        if not date_columns:
            return None
        
        date_col = date_columns[0]
        
        # Look for numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if not numeric_cols:
            return None
        
        # Select numeric columns (up to 3) to show in the chart
        selected_numeric_cols = numeric_cols[:3]
        
        # Group by date and aggregate
        try:
            # Try to convert to datetime
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            # Sort by date
            df = df.sort_values(by=date_col)
        except:
            # If conversion fails, use the column as is
            pass
        
        # Group by date column and compute mean for numeric columns
        grouped = df.groupby(date_col)[selected_numeric_cols].mean().reset_index()
        
        # Convert date labels to strings for the chart
        date_labels = [str(date) for date in grouped[date_col].tolist()]
        
        # Create datasets for each numeric column
        datasets = []
        for col in selected_numeric_cols:
            datasets.append({
                'label': col,
                'data': grouped[col].tolist()
            })
        
        # Create chart data
        chart_data = {
            'type': 'line',
            'title': 'Time Series Analysis',
            'labels': date_labels,
            'datasets': datasets,
            'description': f'This chart shows the trend of {", ".join(selected_numeric_cols)} over time.'
        }
        
        return chart_data
    
    except Exception as e:
        logger.error(f"Error creating time series chart: {str(e)}")
        return None

def create_category_comparison_chart(df):
    """
    Create a category comparison chart if categorical data is available.
    
    Args:
        df (DataFrame): Data as pandas DataFrame
        
    Returns:
        dict: Visualization data or None if not applicable
    """
    try:
        # Look for category columns
        category_columns = [col for col in df.columns if any(term in col.lower() for term in 
                                                          ['category', 'type', 'segment', 'department', 'division', 'product'])]
        
        if not category_columns:
            return None
        
        category_col = category_columns[0]
        
        # Look for numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if not numeric_cols:
            return None
        
        # Select a numeric column to aggregate
        numeric_col = numeric_cols[0]
        
        # Group by category and aggregate
        grouped = df.groupby(category_col)[numeric_col].sum().reset_index()
        
        # Sort by the numeric value
        grouped = grouped.sort_values(by=numeric_col, ascending=False)
        
        # Limit to top 10 categories
        if len(grouped) > 10:
            grouped = grouped.head(10)
        
        # Create chart data
        chart_data = {
            'type': 'bar',
            'title': f'{numeric_col} by {category_col}',
            'labels': grouped[category_col].tolist(),
            'datasets': [{
                'label': numeric_col,
                'data': grouped[numeric_col].tolist()
            }],
            'description': f'This chart compares {numeric_col} across different {category_col} categories.'
        }
        
        return chart_data
    
    except Exception as e:
        logger.error(f"Error creating category comparison chart: {str(e)}")
        return None

def create_distribution_chart(df):
    """
    Create a distribution chart for numeric data.
    
    Args:
        df (DataFrame): Data as pandas DataFrame
        
    Returns:
        dict: Visualization data or None if not applicable
    """
    try:
        # Look for numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if not numeric_cols or len(numeric_cols) < 2:
            return None
        
        # Select two numeric columns for comparison
        numeric_col1 = numeric_cols[0]
        numeric_col2 = numeric_cols[1]
        
        # Create bins for the first numeric column
        # Determine number of bins based on data size
        n_bins = min(10, len(df) // 5) if len(df) > 10 else 5
        
        # Create histogram data - handle various return formats
        try:
            result = pd.cut(df[numeric_col1], bins=n_bins, retbins=True, include_lowest=True)
            if isinstance(result, tuple) and len(result) >= 2:
                hist_data1, bin_edges = result
            else:
                # If pd.cut doesn't return the expected format, use numpy instead
                import numpy as np
                bin_edges = np.linspace(df[numeric_col1].min(), df[numeric_col1].max(), n_bins + 1)
                hist_data1 = pd.cut(df[numeric_col1], bins=bin_edges, include_lowest=True)
                
            hist_counts1 = hist_data1.value_counts().sort_index()
            
            # Create histogram data for second column using same bins
            hist_data2 = pd.cut(df[numeric_col2], bins=bin_edges, include_lowest=True)
            hist_counts2 = hist_data2.value_counts().sort_index()
        except Exception as e:
            logger.warning(f"Error in histogram creation: {str(e)}. Using alternative method.")
            
            # Alternative approach using numpy histogram
            import numpy as np
            hist1, bin_edges = np.histogram(df[numeric_col1].dropna(), bins=n_bins)
            hist2, _ = np.histogram(df[numeric_col2].dropna(), bins=bin_edges)
            
            # Convert to Series for consistent interface
            hist_counts1 = pd.Series(hist1)
            hist_counts2 = pd.Series(hist2)
        
        # Create bin labels
        bin_labels = [f"{bin_edges[i]:.1f}-{bin_edges[i+1]:.1f}" for i in range(len(bin_edges)-1)]
        
        # Create chart data
        chart_data = {
            'type': 'bar',
            'title': f'Distribution Comparison',
            'labels': bin_labels,
            'datasets': [
                {
                    'label': numeric_col1,
                    'data': hist_counts1.tolist()
                },
                {
                    'label': numeric_col2,
                    'data': hist_counts2.tolist()
                }
            ],
            'description': f'This chart shows the distribution of {numeric_col1} and {numeric_col2}.'
        }
        
        return chart_data
    
    except Exception as e:
        logger.error(f"Error creating distribution chart: {str(e)}")
        return None

def create_composition_chart(df):
    """
    Create a pie chart showing composition of a category.
    
    Args:
        df (DataFrame): Data as pandas DataFrame
        
    Returns:
        dict: Visualization data or None if not applicable
    """
    try:
        # Look for category columns
        category_columns = [col for col in df.columns if any(term in col.lower() for term in 
                                                          ['category', 'type', 'segment', 'department', 'division', 'product'])]
        
        if not category_columns:
            return None
        
        category_col = category_columns[0]
        
        # Look for numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if not numeric_cols:
            return None
        
        # Select a numeric column to aggregate
        numeric_col = numeric_cols[0]
        
        # Group by category and aggregate
        grouped = df.groupby(category_col)[numeric_col].sum().reset_index()
        
        # Sort by the numeric value
        grouped = grouped.sort_values(by=numeric_col, ascending=False)
        
        # Limit to top 8 categories for pie chart clarity
        if len(grouped) > 8:
            # Keep top 7 and group the rest as "Other"
            top_grouped = grouped.head(7)
            other_value = grouped.iloc[7:][numeric_col].sum()
            
            # Add "Other" category
            other_row = pd.DataFrame({category_col: ['Other'], numeric_col: [other_value]})
            grouped = pd.concat([top_grouped, other_row])
        
        # Create chart data
        chart_data = {
            'type': 'pie',
            'title': f'Composition of {numeric_col} by {category_col}',
            'labels': grouped[category_col].tolist(),
            'datasets': [{
                'label': numeric_col,
                'data': grouped[numeric_col].tolist()
            }],
            'description': f'This chart shows the proportion of {numeric_col} by different {category_col} categories.'
        }
        
        return chart_data
    
    except Exception as e:
        logger.error(f"Error creating composition chart: {str(e)}")
        return None

def create_correlation_chart(df):
    """
    Create a scatter plot showing correlation between two numeric variables.
    
    Args:
        df (DataFrame): Data as pandas DataFrame
        
    Returns:
        dict: Visualization data or None if not applicable
    """
    try:
        # Look for numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if len(numeric_cols) < 2:
            return None
        
        # Select two numeric columns
        x_col = numeric_cols[0]
        y_col = numeric_cols[1]
        
        # Create chart data
        chart_data = {
            'type': 'scatter',
            'title': f'Correlation: {x_col} vs {y_col}',
            'labels': [x_col, y_col],
            'datasets': [{
                'label': 'Data Points',
                'data': [df[x_col].tolist(), df[y_col].tolist()]
            }],
            'description': f'This scatter plot shows the relationship between {x_col} and {y_col}.'
        }
        
        return chart_data
    
    except Exception as e:
        logger.error(f"Error creating correlation chart: {str(e)}")
        return None
