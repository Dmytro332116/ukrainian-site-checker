from jinja2 import Template
from typing import Dict, List
from datetime import datetime
import weasyprint
from sqlalchemy.orm import Session

from app.models import ScanSession, Website


class ReportGenerator:
    """Service for generating HTML and PDF reports."""
    
    HTML_TEMPLATE = """
    <!DOCTYPE html>
    <html lang="uk">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Звіт сканування - {{ website.name }}</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }
            h1, h2, h3 {
                color: #1976D2;
                margin-bottom: 15px;
            }
            .header {
                border-bottom: 3px solid #1976D2;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }
            .summary {
                background: #f5f5f5;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 30px;
            }
            .summary-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-top: 15px;
            }
            .summary-item {
                background: white;
                padding: 15px;
                border-radius: 5px;
                border-left: 4px solid #1976D2;
            }
            .summary-item h3 {
                font-size: 14px;
                color: #666;
                margin-bottom: 5px;
            }
            .summary-item .value {
                font-size: 28px;
                font-weight: bold;
                color: #1976D2;
            }
            .error-section {
                margin-bottom: 40px;
            }
            .error-card {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
            }
            .error-type {
                display: inline-block;
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                text-transform: uppercase;
                margin-right: 10px;
            }
            .error-type.spelling { background: #fff3cd; color: #856404; }
            .error-type.address { background: #f8d7da; color: #721c24; }
            .error-type.broken_link { background: #f8d7da; color: #721c24; }
            .error-type.phone { background: #fff3cd; color: #856404; }
            .error-type.seo { background: #d1ecf1; color: #0c5460; }
            .severity {
                display: inline-block;
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            .severity.error { background: #dc3545; color: white; }
            .severity.warning { background: #ffc107; color: #333; }
            .severity.info { background: #17a2b8; color: white; }
            .severity.critical { background: #e91e63; color: white; }
            .error-details {
                margin-top: 15px;
            }
            .error-message {
                font-size: 16px;
                margin-bottom: 10px;
            }
            .error-context {
                background: #f8f9fa;
                padding: 10px;
                border-left: 3px solid #dee2e6;
                margin: 10px 0;
                font-family: monospace;
                font-size: 14px;
            }
            .error-suggestion {
                background: #d4edda;
                padding: 10px;
                border-left: 3px solid #28a745;
                margin: 10px 0;
                color: #155724;
            }
            .page-info {
                color: #666;
                font-size: 14px;
                margin-bottom: 15px;
            }
            .footer {
                margin-top: 50px;
                padding-top: 20px;
                border-top: 2px solid #e0e0e0;
                text-align: center;
                color: #666;
                font-size: 14px;
            }
            @media print {
                body { padding: 10px; }
                .error-card { page-break-inside: avoid; }
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Звіт сканування сайту</h1>
            <p><strong>Сайт:</strong> {{ website.name }} ({{ website.url }})</p>
            <p><strong>Дата сканування:</strong> {{ scan.created_at.strftime('%d.%m.%Y %H:%M') }}</p>
            <p><strong>Статус:</strong> {{ scan_status_text }}</p>
        </div>

        <div class="summary">
            <h2>Загальна статистика</h2>
            <div class="summary-grid">
                <div class="summary-item">
                    <h3>Знайдено сторінок</h3>
                    <div class="value">{{ scan.pages_found }}</div>
                </div>
                <div class="summary-item">
                    <h3>Оброблено сторінок</h3>
                    <div class="value">{{ scan.pages_processed }}</div>
                </div>
                <div class="summary-item">
                    <h3>Знайдено помилок</h3>
                    <div class="value">{{ scan.errors_found }}</div>
                </div>
                <div class="summary-item">
                    <h3>Критичні помилки</h3>
                    <div class="value">{{ stats.critical }}</div>
                </div>
            </div>
        </div>

        {% if stats.by_type %}
        <div class="error-section">
            <h2>Помилки за типами</h2>
            <div class="summary-grid">
                {% for error_type, count in stats.by_type.items() %}
                <div class="summary-item">
                    <h3>{{ error_type_names[error_type] }}</h3>
                    <div class="value">{{ count }}</div>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endif %}

        {% if pages_with_errors %}
        <div class="error-section">
            <h2>Детальний список помилок</h2>
            
            {% for page in pages_with_errors %}
            <div class="error-card">
                <h3>{{ page.title or page.url }}</h3>
                <div class="page-info">
                    <strong>URL:</strong> {{ page.url }}<br>
                    <strong>Статус код:</strong> {{ page.status_code }}<br>
                    <strong>Помилок на сторінці:</strong> {{ page.errors|length }}
                </div>
                
                {% for error in page.errors %}
                <div class="error-details">
                    <span class="error-type {{ error.error_type }}">
                        {{ error_type_names[error.error_type] }}
                    </span>
                    <span class="severity {{ error.severity }}">
                        {{ severity_names[error.severity] }}
                    </span>
                    
                    <div class="error-message">{{ error.message }}</div>
                    
                    {% if error.context %}
                    <div class="error-context">
                        <strong>Контекст:</strong><br>
                        {{ error.context }}
                    </div>
                    {% endif %}
                    
                    {% if error.suggestion %}
                    <div class="error-suggestion">
                        <strong>💡 Рекомендація:</strong> {{ error.suggestion }}
                    </div>
                    {% endif %}
                </div>
                {% if not loop.last %}<hr style="margin: 20px 0; border: none; border-top: 1px solid #e0e0e0;">{% endif %}
                {% endfor %}
            </div>
            {% endfor %}
        </div>
        {% endif %}

        <div class="footer">
            <p>Згенеровано Ukrainian Site Checker v1.0.0</p>
            <p>{{ now.strftime('%d.%m.%Y %H:%M:%S') }}</p>
        </div>
    </body>
    </html>
    """
    
    ERROR_TYPE_NAMES = {
        'spelling': 'Орфографія',
        'address': 'Формат адреси',
        'broken_link': 'Битi посилання',
        'phone': 'Телефонні номери',
        'seo': 'SEO',
    }
    
    SEVERITY_NAMES = {
        'info': 'Інформація',
        'warning': 'Попередження',
        'error': 'Помилка',
        'critical': 'Критична',
    }
    
    STATUS_NAMES = {
        'pending': 'Очікується',
        'running': 'Виконується',
        'completed': 'Завершено',
        'failed': 'Помилка',
    }
    
    def generate_html_report(self, scan: ScanSession) -> str:
        """Generate HTML report for scan session."""
        # Calculate statistics
        stats = self._calculate_stats(scan)
        
        # Get pages with errors
        pages_with_errors = [p for p in scan.pages if p.errors]
        
        # Render template
        template = Template(self.HTML_TEMPLATE)
        html = template.render(
            scan=scan,
            website=scan.website,
            pages_with_errors=pages_with_errors,
            stats=stats,
            error_type_names=self.ERROR_TYPE_NAMES,
            severity_names=self.SEVERITY_NAMES,
            scan_status_text=self.STATUS_NAMES.get(scan.status, scan.status),
            now=datetime.now(),
        )
        
        return html
    
    def generate_pdf_report(self, scan: ScanSession) -> bytes:
        """Generate PDF report from HTML."""
        html = self.generate_html_report(scan)
        pdf = weasyprint.HTML(string=html).write_pdf()
        return pdf
    
    def _calculate_stats(self, scan: ScanSession) -> Dict:
        """Calculate error statistics."""
        stats = {
            'critical': 0,
            'by_type': {},
            'by_severity': {},
        }
        
        for page in scan.pages:
            for error in page.errors:
                # Count by severity
                if error.severity == 'critical':
                    stats['critical'] += 1
                
                stats['by_severity'][error.severity] = stats['by_severity'].get(error.severity, 0) + 1
                stats['by_type'][error.error_type] = stats['by_type'].get(error.error_type, 0) + 1
        
        return stats

