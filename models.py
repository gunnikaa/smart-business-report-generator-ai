import datetime
from app import db

class DataFile(db.Model):
    """Model representing uploaded financial data files"""
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # e.g., 'csv', 'excel', 'json'
    upload_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    file_size = db.Column(db.Integer)  # Size in bytes
    
    # Foreign keys
    reports = db.relationship('Report', back_populates='data_file', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<DataFile {self.filename}>"

class Report(db.Model):
    """Model representing generated business reports"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    generation_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    report_type = db.Column(db.String(50), nullable=False)  # e.g., 'financial', 'sales', 'trend'
    pdf_path = db.Column(db.String(255))  # Path to stored PDF file
    excel_path = db.Column(db.String(255))  # Path to stored Excel file
    
    # Relationship with data file
    data_file_id = db.Column(db.Integer, db.ForeignKey('data_file.id'), nullable=False)
    data_file = db.relationship('DataFile', back_populates='reports')
    
    # Relationship with insights
    insights = db.relationship('Insight', back_populates='report', cascade='all, delete-orphan')
    
    # Relationship with visualizations
    visualizations = db.relationship('Visualization', back_populates='report', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Report {self.title}>"

class Insight(db.Model):
    """Model representing NLP-generated insights from report data"""
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    confidence = db.Column(db.Float)  # Confidence score of the insight
    category = db.Column(db.String(100))  # e.g., 'trend', 'anomaly', 'recommendation'
    
    # Relationship with report
    report_id = db.Column(db.Integer, db.ForeignKey('report.id'), nullable=False)
    report = db.relationship('Report', back_populates='insights')
    
    def __repr__(self):
        return f"<Insight {self.id}: {self.text[:30]}...>"

class Visualization(db.Model):
    """Model representing data visualizations generated for reports"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    chart_type = db.Column(db.String(50), nullable=False)  # e.g., 'bar', 'line', 'pie'
    data_json = db.Column(db.Text, nullable=False)  # JSON representation of the visualization data
    description = db.Column(db.Text)
    
    # Relationship with report
    report_id = db.Column(db.Integer, db.ForeignKey('report.id'), nullable=False)
    report = db.relationship('Report', back_populates='visualizations')
    
    def __repr__(self):
        return f"<Visualization {self.title}>"
