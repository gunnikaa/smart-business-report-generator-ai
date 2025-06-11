import re
import logging
import statistics
from collections import Counter

# Configure logging
logger = logging.getLogger(__name__)

def analyze_data(data):
    """
    Perform basic NLP analysis on financial data to extract insights.
    
    Args:
        data (list or dict): The processed financial data
        
    Returns:
        list: A list of insight statements derived from the data
    """
    try:
        insights = []
        
        if not data or not isinstance(data, list):
            return ["Insufficient data for analysis."]
        
        # Check for numeric fields to analyze
        numeric_fields = identify_numeric_fields(data)
        date_fields = identify_date_fields(data)
        category_fields = identify_category_fields(data)
        
        # Generate basic statistical insights
        statistical_insights = generate_statistical_insights(data, numeric_fields)
        insights.extend(statistical_insights)
        
        # Generate trend insights if date fields are present
        if date_fields:
            trend_insights = generate_trend_insights(data, date_fields, numeric_fields)
            insights.extend(trend_insights)
        
        # Generate category comparison insights if category fields are present
        if category_fields:
            category_insights = generate_category_insights(data, category_fields, numeric_fields)
            insights.extend(category_insights)
        
        # If we have both date and category fields, generate more complex insights
        if date_fields and category_fields:
            complex_insights = generate_complex_insights(data, date_fields, category_fields, numeric_fields)
            insights.extend(complex_insights)
        
        # Deduplicate insights
        unique_insights = list(set(insights))
        
        # If we have very few insights, generate some general recommendations
        if len(unique_insights) < 3:
            recommendations = generate_recommendations(data)
            unique_insights.extend(recommendations)
        
        return unique_insights
    
    except Exception as e:
        logger.error(f"Error analyzing data: {str(e)}")
        return ["Error analyzing data. Please check the input format."]

def identify_numeric_fields(data):
    """
    Identify fields with numeric values.
    
    Args:
        data (list): List of data records
        
    Returns:
        list: List of numeric field names
    """
    if not data:
        return []
    
    # Use the first record to identify candidate fields
    sample = data[0]
    candidates = []
    
    for key, value in sample.items():
        if isinstance(value, (int, float)) or (isinstance(value, str) and value.replace('.', '', 1).isdigit()):
            candidates.append(key)
    
    # Verify candidates across the dataset
    numeric_fields = []
    for field in candidates:
        numeric_count = sum(1 for item in data if field in item and 
                            (isinstance(item[field], (int, float)) or 
                             (isinstance(item[field], str) and item[field].replace('.', '', 1).isdigit())))
        
        # If at least 80% of values are numeric, consider it a numeric field
        if numeric_count / len(data) >= 0.8:
            numeric_fields.append(field)
    
    return numeric_fields

def identify_date_fields(data):
    """
    Identify fields that might contain date information.
    
    Args:
        data (list): List of data records
        
    Returns:
        list: List of date field names
    """
    if not data:
        return []
    
    date_indicators = ['date', 'period', 'month', 'year', 'quarter', 'day', 'week']
    date_fields = []
    
    # Use the first record to check field names
    sample = data[0]
    
    for key in sample.keys():
        key_lower = key.lower()
        if any(indicator in key_lower for indicator in date_indicators):
            date_fields.append(key)
    
    return date_fields

def identify_category_fields(data):
    """
    Identify fields that might represent categories.
    
    Args:
        data (list): List of data records
        
    Returns:
        list: List of category field names
    """
    if not data:
        return []
    
    category_indicators = ['category', 'type', 'department', 'division', 'segment', 'product', 'region', 'country']
    category_fields = []
    
    # Use the first record to check field names
    sample = data[0]
    
    for key in sample.keys():
        key_lower = key.lower()
        if any(indicator in key_lower for indicator in category_indicators):
            category_fields.append(key)
    
    return category_fields

def generate_statistical_insights(data, numeric_fields):
    """
    Generate insights based on basic statistics.
    
    Args:
        data (list): List of data records
        numeric_fields (list): List of numeric field names
        
    Returns:
        list: Statistical insights
    """
    insights = []
    
    for field in numeric_fields:
        values = [float(item[field]) for item in data if field in item and item[field] is not None]
        
        if not values:
            continue
        
        # Calculate basic statistics
        try:
            total = sum(values)
            average = total / len(values)
            maximum = max(values)
            minimum = min(values)
            
            # Only add insights if we have enough data points
            if len(values) >= 3:
                insights.append(f"The total {field.replace('_', ' ')} is {total:.2f}.")
                insights.append(f"The average {field.replace('_', ' ')} is {average:.2f}.")
                insights.append(f"The maximum {field.replace('_', ' ')} recorded is {maximum:.2f}.")
                insights.append(f"The minimum {field.replace('_', ' ')} recorded is {minimum:.2f}.")
                
                # If field likely represents revenue, profit, or similar
                if any(term in field.lower() for term in ['revenue', 'profit', 'sales', 'income']):
                    percent_diff = ((maximum - minimum) / minimum) * 100 if minimum > 0 else 0
                    insights.append(f"There is a {percent_diff:.1f}% difference between the highest and lowest {field.replace('_', ' ')}.")
                
                # Calculate standard deviation for variability
                if len(values) >= 5:
                    std_dev = statistics.stdev(values)
                    variability = (std_dev / average) * 100 if average > 0 else 0
                    
                    if variability > 30:
                        insights.append(f"There is high variability in {field.replace('_', ' ')} (coefficient of variation: {variability:.1f}%).")
                    elif variability < 10:
                        insights.append(f"There is low variability in {field.replace('_', ' ')} (coefficient of variation: {variability:.1f}%).")
        
        except Exception as e:
            logger.error(f"Error calculating statistics for {field}: {str(e)}")
    
    return insights

def generate_trend_insights(data, date_fields, numeric_fields):
    """
    Generate insights related to trends over time.
    
    Args:
        data (list): List of data records
        date_fields (list): List of date field names
        numeric_fields (list): List of numeric field names
        
    Returns:
        list: Trend insights
    """
    insights = []
    
    if not date_fields or not numeric_fields:
        return insights
    
    # Use the first date field for analysis
    date_field = date_fields[0]
    
    for numeric_field in numeric_fields:
        # Sort data by date field if possible
        try:
            # Extract data points with both date and numeric values
            data_points = [(item[date_field], float(item[numeric_field])) 
                         for item in data 
                         if date_field in item and numeric_field in item and item[date_field] and item[numeric_field] is not None]
            
            if len(data_points) < 3:
                continue
            
            # Sort by date
            data_points.sort(key=lambda x: x[0])
            
            # Get first and last values to detect overall trend
            first_value = data_points[0][1]
            last_value = data_points[-1][1]
            
            # Calculate percent change
            percent_change = ((last_value - first_value) / first_value) * 100 if first_value > 0 else 0
            
            # Generate trend insight
            if percent_change > 10:
                insights.append(f"The {numeric_field.replace('_', ' ')} shows an increasing trend of {percent_change:.1f}% over the analyzed period.")
            elif percent_change < -10:
                insights.append(f"The {numeric_field.replace('_', ' ')} shows a decreasing trend of {abs(percent_change):.1f}% over the analyzed period.")
            else:
                insights.append(f"The {numeric_field.replace('_', ' ')} remains relatively stable over the analyzed period (change: {percent_change:.1f}%).")
            
            # Detect quarter-to-quarter or month-to-month changes
            if len(data_points) >= 6:
                segments = min(4, len(data_points) // 2)  # Divide into segments (max 4)
                segment_size = len(data_points) // segments
                
                segment_averages = []
                for i in range(segments):
                    start_idx = i * segment_size
                    end_idx = start_idx + segment_size if i < segments - 1 else len(data_points)
                    segment_values = [point[1] for point in data_points[start_idx:end_idx]]
                    segment_averages.append(sum(segment_values) / len(segment_values))
                
                # Compare first and last segment
                segment_change = ((segment_averages[-1] - segment_averages[0]) / segment_averages[0]) * 100 if segment_averages[0] > 0 else 0
                
                if segment_change > 15:
                    insights.append(f"The {numeric_field.replace('_', ' ')} shows a strong positive trend in the most recent period (change: {segment_change:.1f}%).")
                elif segment_change < -15:
                    insights.append(f"The {numeric_field.replace('_', ' ')} shows a concerning downward trend in the most recent period (change: {abs(segment_change):.1f}%).")
        
        except Exception as e:
            logger.error(f"Error analyzing trends for {numeric_field}: {str(e)}")
    
    return insights

def generate_category_insights(data, category_fields, numeric_fields):
    """
    Generate insights comparing different categories.
    
    Args:
        data (list): List of data records
        category_fields (list): List of category field names
        numeric_fields (list): List of numeric field names
        
    Returns:
        list: Category comparison insights
    """
    insights = []
    
    if not category_fields or not numeric_fields:
        return insights
    
    # Use the first category field for analysis
    category_field = category_fields[0]
    
    for numeric_field in numeric_fields:
        try:
            # Group data by category
            category_data = {}
            
            for item in data:
                if category_field in item and numeric_field in item and item[category_field] is not None and item[numeric_field] is not None:
                    category = str(item[category_field])
                    value = float(item[numeric_field])
                    
                    if category not in category_data:
                        category_data[category] = []
                    
                    category_data[category].append(value)
            
            # Need at least 2 categories with data
            if len(category_data) < 2:
                continue
            
            # Calculate average for each category
            category_averages = {}
            for category, values in category_data.items():
                if values:
                    category_averages[category] = sum(values) / len(values)
            
            # Find best and worst performing categories
            sorted_categories = sorted(category_averages.items(), key=lambda x: x[1], reverse=True)
            
            # Generate insights for top and bottom performers
            if len(sorted_categories) >= 2:
                top_category, top_avg = sorted_categories[0]
                bottom_category, bottom_avg = sorted_categories[-1]
                
                insights.append(f"The best performing category in terms of {numeric_field.replace('_', ' ')} is '{top_category}' with an average of {top_avg:.2f}.")
                insights.append(f"The lowest performing category in terms of {numeric_field.replace('_', ' ')} is '{bottom_category}' with an average of {bottom_avg:.2f}.")
                
                # Calculate the performance gap
                performance_gap = ((top_avg - bottom_avg) / bottom_avg) * 100 if bottom_avg > 0 else 0
                
                if performance_gap > 50:
                    insights.append(f"There is a significant performance gap of {performance_gap:.1f}% between the top and bottom categories for {numeric_field.replace('_', ' ')}.")
            
            # If we have more than 3 categories, provide more detailed analysis
            if len(sorted_categories) >= 3:
                # Calculate the total contribution
                total = sum(avg for _, avg in sorted_categories)
                
                # Check for dominant categories (contributing more than 40%)
                for category, avg in sorted_categories:
                    contribution = (avg / total) * 100 if total > 0 else 0
                    if contribution > 40:
                        insights.append(f"The '{category}' category dominates with {contribution:.1f}% of the total {numeric_field.replace('_', ' ')}.")
                        break
                
                # Check for concentration (top 2 categories > 70%)
                if len(sorted_categories) >= 4:
                    top_two_contribution = ((sorted_categories[0][1] + sorted_categories[1][1]) / total) * 100 if total > 0 else 0
                    if top_two_contribution > 70:
                        insights.append(f"Top two categories represent {top_two_contribution:.1f}% of the total {numeric_field.replace('_', ' ')}, indicating high concentration.")
        
        except Exception as e:
            logger.error(f"Error analyzing categories for {numeric_field}: {str(e)}")
    
    return insights

def generate_complex_insights(data, date_fields, category_fields, numeric_fields):
    """
    Generate more complex insights combining time and category analysis.
    
    Args:
        data (list): List of data records
        date_fields (list): List of date field names
        category_fields (list): List of category field names
        numeric_fields (list): List of numeric field names
        
    Returns:
        list: Complex insights
    """
    insights = []
    
    if not date_fields or not category_fields or not numeric_fields:
        return insights
    
    # Use the first date and category fields
    date_field = date_fields[0]
    category_field = category_fields[0]
    
    for numeric_field in numeric_fields:
        try:
            # Organize data by category and then by date
            organized_data = {}
            
            for item in data:
                if all(field in item for field in [date_field, category_field, numeric_field]) and \
                   all(item[field] is not None for field in [date_field, category_field, numeric_field]):
                    
                    category = str(item[category_field])
                    date = item[date_field]
                    value = float(item[numeric_field])
                    
                    if category not in organized_data:
                        organized_data[category] = {}
                    
                    if date not in organized_data[category]:
                        organized_data[category][date] = []
                    
                    organized_data[category][date].append(value)
            
            # Need at least 2 categories with data over time
            if len(organized_data) < 2:
                continue
            
            # Calculate growth rates for each category
            growth_rates = {}
            
            for category, date_data in organized_data.items():
                if len(date_data) < 2:
                    continue
                
                # Get earliest and latest dates
                sorted_dates = sorted(date_data.keys())
                earliest_date = sorted_dates[0]
                latest_date = sorted_dates[-1]
                
                # Calculate average values for earliest and latest periods
                earliest_avg = sum(date_data[earliest_date]) / len(date_data[earliest_date])
                latest_avg = sum(date_data[latest_date]) / len(date_data[latest_date])
                
                # Calculate growth rate
                growth_rate = ((latest_avg - earliest_avg) / earliest_avg) * 100 if earliest_avg > 0 else 0
                growth_rates[category] = growth_rate
            
            # Need at least 2 categories with growth rates
            if len(growth_rates) < 2:
                continue
            
            # Find categories with highest and lowest growth
            sorted_growth = sorted(growth_rates.items(), key=lambda x: x[1], reverse=True)
            fastest_growing = sorted_growth[0]
            slowest_growing = sorted_growth[-1]
            
            # Generate insights about growth comparison
            insights.append(f"The fastest growing category for {numeric_field.replace('_', ' ')} is '{fastest_growing[0]}' with a growth rate of {fastest_growing[1]:.1f}%.")
            
            if slowest_growing[1] < 0:
                insights.append(f"The category '{slowest_growing[0]}' is showing a decline of {abs(slowest_growing[1]):.1f}% in {numeric_field.replace('_', ' ')}.")
            else:
                insights.append(f"The slowest growing category for {numeric_field.replace('_', ' ')} is '{slowest_growing[0]}' with a growth rate of {slowest_growing[1]:.1f}%.")
            
            # Check for categories with contrasting performance
            growth_diff = fastest_growing[1] - slowest_growing[1]
            if growth_diff > 50:
                insights.append(f"There is a significant growth gap of {growth_diff:.1f}% between the best and worst performing categories for {numeric_field.replace('_', ' ')}.")
        
        except Exception as e:
            logger.error(f"Error generating complex insights for {numeric_field}: {str(e)}")
    
    return insights

def generate_recommendations(data):
    """
    Generate general business recommendations based on the data.
    
    Args:
        data (list): List of data records
        
    Returns:
        list: Business recommendations
    """
    return [
        "Consider conducting a detailed analysis of your best performing segments to identify success factors that can be applied elsewhere.",
        "Regular financial monitoring and reporting can help identify trends earlier and improve decision-making.",
        "Diversify revenue streams to reduce dependency on any single source and increase business resilience.",
        "Implement forecasting models to better predict future performance and prepare accordingly.",
        "Review cost structures periodically to identify opportunities for optimization and improved margins."
    ]
