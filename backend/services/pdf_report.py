import io
from weasyprint import HTML
from backend.models.scan import ScanResult
from backend.models.audit import AuditRecord

def generate_scan_pdf_report(scan: ScanResult, audit_records: list[AuditRecord]) -> bytes:
    audit_rows_html = ""
    for a in audit_records:
        override_badge = "<span style='color: red; font-weight: bold;'>(Critical Overridden)</span>" if a.overrode_critical else ""
        audit_rows_html += f"""
        <tr>
            <td>{a.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</td>
            <td><strong>{a.action.upper()}</strong> {override_badge}</td>
            <td>{a.reviewer}</td>
            <td>{a.comment or '-'}</td>
        </tr>
        """

    findings_html = ""
    findings = scan.results.get("findings", []) if isinstance(scan.results, dict) else []
    for f in findings:
        severity = f.get("severity", "info").upper()
        rule = f.get("rule_name", "Compliance Rule")
        msg = f.get("message", "")
        findings_html += f"""
        <div style="margin-bottom: 8px; padding: 8px; border-left: 4px solid #3182ce; background: #f7fafc;">
            <strong>[{severity}] {rule}:</strong> {msg}
        </div>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: sans-serif; margin: 30px; color: #2d3748; }}
            h1 {{ color: #2b6cb0; border-bottom: 2px solid #2b6cb0; padding-bottom: 8px; }}
            .meta {{ margin-bottom: 20px; background: #edf2f7; padding: 12px; border-radius: 6px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
            th, td {{ border: 1px solid #cbd5e0; padding: 8px; text-align: left; }}
            th {{ background-color: #e2e8f0; }}
        </style>
    </head>
    <body>
        <h1>BrandVerify Audit Report</h1>
        <div class="meta">
            <p><strong>Scan ID:</strong> {scan.id}</p>
            <p><strong>Brand ID:</strong> {scan.brand_id}</p>
            <p><strong>Content Type:</strong> {scan.content_type}</p>
            <p><strong>Review Status:</strong> {scan.review_status.upper()}</p>
            <p><strong>Created At:</strong> {scan.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <h2>Findings & Compliance Flags</h2>
        {findings_html or '<p>No issues found.</p>'}

        <h2>Immutable Decision History</h2>
        <table>
            <thead>
                <tr>
                    <th>Timestamp</th>
                    <th>Action</th>
                    <th>Reviewer</th>
                    <th>Comment</th>
                </tr>
            </thead>
            <tbody>
                {audit_rows_html or '<tr><td colspan="4">No decision records found.</td></tr>'}
            </tbody>
        </table>
    </body>
    </html>
    """

    pdf_file = io.BytesIO()
    HTML(string=html_content).write_pdf(pdf_file)
    return pdf_file.getvalue()
