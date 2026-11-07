import re
from urllib.parse import urlparse

TYPE_LABELS = {
    "resume": "Resume / CV",
    "certificate": "Educational Certificate",
    "training": "Course / Training Certificate",
    "offer": "Experience / Offer Letter",
    "id": "ID Document",
    "legal": "Legal Document",
    "invoice": "Invoice / Bill",
    "contract": "Agreement / Contract",
    "email": "Email / Message",
    "url": "URL / Link",
    "other": "Other Document",
}

BASE_RULES = [
    (r"\b(password|otp|one[- ]time password)\b", "high", "Sensitive credential request detected", "The document/message mentions passwords or OTPs."),
    (r"\b(pay|payment|fee|deposit|transfer)\b.{0,60}\b(before|prior|advance)\b", "high", "Advance payment language detected", "Payment is requested before a stated action or benefit."),
    (r"\b(urgent|immediately|act now|within \d+ hours)\b", "medium", "Urgency language detected", "Urgency can be a risk signal when combined with other anomalies."),
    (r"\b(congratulations|selected|winner|guaranteed)\b", "low", "Promotional/selection claim detected", "This is a contextual signal, not proof of fraud."),
]

def analyze(text: str, doc_type: str, filename: str, extraction_warnings=None):
    text = text or ""
    low = text.lower()
    findings = []
    recommendations = []
    score = 100

    if not text.strip():
        findings.append({"severity":"medium","title":"Very little readable text","detail":"The system could not extract enough text for a meaningful content analysis.","evidence":"No readable text extracted."})
        score -= 25
        recommendations.append("Upload a clearer scan or enable OCR/Tesseract for image-based documents.")
    elif len(text.strip()) < 80:
        findings.append({"severity":"medium","title":"Limited document content","detail":"Only a small amount of readable text was available.","evidence":text.strip()[:300]})
        score -= 10
        recommendations.append("Review the original document manually and provide a clearer/full copy if needed.")

    for pattern, severity, title, detail in BASE_RULES:
        if re.search(pattern, low, re.S):
            findings.append({"severity":severity,"title":title,"detail":detail,"evidence":_snippet(text, pattern)})
            score -= {"high":18,"medium":8,"low":2}[severity]

    required = required_fields(doc_type)
    missing = [label for label, patterns in required if not any(re.search(p, low) for p in patterns)]
    if missing and text:
        for label in missing[:4]:
            findings.append({"severity":"medium","title":f"Could not locate {label}","detail":"The field was not detected in extracted text. It may still exist in the original document.","evidence":"Field not found by text rules."})
            score -= 5
        recommendations.append("Check the missing fields against the original document or official source.")

    if doc_type in {"invoice"}:
        amounts = re.findall(r"(?:₹|rs\.?|inr|\$|usd)\s?[\d,]+(?:\.\d{1,2})?", low)
        if not amounts:
            findings.append({"severity":"medium","title":"No monetary amount detected","detail":"An invoice normally contains an amount or total, but none was detected.","evidence":"No currency/amount pattern found."})
            score -= 8
            recommendations.append("Verify the invoice total, tax and line items manually.")

    if doc_type in {"certificate", "training"} and not re.search(r"(certificate|certif|awarded|completion|course)", low):
        findings.append({"severity":"medium","title":"Certificate context not detected","detail":"The text does not strongly identify itself as a certificate.","evidence":"Certificate-related keywords were not detected."})
        score -= 10

    if doc_type == "url":
        urls = re.findall(r"https?://[^\s]+", text)
        for u in urls[:5]:
            host = urlparse(u).netloc.lower()
            if host and any(x in host for x in ["bit.ly", "tinyurl", "t.co"]):
                findings.append({"severity":"medium","title":"Shortened URL detected","detail":"A shortened link hides the final destination and deserves extra verification.","evidence":u})
                score -= 10
                recommendations.append("Open links only after checking the destination domain and using an official source.")

    if extraction_warnings:
        for warning in extraction_warnings:
            findings.append({"severity":"medium","title":"Extraction warning","detail":warning,"evidence":"File processing"})
            score -= 3

    score = max(0, min(100, score))
    if any(f["severity"] == "high" for f in findings):
        score = min(score, 74)   # a high-severity finding keeps the result at Medium risk or worse
    if score >= 75:
        risk = "Low"
    elif score >= 45:
        risk = "Medium"
    else:
        risk = "High"

    if not findings:
        findings.append({"severity":"info","title":"No obvious screening anomalies found","detail":"The rule-based screening checks did not find a strong issue in the extracted content.","evidence":"No flagged pattern."})
        recommendations.append("For important documents, verify the issuer through an official channel.")
    if risk == "High":
        recommendations.insert(0, "Do not rely on this document alone; perform official or human verification before acting.")
    elif risk == "Medium":
        recommendations.insert(0, "Review the flagged items and verify important claims through an official source.")
    else:
        recommendations.insert(0, "No major screening anomaly was detected, but AI screening is not proof of authenticity.")

    confidence = max(55, min(96, 60 + min(25, len(text)//300) - min(10, len(findings))))
    return score, risk, confidence, findings, list(dict.fromkeys(recommendations))

def _snippet(text, pattern):
    m = re.search(pattern, text, re.I | re.S)
    if not m: return "Pattern matched in extracted text."
    return text[max(0,m.start()-70):min(len(text),m.end()+120)].replace("\n", " ").strip()

def required_fields(doc_type):
    common = [
        ("Name", [r"\bname\b", r"candidate", r"employee"]),
        ("Date", [r"\bdate\b", r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", r"\b20\d{2}\b"]),
    ]
    mapping = {
        "certificate": common + [("Institution", [r"university|college|institution|school|institute"]),("Certificate number", [r"certificate\s*(no|number|id)|cert\.?\s*no"])],
        "training": common + [("Training/course", [r"course|training|program|completion"])],
        "resume": [("Name", [r"\bname\b"]),("Education", [r"education|degree|\bb\.?s?c\b|\bb\.?e\b|\bm\.?c\.?a\b|\bm\.?b\.?a\b|university|college"]),("Experience", [r"experience|employment|worked|internship"])],
        "offer": common + [("Company", [r"company|organization|employer|inc\.|ltd\."]),("Designation", [r"designation|role|position|job title"])],
        "invoice": [("Invoice number", [r"invoice\s*(no|number|#|id)"]), ("Date", [r"\bdate\b"]), ("Amount", [r"total|amount|₹|inr|usd|\$"])],
        "contract": [("Parties", [r"between|party|parties|agreement"]),("Date", [r"\bdate\b"]),("Terms", [r"terms|obligation|termination|payment"])],
        "id": [("Name", [r"\bname\b"]),("Date", [r"date of birth|dob|date"]),("Expiry", [r"expiry|expires|valid until|validity"])],
        "legal": common + [("Parties", [r"party|parties|between"]),("Terms", [r"terms|clause|agreement"])],
    }
    if doc_type in {"url", "email", "other"}:
        return []          # no fixed mandatory fields for links, messages or generic documents
    return mapping.get(doc_type, common)
