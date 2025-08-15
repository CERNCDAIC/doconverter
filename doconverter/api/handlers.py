#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (C) 2017, CERN
# This software is distributed under the terms of the GNU General Public
# Licence version 3 (GPL Version 3), copied verbatim in the file "LICENSE".
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as Intergovernmental Organization
# or submit itself to any jurisdiction.

from flask import Flask, render_template_string
from flask_restful import Api
from doconverter.api.UploadFile import UploadFile
from doconverter.api.ReceivedFile import ReceivedFile
from doconverter.api.MonitorWWW import MonitorWWW
from doconverter.api.Stats import Stats
from flask_sqlalchemy import SQLAlchemy
from doconverter.config import APPCONFIG


app = Flask(__name__)
app.debug = True
# limit the maximum size of files to be upload to 400 MB
app.config['MAX_CONTENT_LENGTH'] = 2000 * 1024 * 1024

api = Api(app)


app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = APPCONFIG['SQLALCHEMY_DATABASE_URI']
app.config['SQLALCHEMY_POOL_SIZE'] = 20
app.config['SQLALCHEMY_POOL_RECYCLE'] = 1
db = SQLAlchemy(app)


@app.route('/')
def index():
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CERN Document Converter Service</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #333;
                min-height: 100vh;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 10px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                overflow: hidden;
            }
            .header {
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                color: white;
                padding: 40px;
                text-align: center;
            }
            .header h1 {
                margin: 0;
                font-size: 2.5em;
                font-weight: 300;
            }
            .header p {
                margin: 10px 0 0 0;
                font-size: 1.2em;
                opacity: 0.9;
            }
            .content {
                padding: 40px;
            }
            .section {
                margin-bottom: 30px;
            }
            .section h2 {
                color: #1e3c72;
                border-bottom: 2px solid #e0e0e0;
                padding-bottom: 10px;
                margin-bottom: 20px;
            }
            .api-endpoint {
                background: #f8f9fa;
                border-left: 4px solid #007bff;
                padding: 15px;
                margin: 10px 0;
                border-radius: 0 5px 5px 0;
            }
            .api-endpoint h3 {
                margin: 0 0 10px 0;
                color: #007bff;
            }
            .method {
                display: inline-block;
                background: #28a745;
                color: white;
                padding: 4px 8px;
                border-radius: 3px;
                font-size: 0.8em;
                font-weight: bold;
                margin-right: 10px;
            }
            .endpoint-url {
                font-family: 'Courier New', monospace;
                background: #e9ecef;
                padding: 2px 6px;
                border-radius: 3px;
                color: #495057;
            }
            .features {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }
            .feature-card {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                border: 1px solid #e9ecef;
            }
            .feature-card h3 {
                color: #1e3c72;
                margin-top: 0;
            }
            .status {
                text-align: center;
                padding: 20px;
                background: #d4edda;
                color: #155724;
                border-radius: 5px;
                margin: 20px 0;
            }
            .footer {
                background: #f8f9fa;
                padding: 20px;
                text-align: center;
                border-top: 1px solid #e9ecef;
                color: #6c757d;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📄 CERN Document Converter</h1>
                <p>Automated document conversion service for various file formats</p>
            </div>
            
            <div class="content">
                <div class="status">
                    ✅ Service is running and ready to process document conversions
                </div>
                
                <div class="section">
                    <h2>🚀 API Endpoints</h2>
                    <div class="api-endpoint">
                        <h3><span class="method">POST</span> Upload Files</h3>
                        <p><span class="endpoint-url">/doconverter/api/v1.0/uploads</span></p>
                        <p>Upload files for conversion to various formats (PDF, PDF/A, PS, thumbnails, etc.)</p>
                    </div>
                    
                    <div class="api-endpoint">
                        <h3><span class="method">GET</span> Monitor Status</h3>
                        <p><span class="endpoint-url">/doconverter/api/v1.0/monitor</span></p>
                        <p>Monitor the status of conversion jobs</p>
                    </div>
                    
                    <div class="api-endpoint">
                        <h3><span class="method">GET</span> Received Files</h3>
                        <p><span class="endpoint-url">/doconverter/api/v1.0/received</span></p>
                        <p>Access converted files that have been processed</p>
                    </div>
                    
                    <div class="api-endpoint">
                        <h3><span class="method">GET</span> Statistics</h3>
                        <p><span class="endpoint-url">/doconverter/api/v1.0/stats/{report}</span></p>
                        <p>Get conversion statistics and reports</p>
                    </div>
                </div>
                
                <div class="section">
                    <h2>🔄 Supported Conversions</h2>
                    <div class="features">
                        <div class="feature-card">
                            <h3>📊 Office Documents</h3>
                            <p>Convert Office 2016, OpenOffice, RTF, HTML files to PDF, PDF/A, or PS formats</p>
                        </div>
                        <div class="feature-card">
                            <h3>🎨 Graphics & CAD</h3>
                            <p>Convert AutoCAD (CDX), CorelDraw (CDR), BMP, JPG, TIF files</p>
                        </div>
                        <div class="feature-card">
                            <h3>📄 PDF Processing</h3>
                            <p>Convert PDFs to images, create thumbnails, or extract pages</p>
                        </div>
                        <div class="feature-card">
                            <h3>🔍 OCR Processing</h3>
                            <p>OCR conversion for TIF, PNG, JPG files using Tesseract and MODI engines</p>
                        </div>
                        <div class="feature-card">
                            <h3>📏 Technical Drawings</h3>
                            <p>Convert PLT files to PDF with HPGL converter</p>
                        </div>
                        <div class="feature-card">
                            <h3>✏️ Word Documents</h3>
                            <p>Special handling for DOC/DOCX with revision control options</p>
                        </div>
                    </div>
                </div>
                
                <div class="section">
                    <h2>📖 How to Use</h2>
                    <p>The service uses a REST API with no authentication required. Upload your file using multipart/form-data and specify:</p>
                    <ul>
                        <li><strong>uploadedfile</strong>: Your file to convert</li>
                        <li><strong>converter</strong>: Target format (pdf, pdfa, ps, thumb, etc.)</li>
                        <li><strong>dirresponse</strong>: Where to store the converted file</li>
                        <li><strong>urlresponse</strong>: Callback URL for notifications</li>
                        <li><strong>options</strong>: Format-specific conversion options</li>
                    </ul>
                </div>
            </div>
            
            <div class="footer">
                <p>© CERN - Document Conversion Service | <a href="https://github.com/CERNCDAIC/doconverter" target="_blank">GitHub Repository</a></p>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html_template)


@app.route('/redirect')
def redirect_to_api():
    """Alternative route that redirects to the API documentation or a specific endpoint"""
    from flask import redirect
    return redirect('/doconverter/api/v1.0/monitor', code=302)


api.add_resource(UploadFile, '/doconverter/api/v1.0/uploads')
api.add_resource(MonitorWWW, '/doconverter/api/v1.0/monitor')
api.add_resource(ReceivedFile, '/doconverter/api/v1.0/received')
api.add_resource(Stats, '/doconverter/api/v1.0/stats/<int:report>')
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
    # app.run(debug=True)
