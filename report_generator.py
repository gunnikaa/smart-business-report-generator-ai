import os
import logging
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# Configure logging
logger = logging.getLogger(__name__)

def generate_pdf_report(report, insights, visualizations, data, output_path):
    """
    Generate a PDF report with insights and visualizations.
    
    Args:
        report (Report): Report object from database
        insights (list): List of insight statements
        visualizations (list): List of visualization data
        data (list): Processed financial data
        output_path (str): Path to save the PDF report
    
    Returns:
        bool: True if report generation was successful, False otherwise
    """
    try:
        # Create a PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Get styles
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='Heading1',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=12
        ))
        styles.add(ParagraphStyle(
            name='Heading2',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=8,
            spaceBefore=8
        ))
        styles.add(ParagraphStyle(
            name='Normal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6
        ))
        
        # Create document content
        content = []
        
        # Add title
        content.append(Paragraph(report.title, styles['Heading1']))
        content.append(Spacer(1, 0.25 * inch))
        
        # Add report details
        content.append(Paragraph(f"Report Type: {report.report_type.capitalize()}", styles['Normal']))
        content.append(Paragraph(f"Generated on: {report.generation_date.strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
        content.append(Spacer(1, 0.25 * inch))
        
        # Add executive summary
        content.append(Paragraph("Executive Summary", styles['Heading2']))
        content.append(Paragraph("This report provides an analysis of the financial data, highlighting key trends, patterns, and insights derived from the data.", styles['Normal']))
        content.append(Spacer(1, 0.25 * inch))
        
        # Add key insights
        content.append(Paragraph("Key Insights", styles['Heading2']))
        for insight in insights[:8]:  # Limit to top 8 insights
            content.append(Paragraph(f"• {insight}", styles['Normal']))
        content.append(Spacer(1, 0.25 * inch))
        
        # Add data visualizations
        content.append(Paragraph("Data Visualizations", styles['Heading2']))
        
        # Generate visualization images
        for viz_data in visualizations[:4]:  # Limit to top 4 visualizations
            # Generate image from visualization data
            img_data = generate_chart_image(viz_data)
            if img_data:
                img = Image(img_data, width=6*inch, height=3*inch)
                content.append(img)
                content.append(Paragraph(viz_data.get('title', 'Chart'), styles['Normal']))
                if 'description' in viz_data and viz_data['description']:
                    content.append(Paragraph(viz_data['description'], styles['Normal']))
                content.append(Spacer(1, 0.25 * inch))
        
        # Add data summary
        content.append(Paragraph("Data Summary", styles['Heading2']))
        
        # Create a summary table of the data (first 10 rows max)
        if isinstance(data, list) and data:
            # Convert to DataFrame for easier handling
            df = pd.DataFrame(data[:10])
            
            # Limit columns to first 6 to avoid wide tables
            columns = list(df.columns)[:6]
            df = df[columns]
            
            # Create table data including header
            table_data = [columns]
            for _, row in df.iterrows():
                table_data.append([str(row[col])[:30] for col in columns])  # Truncate long values
            
            # Create the table
            table = Table(table_data, repeatRows=1)
            
            # Add style
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            content.append(table)
            content.append(Spacer(1, 0.25 * inch))
        
        # Add recommendations
        content.append(Paragraph("Recommendations", styles['Heading2']))
        recommendations = [
            "Focus on the highest performing segments identified in the analysis to maximize returns.",
            "Address the underperforming areas with targeted strategies based on the insights provided.",
            "Monitor the trends identified in this report and establish regular reporting cycles.",
            "Consider further detailed analysis on specific areas of interest highlighted in this report."
        ]
        for rec in recommendations:
            content.append(Paragraph(f"• {rec}", styles['Normal']))
        
        # Add footer
        content.append(Spacer(1, 0.5 * inch))
        content.append(Paragraph("Generated by Business Report Generator", styles['Normal']))
        
        # Build the PDF
        doc.build(content)
        
        logger.info(f"PDF report generated successfully: {output_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error generating PDF report: {str(e)}")
        return False

def generate_chart_image(viz_data):
    """
    Generate an image from visualization data.
    
    Args:
        viz_data (dict): Visualization data
    
    Returns:
        BytesIO: Image data or None if generation fails
    """
    try:
        # Create a BytesIO object to store the image
        img_data = BytesIO()
        
        # Create a figure
        plt.figure(figsize=(10, 6))
        
        # Get chart type and data
        chart_type = viz_data.get('type', 'bar')
        labels = viz_data.get('labels', [])
        datasets = viz_data.get('datasets', [])
        
        if not labels or not datasets:
            return None
        
        # Generate the appropriate chart
        if chart_type == 'bar':
            # For bar chart with multiple datasets
            x = range(len(labels))
            width = 0.8 / len(datasets)
            
            for i, dataset in enumerate(datasets):
                offset = width * i - (width * (len(datasets) - 1)) / 2
                plt.bar([pos + offset for pos in x], dataset.get('data', []), width=width, 
                       label=dataset.get('label', f'Dataset {i+1}'))
            
            plt.xlabel('Categories')
            plt.ylabel('Values')
            plt.title(viz_data.get('title', 'Bar Chart'))
            plt.xticks(x, labels, rotation=45)
            plt.legend()
            
        elif chart_type == 'line':
            # For line chart with multiple datasets
            for i, dataset in enumerate(datasets):
                plt.plot(labels, dataset.get('data', []), label=dataset.get('label', f'Dataset {i+1}'))
            
            plt.xlabel('Time Period')
            plt.ylabel('Values')
            plt.title(viz_data.get('title', 'Line Chart'))
            plt.xticks(rotation=45)
            plt.legend()
            
        elif chart_type == 'pie':
            # For pie chart (first dataset only)
            if datasets and 'data' in datasets[0]:
                plt.pie(datasets[0]['data'], labels=labels, autopct='%1.1f%%')
                plt.title(viz_data.get('title', 'Pie Chart'))
            
        elif chart_type == 'scatter':
            # For scatter plot (first dataset only)
            if datasets and 'data' in datasets[0] and len(datasets[0]['data']) >= 2:
                x_data = datasets[0]['data'][0]
                y_data = datasets[0]['data'][1]
                plt.scatter(x_data, y_data)
                plt.xlabel(labels[0] if labels else 'X')
                plt.ylabel(labels[1] if len(labels) > 1 else 'Y')
                plt.title(viz_data.get('title', 'Scatter Plot'))
        
        # Adjust layout
        plt.tight_layout()
        
        # Save the figure to the BytesIO object
        plt.savefig(img_data, format='png')
        plt.close()
        
        # Reset the file pointer
        img_data.seek(0)
        
        return img_data
    
    except Exception as e:
        logger.error(f"Error generating chart image: {str(e)}")
        return None

def generate_excel_report(report, data, output_path):
    """
    Generate an Excel report with the analyzed data.
    
    Args:
        report (Report): Report object from database
        data (list): Processed financial data
        output_path (str): Path to save the Excel report
    
    Returns:
        bool: True if report generation was successful, False otherwise
    """
    try:
        # Convert data to DataFrame
        if not isinstance(data, list) or not data:
            logger.error("Invalid data for Excel report")
            return False
        
        df = pd.DataFrame(data)
        
        # Create a Pandas Excel writer
        writer = pd.ExcelWriter(output_path, engine='xlsxwriter')
        
        # Write the data to a sheet named 'Data'
        df.to_excel(writer, sheet_name='Data', index=False)
        
        # Get the workbook and worksheet objects
        workbook = writer.book
        worksheet = writer.sheets['Data']
        
        # Add formats
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        
        # Apply the header format
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num + 1, value, header_format)
            worksheet.set_column(col_num + 1, col_num + 1, 15)  # Set column width
        
        # Create a 'Summary' sheet
        summary_sheet = workbook.add_worksheet('Summary')
        
        # Add report information
        summary_sheet.write(0, 0, 'Report Title')
        summary_sheet.write(0, 1, report.title)
        summary_sheet.write(1, 0, 'Report Type')
        summary_sheet.write(1, 1, report.report_type)
        summary_sheet.write(2, 0, 'Generation Date')
        summary_sheet.write(2, 1, report.generation_date.strftime('%Y-%m-%d %H:%M'))
        
        # Add basic statistics for numeric columns
        summary_sheet.write(4, 0, 'Data Statistics', workbook.add_format({'bold': True}))
        
        row = 5
        for col in df.select_dtypes(include=['number']).columns:
            summary_sheet.write(row, 0, f'{col} (Mean)')
            summary_sheet.write(row, 1, df[col].mean())
            row += 1
            
            summary_sheet.write(row, 0, f'{col} (Sum)')
            summary_sheet.write(row, 1, df[col].sum())
            row += 1
            
            summary_sheet.write(row, 0, f'{col} (Min)')
            summary_sheet.write(row, 1, df[col].min())
            row += 1
            
            summary_sheet.write(row, 0, f'{col} (Max)')
            summary_sheet.write(row, 1, df[col].max())
            row += 2  # Add an extra blank row between stats
        
        # Save the Excel file
        writer.close()
        
        logger.info(f"Excel report generated successfully: {output_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error generating Excel report: {str(e)}")
        return False
