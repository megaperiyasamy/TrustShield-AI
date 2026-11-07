from pathlib import Path
import json
from xml.sax.saxutils import escape
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib import colors
from reportlab.lib.units import mm

def create_report(analysis, user_name, out_dir):
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    path = Path(out_dir) / f"trustshield_report_{analysis.id}.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=16*mm, leftMargin=16*mm, topMargin=16*mm, bottomMargin=16*mm)
    styles = getSampleStyleSheet()
    styles["Title"].textColor = colors.HexColor("#4C1D95")      # deep purple
    styles["Heading2"].textColor = colors.HexColor("#2F6BFF")   # electric blue
    story = [Paragraph("AI TrustShield — Screening Report", styles["Title"]), Spacer(1, 4), HRFlowable(width="100%", thickness=2, color=colors.HexColor("#22D3EE")), Spacer(1, 10)]
    story += [Paragraph(f"User: {escape(str(user_name))}", styles["BodyText"]), Paragraph(f"Document: {escape(str(analysis.filename))}", styles["BodyText"]), Paragraph(f"Type: {escape(str(analysis.document_type))}", styles["BodyText"]), Spacer(1, 10)]
    data = [["Risk Level", analysis.risk_level], ["AI Screening Score", f"{analysis.score}/100"], ["Confidence", f"{analysis.confidence}%"], ["Issues Detected", str(analysis.issues_count)]]
    table_style = TableStyle([("GRID",(0,0),(-1,-1),0.5,colors.HexColor("#C4B5FD")),("BACKGROUND",(0,0),(0,-1),colors.HexColor("#EDE9FE")),("VALIGN",(0,0),(-1,-1),"TOP")])
    story.append(Table(data, colWidths=[55*mm, 110*mm], style=table_style))
    story.append(Spacer(1, 14)); story.append(Paragraph("Findings", styles["Heading2"]))
    findings = json.loads(analysis.findings_json or "[]")
    recommendations = json.loads(analysis.recommendations_json or "[]")
    for f in findings:
        story.append(Paragraph(f"<b>{escape(str(f['severity']).upper())} — {escape(str(f['title']))}</b>", styles["BodyText"]))
        story.append(Paragraph(escape(str(f["detail"])), styles["BodyText"]))
        if f.get("evidence"): story.append(Paragraph(f"Evidence: {escape(str(f['evidence'])[:500])}", styles["BodyText"]))
        story.append(Spacer(1, 6))
    story.append(Paragraph("Recommendations", styles["Heading2"]))
    for item in recommendations: story.append(Paragraph("• " + escape(str(item)), styles["BodyText"]))
    story.append(Spacer(1, 12)); story.append(Paragraph("Disclaimer: This report is an AI screening aid. It does not prove authenticity or fraud. Important documents should be verified with the issuing organization or another official source.", styles["Italic"]))
    doc.build(story)
    return path
