import os
import logging
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import render_template, request, redirect, url_for, flash, jsonify, send_from_directory, session
from app import db
from models import DataFile, Report, Insight, Visualization
from data_processor import process_data_file, validate_file
from report_generator import generate_pdf_report, generate_excel_report
from nlp_analyzer import analyze_data
from visualizer import create_visualizations

# Configure logging
logger = logging.getLogger(__name__)

UPLOAD_FOLDER = '/tmp/uploads'
REPORT_FOLDER = '/tmp/reports'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'json'}

# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)

def register_routes(app):
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/upload', methods=['POST'])
    def upload_file():
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        
        if file and validate_file(file.filename, ALLOWED_EXTENSIONS):
            try:
                filename = secure_filename(file.filename)
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)
                
                # Get file extension
                file_extension = filename.rsplit('.', 1)[1].lower()
                
                # Create database record for the file
                data_file = DataFile(
                    filename=filename,
                    file_type=file_extension,
                    file_size=os.path.getsize(file_path)
                )
                db.session.add(data_file)
                db.session.commit()
                
                # Process the file to extract data
                processed_data = process_data_file(file_path, file_extension)
                
                # Store only data_file_id in session
                session['data_file_id'] = data_file.id
                
                # Create a temporary file to store the processed data
                import pickle
                data_pickle_path = os.path.join(UPLOAD_FOLDER, f'data_{data_file.id}.pickle')
                with open(data_pickle_path, 'wb') as f:
                    pickle.dump(processed_data, f)
                
                flash('File successfully uploaded and processed', 'success')
                return redirect(url_for('dashboard'))
            
            except Exception as e:
                logger.error(f"Error processing file: {str(e)}")
                flash(f'Error processing file: {str(e)}', 'danger')
                return redirect(request.url)
        else:
            flash(f'Invalid file type. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}', 'danger')
            return redirect(request.url)
    
    @app.route('/dashboard')
    def dashboard():
        # Check if we have data file ID
        if 'data_file_id' not in session:
            flash('No data available. Please upload a file first.', 'warning')
            return redirect(url_for('index'))
        
        data_file_id = session['data_file_id']
        
        # Load processed data from pickle file
        import pickle
        data_pickle_path = os.path.join(UPLOAD_FOLDER, f'data_{data_file_id}.pickle')
        try:
            with open(data_pickle_path, 'rb') as f:
                processed_data = pickle.load(f)
        except FileNotFoundError:
            flash('Data file not found. Please upload a file again.', 'warning')
            return redirect(url_for('index'))
        
        # Get basic statistics and samples
        data_preview = processed_data[:5] if isinstance(processed_data, list) else processed_data
        
        # Generate basic insights
        insights = analyze_data(processed_data)
        
        # Generate visualization data
        viz_data = create_visualizations(processed_data)
        
        # Add current date for report title
        now = datetime.now()
        
        return render_template(
            'dashboard.html', 
            data_preview=data_preview,
            insights=insights,
            viz_data=json.dumps(viz_data),
            data_file_id=data_file_id,
            now=now
        )
    
    @app.route('/generate-report', methods=['POST'])
    def generate_report():
        if 'data_file_id' not in session:
            flash('No data available. Please upload a file first.', 'warning')
            return redirect(url_for('index'))
        
        report_title = request.form.get('report_title', f'Business Report - {datetime.now().strftime("%Y-%m-%d")}')
        report_type = request.form.get('report_type', 'financial')
        
        data_file_id = session['data_file_id']
        
        # Load processed data from pickle file
        import pickle
        data_pickle_path = os.path.join(UPLOAD_FOLDER, f'data_{data_file_id}.pickle')
        try:
            with open(data_pickle_path, 'rb') as f:
                processed_data = pickle.load(f)
        except FileNotFoundError:
            flash('Data file not found. Please upload a file again.', 'warning')
            return redirect(url_for('index'))
        
        try:
            # Get the data file
            data_file = DataFile.query.get(data_file_id)
            if not data_file:
                flash('Source data file not found', 'danger')
                return redirect(url_for('index'))
            
            # Create report record
            report = Report(
                title=report_title,
                report_type=report_type,
                data_file_id=data_file_id
            )
            db.session.add(report)
            db.session.commit()
            
            # Generate insights
            insights_data = analyze_data(processed_data)
            for insight_text in insights_data:
                insight = Insight(
                    text=insight_text,
                    confidence=0.85,  # Example confidence value
                    category='trend',
                    report_id=report.id
                )
                db.session.add(insight)
            
            # Generate visualizations
            viz_data = create_visualizations(processed_data)
            for i, viz in enumerate(viz_data):
                visualization = Visualization(
                    title=f"Chart {i+1}: {viz.get('title', 'Untitled')}",
                    chart_type=viz.get('type', 'bar'),
                    data_json=json.dumps(viz),
                    description=viz.get('description', ''),
                    report_id=report.id
                )
                db.session.add(visualization)
            
            # Save changes to database
            db.session.commit()
            
            # Generate PDF
            pdf_filename = f"report_{report.id}.pdf"
            pdf_path = os.path.join(REPORT_FOLDER, pdf_filename)
            generate_pdf_report(report, insights_data, viz_data, processed_data, pdf_path)
            
            # Generate Excel
            excel_filename = f"report_{report.id}.xlsx"
            excel_path = os.path.join(REPORT_FOLDER, excel_filename)
            generate_excel_report(report, processed_data, excel_path)
            
            # Update report with file paths
            report.pdf_path = pdf_filename
            report.excel_path = excel_filename
            db.session.commit()
            
            flash('Report generated successfully', 'success')
            return redirect(url_for('report_detail', report_id=report.id))
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            flash(f'Error generating report: {str(e)}', 'danger')
            return redirect(url_for('dashboard'))
    
    @app.route('/reports')
    def reports():
        # Get all reports
        all_reports = Report.query.order_by(Report.generation_date.desc()).all()
        return render_template('reports.html', reports=all_reports)
    
    @app.route('/reports/<int:report_id>')
    def report_detail(report_id):
        report = Report.query.get_or_404(report_id)
        return render_template('report_detail.html', report=report)
    
    @app.route('/download/<file_type>/<int:report_id>')
    def download_report(file_type, report_id):
        report = Report.query.get_or_404(report_id)
        
        if file_type == 'pdf' and report.pdf_path:
            return send_from_directory(REPORT_FOLDER, report.pdf_path, as_attachment=True)
        elif file_type == 'excel' and report.excel_path:
            return send_from_directory(REPORT_FOLDER, report.excel_path, as_attachment=True)
        else:
            flash('Requested file not found', 'danger')
            return redirect(url_for('report_detail', report_id=report_id))
