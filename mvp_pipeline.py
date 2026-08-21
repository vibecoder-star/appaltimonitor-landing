#!/usr/bin/env python3
"""
AppaltiMonitor — TED Concierge MVP
Modular pipeline for public procurement intelligence
"""

import csv
import json
import os
import re
import ssl
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter, defaultdict

# Configuration
BASE_DIR = Path("/opt/autonomous-venture-engine/appalti-monitor")
OUTPUT_DIR = BASE_DIR / "output"
PROFILES_DIR = BASE_DIR / "profiles"
REPORTS_DIR = BASE_DIR / "reports"
KPIS_DIR = BASE_DIR / "kpis"

for d in [OUTPUT_DIR, PROFILES_DIR, REPORTS_DIR, KPIS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

TED_API_URL = "https://api.ted.europa.eu/v3/notices/search"

# CPV code mapping (common Italian procurement codes)
CPV_MAPPING = {
    "72": "IT services",
    "48": "Software packages",
    "302": "IT equipment",
    "45": "Construction work",
    "44": "Structures",
    "43": "Industrial work",
    "90": "Sewage/sanitation",
    "99": "Other services",
    "71": "Architectural/engineering",
    "50": "Repair/maintenance",
    "34": "Transport equipment",
    "09": "Energy",
    "33": "Medical devices",
    "79": "Support services",
    "55": "Hotel/restaurant",
    "66": "Financial services",
    "73": "Research/development",
    "80": "Education",
    "85": "Health/social",
    "92": "Recreational",
    "98": "Community/personal"
}

class TEDAPIClient:
    """Client for TED Search API v3"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.base_url = TED_API_URL
        self.ssl_context = ssl.create_default_context()
    
    def search(self, query, fields, page=1, limit=50):
        """Execute a search query against TED API"""
        payload = {
            "query": query,
            "fields": fields,
            "page": page,
            "limit": limit,
            "scope": "ALL",
            "checkQuerySyntax": False,
            "paginationMode": "PAGE_NUMBER",
            "onlyLatestVersions": False
        }
        
        if self.api_key:
            payload["apiKey"] = self.api_key
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        req = urllib.request.Request(
            self.base_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=30, context=self.ssl_context) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8") if e.fp else ""
            return {"error": True, "status": e.code, "message": body}
        except Exception as e:
            return {"error": True, "message": str(e)}
    
    def build_query(self, profile, date_from=None, date_to=None):
        """Build TED expert query from customer profile"""
        if not date_from:
            date_from = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")
        if not date_to:
            date_to = datetime.now().strftime("%Y%m%d")
        
        # Date filter
        date_filter = f"publication-date = ({date_from} <> {date_to})"
        
        # Country filter (use ISO 3166-1 alpha-3: ITA for Italy)
        countries = " ".join(profile.get("countries", ["ITA"]))
        country_filter = f"organisation-country-buyer IN ({countries})"
        
        # CPV filter
        cpv_codes = " ".join([f"{cpv}*" for cpv in profile.get("cpv_codes", [])])
        cpv_filter = f"classification-cpv IN ({cpv_codes})"
        
        # Combine
        return f"({date_filter}) AND ({country_filter}) AND ({cpv_filter})"
    
    def get_default_fields(self):
        """Return default fields to retrieve"""
        return [
            "notice-identifier",
            "notice-title",
            "buyer-name",
            "buyer-country",
            "place-of-performance",
            "classification-cpv",
            "publication-date",
            "deadline-receipt-tender-date-lot",
            "estimated-value-cur-lot",
            "form-type"
        ]


class ProfileEngine:
    """Manage customer profiles"""
    
    def __init__(self, profiles_dir=PROFILES_DIR):
        self.profiles_dir = profiles_dir
    
    def create_profile(self, profile_data):
        """Create and validate a new customer profile"""
        profile = {
            "id": profile_data.get("id", f"profile_{datetime.now().strftime('%Y%m%d%H%M%S')}"),
            "company_name": profile_data.get("company_name", "Unknown"),
            "industry": profile_data.get("industry", ""),
            "cpv_codes": profile_data.get("cpv_codes", []),
            "cpv_detailed": profile_data.get("cpv_detailed", []),
            "countries": profile_data.get("countries", ["IT"]),
            "value_min": profile_data.get("value_min", 10000),
            "value_max": profile_data.get("value_max", 1000000),
            "excluded_categories": profile_data.get("excluded_categories", []),
            "keywords": profile_data.get("keywords", []),
            "excluded_keywords": profile_data.get("excluded_keywords", []),
            "preferred_buyers": profile_data.get("preferred_buyers", []),
            "notes": profile_data.get("notes", ""),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Save profile
        profile_path = self.profiles_dir / f"{profile['id']}.json"
        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)
        
        return profile
    
    def load_profile(self, profile_id):
        """Load a profile by ID"""
        profile_path = self.profiles_dir / f"{profile_id}.json"
        if not profile_path.exists():
            return None
        with open(profile_path, "r") as f:
            return json.load(f)
    
    def list_profiles(self):
        """List all available profiles"""
        profiles = []
        for p in self.profiles_dir.glob("*.json"):
            with open(p, "r") as f:
                profiles.append(json.load(f))
        return profiles


class RelevanceEngine:
    """Score and rank tenders by relevance"""
    
    def __init__(self, profile):
        self.profile = profile
    
    def score_tender(self, tender):
        """Calculate relevance score for a tender"""
        scores = {
            "cpv": 0,
            "geography": 0,
            "value": 0,
            "deadline": 0,
            "keyword": 0,
            "buyer": 0
        }
        reasons = []
        
        # CPV score (0-30) - check ALL CPVs in the list
        cpv_list = tender.get("cpv_list", [])
        if not cpv_list:
            cpv_list = [tender.get("cpv", "")]
        
        for code in self.profile.get("cpv_codes", []):
            for cpv in cpv_list:
                if cpv.startswith(code):
                    scores["cpv"] = 30
                    reasons.append(f"CPV match: {code} (found {cpv})")
                    break
            if scores["cpv"] > 0:
                break
        
        # Detailed CPV bonus (0-10)
        for code in self.profile.get("cpv_detailed", []):
            for cpv in cpv_list:
                if cpv.startswith(code):
                    scores["cpv"] += 10
                    reasons.append(f"Detailed CPV match: {code} (found {cpv})")
                    break
            if scores["cpv"] > 30:
                break
        
        # Geography score (0-20)
        place = tender.get("place_performance", "").upper()
        for country in self.profile.get("countries", ["IT"]):
            if country.upper() in place:
                scores["geography"] = 20
                reasons.append(f"Location match: {country}")
                break
        
        # Value score (0-20)
        value = tender.get("estimated_value")
        if value:
            vmin = self.profile.get("value_min", 0)
            vmax = self.profile.get("value_max", 1000000)
            if vmin <= value <= vmax:
                scores["value"] = 20
                reasons.append(f"Value in range: €{value:,.0f}")
            elif value < vmin:
                scores["value"] = 5
                reasons.append(f"Value below range: €{value:,.0f}")
            else:
                scores["value"] = 10
                reasons.append(f"Value above range: €{value:,.0f}")
        
        # Deadline score (0-15)
        if tender.get("is_active"):
            scores["deadline"] = 15
            reasons.append("Active deadline")
        elif tender.get("deadline"):
            scores["deadline"] = 5
            reasons.append("Deadline passed")
        
        # Keyword score (0-10)
        title = tender.get("title", "").lower()
        for kw in self.profile.get("keywords", []):
            if kw.lower() in title:
                scores["keyword"] = 10
                reasons.append(f"Keyword match: {kw}")
                break
        
        # Buyer preference score (0-5)
        buyer = tender.get("buyer", "").upper()
        for bp in self.profile.get("preferred_buyers", []):
            if bp.upper() in buyer:
                scores["buyer"] = 5
                reasons.append(f"Preferred buyer: {bp}")
                break
        
        # Calculate total
        total = sum(scores.values())
        
        # Confidence level
        if total >= 70:
            confidence = "HIGH"
        elif total >= 40:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"
        
        return {
            "total": total,
            "breakdown": scores,
            "reasons": reasons,
            "confidence": confidence
        }


class QualityControl:
    """Validate tender data quality"""
    
    REQUIRED_FIELDS = ["notice_id", "title", "buyer", "publication_date"]
    IMPORTANT_FIELDS = ["deadline", "estimated_value", "cpv", "place_performance"]
    
    def validate(self, tender):
        """Validate a tender record"""
        issues = []
        warnings = []
        
        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if not tender.get(field):
                issues.append(f"Missing required field: {field}")
        
        # Check important fields
        for field in self.IMPORTANT_FIELDS:
            if not tender.get(field):
                warnings.append(f"Missing important field: {field}")
        
        # Validate dates
        if tender.get("publication_date"):
            try:
                datetime.strptime(tender["publication_date"], "%Y-%m-%d")
            except:
                issues.append("Invalid publication_date format")
        
        if tender.get("deadline"):
            try:
                datetime.strptime(tender["deadline"], "%Y-%m-%d")
            except:
                warnings.append("Invalid deadline format")
        
        # Validate value
        if tender.get("estimated_value") is not None:
            if tender["estimated_value"] < 0:
                issues.append("Negative estimated value")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "quality": "HIGH" if len(issues) == 0 and len(warnings) == 0 else
                      "MEDIUM" if len(issues) == 0 else "LOW"
        }


class ReportGenerator:
    """Generate professional intelligence reports"""
    
    def __init__(self, profile, tenders, kpis):
        self.profile = profile
        self.tenders = tenders
        self.kpis = kpis
    
    def generate_markdown(self):
        """Generate Markdown report"""
        lines = []
        
        # Header
        lines.append(f"# Public Procurement Intelligence Report")
        lines.append(f"")
        lines.append(f"**Company:** {self.profile.get('company_name', 'Unknown')}  ")
        lines.append(f"**Industry:** {self.profile.get('industry', 'N/A')}  ")
        lines.append(f"**Report Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}  ")
        lines.append(f"**Period:** Last 7 days  ")
        lines.append(f"")
        lines.append(f"---")
        lines.append(f"")
        
        # Executive Summary
        lines.append(f"## Executive Summary")
        lines.append(f"")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Total opportunities retrieved | {self.kpis['total_retrieved']} |")
        lines.append(f"| Relevant opportunities | {self.kpis['relevant']} |")
        lines.append(f"| High priority | {self.kpis['high_priority']} |")
        lines.append(f"| Medium priority | {self.kpis['medium_priority']} |")
        lines.append(f"| Low priority | {self.kpis['low_priority']} |")
        lines.append(f"| With deadline | {self.kpis['with_deadline']} ({self.kpis['with_deadline_pct']:.0f}%) |")
        lines.append(f"| With estimated value | {self.kpis['with_value']} ({self.kpis['with_value_pct']:.0f}%) |")
        lines.append(f"| Processing time | {self.kpis['processing_time']:.1f}s |")
        lines.append(f"")
        
        # Top 5 Opportunities
        high = [t for t in self.tenders if t.get("confidence") == "HIGH"][:5]
        if high:
            lines.append(f"## Top {len(high)} Opportunities")
            lines.append(f"")
            for i, t in enumerate(high, 1):
                lines.append(f"### {i}. {t.get('title', 'Untitled')}")
                lines.append(f"")
                lines.append(f"| Field | Value |")
                lines.append(f"|-------|-------|")
                lines.append(f"| **Score** | {t.get('score', 0)}/100 ({t.get('confidence', 'N/A')}) |")
                lines.append(f"| **Buyer** | {t.get('buyer', 'N/A')} |")
                lines.append(f"| **Location** | {t.get('place_performance', 'N/A')} |")
                lines.append(f"| **CPV** | {t.get('cpv', 'N/A')} |")
                lines.append(f"| **Publication Date** | {t.get('publication_date', 'N/A')} |")
                lines.append(f"| **Deadline** | {t.get('deadline', 'N/A')} {'✅' if t.get('is_active') else '⚠️'} |")
                if t.get('estimated_value'):
                    lines.append(f"| **Estimated Value** | €{t.get('estimated_value'):,.2f} |")
                else:
                    lines.append(f"| **Estimated Value** | N/A |")
                lines.append(f"| **Procedure** | {t.get('procedure_type', 'N/A')} |")
                lines.append(f"| **Source** | [View on TED]({t.get('source_url', '#')}) |")
                lines.append(f"")
                lines.append(f"**Why this matches:** {'; '.join(t.get('match_reasons', []))}")
                lines.append(f"")
                if t.get("quality_warnings"):
                    lines.append(f"**⚠️ Data limitations:** {'; '.join(t['quality_warnings'])}")
                    lines.append(f"")
                lines.append(f"---")
                lines.append(f"")
        
        # Medium Priority
        medium = [t for t in self.tenders if t.get("confidence") == "MEDIUM"][:5]
        if medium:
            lines.append(f"## Medium Priority ({len(medium)} opportunities)")
            lines.append(f"")
            for i, t in enumerate(medium, 1):
                lines.append(f"{i}. **{t.get('title', 'Untitled')[:60]}**  ")
                lines.append(f"   Score: {t.get('score', 0)} | Buyer: {t.get('buyer', 'N/A')} | Deadline: {t.get('deadline', 'N/A')}  ")
                lines.append(f"")
        
        # Low Priority
        low = [t for t in self.tenders if t.get("confidence") == "LOW"][:3]
        if low:
            lines.append(f"## Low Priority ({len(low)} opportunities)")
            lines.append(f"")
            for i, t in enumerate(low, 1):
                lines.append(f"{i}. **{t.get('title', 'Untitled')[:60]}**  ")
                lines.append(f"   Score: {t.get('score', 0)} | Buyer: {t.get('buyer', 'N/A')}  ")
                lines.append(f"")
        
        # Data Limitations
        lines.append(f"## Data Limitations")
        lines.append(f"")
        lines.append(f"- TED data does not include eligibility requirements")
        lines.append(f"- Detailed tender specifications require opening original documents")
        lines.append(f"- Below-threshold tenders (MEPA) are not included")
        lines.append(f"- Award history requires ANAC data enrichment")
        lines.append(f"")
        
        # Recommended Actions
        lines.append(f"## Recommended Next Actions")
        lines.append(f"")
        if high:
            lines.append(f"1. **Review top {min(3, len(high))} opportunities** — verify eligibility")
            lines.append(f"2. **Download tender documents** — from source links above")
            lines.append(f"3. **Prepare documentation** — before deadline")
        else:
            lines.append(f"1. **Expand search criteria** — consider additional CPV codes")
            lines.append(f"2. **Check MEPA** — for below-threshold opportunities")
        lines.append(f"")
        
        # Footer
        lines.append(f"---")
        lines.append(f"")
        lines.append(f"*Report generated by AppaltiMonitor using TED (Tenders Electronic Daily) data.*  ")
        lines.append(f"*This is an automated analysis. Always verify information with official sources.*")
        
        return "\n".join(lines)
    
    def generate_html(self):
        """Generate HTML report"""
        md = self.generate_markdown()
        html = self._md_to_html(md)
        return html
    
    def _md_to_html(self, md):
        """Basic Markdown to HTML conversion"""
        lines = md.split("\n")
        html_lines = []
        in_table = False
        
        for line in lines:
            # Headers
            if line.startswith("# "):
                html_lines.append(f"<h1>{line[2:]}</h1>")
            elif line.startswith("## "):
                html_lines.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith("### "):
                html_lines.append(f"<h3>{line[4:]}</h3>")
            # Table
            elif line.startswith("|"):
                cells = [c.strip() for c in line.split("|")[1:-1]]
                if all(set(c) <= set("-: ") for c in cells):
                    continue  # skip separator
                if not in_table:
                    html_lines.append("<table><thead><tr>")
                    for c in cells:
                        c = c.replace("**", "<strong>", 1)
                        while "**" in c:
                            c = c.replace("**", "</strong>", 1) if "<strong>" in c else c.replace("**", "<strong>", 1)
                        html_lines.append(f"<th>{c}</th>")
                    html_lines.append("</tr></thead><tbody>")
                    in_table = True
                else:
                    html_lines.append("<tr>")
                    for c in cells:
                        c = c.replace("**", "<strong>", 1)
                        while "**" in c:
                            c = c.replace("**", "</strong>", 1) if "<strong>" in c else c.replace("**", "<strong>", 1)
                        html_lines.append(f"<td>{c}</td>")
                    html_lines.append("</tr>")
            else:
                if in_table:
                    html_lines.append("</tbody></table>")
                    in_table = False
                # Bold
                line = line.replace("**", "<strong>", 1)
                while "**" in line:
                    line = line.replace("**", "</strong>", 1) if "<strong>" in line else line.replace("**", "<strong>", 1)
                # Links
                line = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', line)
                if line.strip():
                    html_lines.append(f"<p>{line}</p>")
        
        if in_table:
            html_lines.append("</tbody></table>")
        
        html_template = '<!DOCTYPE html>\n<html>\n<head>\n<meta charset="utf-8">\n'
        html_template += '<title>Procurement Intelligence Report</title>\n'
        html_template += '<style>\n'
        html_template += 'body { font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }\n'
        html_template += 'h1 { color: #1a5276; }\nh2 { color: #2874a6; }\nh3 { color: #3498db; }\n'
        html_template += 'table { border-collapse: collapse; width: 100%; margin: 15px 0; }\n'
        html_template += 'th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }\n'
        html_template += 'th { background-color: #f2f2f2; }\n</style>\n</head>\n<body>\n'
        html_template += ''.join(html_lines)
        html_template += '</body>\n</html>'
        
        return html_template
    
    def save(self, format="both"):
        """Save report in specified format(s)"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        profile_id = self.profile.get("id", "unknown")
        
        paths = {}
        
        if format in ("markdown", "both"):
            md_path = REPORTS_DIR / f"report_{profile_id}_{timestamp}.md"
            with open(md_path, "w") as f:
                f.write(self.generate_markdown())
            paths["markdown"] = str(md_path)
        
        if format in ("html", "both"):
            html_path = REPORTS_DIR / f"report_{profile_id}_{timestamp}.html"
            with open(html_path, "w") as f:
                f.write(self.generate_html())
            paths["html"] = str(html_path)
        
        return paths


class PipelineOrchestrator:
    """Orchestrate the full pipeline"""
    
    def __init__(self):
        self.ted_client = TEDAPIClient()
        self.profile_engine = ProfileEngine()
        self.quality_control = QualityControl()
    
    def run(self, profile_id, date_from=None, date_to=None):
        """Run the full pipeline for a profile"""
        start_time = datetime.now()
        
        # Load profile
        profile = self.profile_engine.load_profile(profile_id)
        if not profile:
            return {"error": f"Profile not found: {profile_id}"}
        
        print(f"Running pipeline for: {profile.get('company_name', profile_id)}")
        
        # Build query
        query = self.ted_client.build_query(profile, date_from, date_to)
        print(f"Query: {query}")
        
        # Call TED API
        fields = self.ted_client.get_default_fields()
        result = self.ted_client.search(query, fields, page=1, limit=100)
        
        if result.get("error"):
            print(f"API Error: {result.get('message', 'Unknown')}")
            return {"error": result}
        
        # Parse notices
        notices = result.get("notices", [])
        total_count = result.get("totalNoticeCount", 0)
        print(f"Total notices: {total_count}, Retrieved: {len(notices)}")
        
        # Parse and normalize
        tenders = []
        for notice in notices:
            tender = self._parse_notice(notice)
            tenders.append(tender)
        
        # Deduplicate
        tenders = self._deduplicate(tenders)
        
        # Quality control
        for t in tenders:
            qc = self.quality_control.validate(t)
            t["quality"] = qc["quality"]
            t["quality_issues"] = qc["issues"]
            t["quality_warnings"] = qc["warnings"]
        
        # Score relevance
        relevance_engine = RelevanceEngine(profile)
        for t in tenders:
            scoring = relevance_engine.score_tender(t)
            t["score"] = scoring["total"]
            t["score_breakdown"] = scoring["breakdown"]
            t["match_reasons"] = scoring["reasons"]
            t["confidence"] = scoring["confidence"]
        
        # Sort by score
        tenders.sort(key=lambda x: x["score"], reverse=True)
        
        # Calculate KPIs
        processing_time = (datetime.now() - start_time).total_seconds()
        kpis = self._calculate_kpis(tenders, total_count, processing_time)
        
        # Generate report
        report_gen = ReportGenerator(profile, tenders, kpis)
        report_paths = report_gen.save(format="both")
        
        # Save tenders data
        data_path = OUTPUT_DIR / f"tenders_{profile_id}_{datetime.now().strftime('%Y%m%d')}.json"
        with open(data_path, "w") as f:
            json.dump(tenders[:50], f, indent=2, default=str)
        
        # Save KPIs
        kpi_path = KPIS_DIR / f"kpis_{profile_id}_{datetime.now().strftime('%Y%m%d')}.json"
        with open(kpi_path, "w") as f:
            json.dump(kpis, f, indent=2)
        
        # Status report
        status = {
            "profile_id": profile_id,
            "profile_name": profile.get("company_name"),
            "timestamp": datetime.now().isoformat(),
            "total_retrieved": total_count,
            "relevant": len(tenders),
            "high_priority": kpis["high_priority"],
            "medium_priority": kpis["medium_priority"],
            "low_priority": kpis["low_priority"],
            "processing_time": processing_time,
            "reports": report_paths,
            "data_path": str(data_path),
            "kpi_path": str(kpi_path)
        }
        
        print(f"Pipeline complete. Reports: {report_paths}")
        return status
    
    def _extract_str(self, field):
        """Extract string from TED field (handles list, dict, string)"""
        if not field:
            return ""
        if isinstance(field, list):
            # Filter out empty strings
            cleaned = [f.strip() for f in field if f and isinstance(f, str)]
            return cleaned[0] if cleaned else ""
        if isinstance(field, dict):
            # Multilingual field - try Italian first, then English, then any
            for lang in ["ita", "eng", "fra", "deu"]:
                if lang in field:
                    val = field[lang]
                    if isinstance(val, list):
                        cleaned = [v.strip() for v in val if v and isinstance(v, str)]
                        return cleaned[0] if cleaned else ""
                    elif isinstance(val, str):
                        return val.strip()
            # Return first available
            for val in field.values():
                if isinstance(val, list):
                    cleaned = [v.strip() for v in val if v and isinstance(v, str)]
                    return cleaned[0] if cleaned else ""
                elif isinstance(val, str):
                    return val.strip()
        return str(field)
    
    def _extract_buyer(self, field):
        """Extract buyer name (handles multilingual)"""
        return self._extract_str(field)
    
    def _extract_cpv_list(self, field):
        """Extract ALL CPV codes from TED field (handles list, dict, string)"""
        cpvs = []
        if not field:
            return cpvs
        if isinstance(field, list):
            for item in field:
                if isinstance(item, str):
                    cleaned = item.strip().replace(" ", "")
                    if cleaned and len(cleaned) == 8 and cleaned.isdigit():
                        if cleaned not in cpvs:  # Remove duplicates
                            cpvs.append(cleaned)
                    elif cleaned:
                        if cleaned not in cpvs:
                            cpvs.append(cleaned)
                elif isinstance(item, list):
                    for sub in item:
                        if isinstance(sub, str):
                            cleaned = sub.strip().replace(" ", "")
                            if cleaned:
                                if cleaned not in cpvs:
                                    cpvs.append(cleaned)
        elif isinstance(field, dict):
            for lang in ["ita", "eng", "fra", "deu"]:
                if lang in field:
                    val = field[lang]
                    if isinstance(val, list):
                        for item in val:
                            if isinstance(item, str):
                                cleaned = item.strip().replace(" ", "")
                                if cleaned:
                                    if cleaned not in cpvs:
                                        cpvs.append(cleaned)
                    elif isinstance(val, str):
                        cleaned = val.strip().replace(" ", "")
                        if cleaned:
                            if cleaned not in cpvs:
                                cpvs.append(cleaned)
                    break
        elif isinstance(field, str):
            cleaned = field.strip().replace(" ", "")
            if cleaned:
                cpvs.append(cleaned)
        return cpvs
    
    def _extract_cpv(self, field):
        """Extract first CPV code (for backward compatibility)"""
        cpvs = self._extract_cpv_list(field)
        return cpvs[0] if cpvs else ""
    
    def _extract_date(self, field):
        """Extract date string"""
        if not field:
            return ""
        if isinstance(field, list):
            field = field[0] if field else ""
        if isinstance(field, str):
            return field[:10]
        return ""
    
    def _extract_float(self, field):
        """Extract float value"""
        if not field:
            return None
        if isinstance(field, list):
            field = field[0] if field else None
        if field is None:
            return None
        try:
            return float(str(field).replace(",", "").replace(" ", ""))
        except:
            return None
    
    def _parse_notice(self, notice):
        """Parse TED notice into normalized schema"""
        # TED API returns fields directly in the notice object
        f = notice
        
        # Extract fields
        notice_id = self._extract_str(f.get("notice-identifier"))
        title = self._extract_str(f.get("notice-title"))
        buyer = self._extract_buyer(f.get("buyer-name"))
        country = self._extract_str(f.get("organisation-country-buyer"))
        place = self._extract_str(f.get("place-of-performance"))
        cpv_list = self._extract_cpv_list(f.get("classification-cpv"))
        cpv = cpv_list[0] if cpv_list else ""
        pub_date = self._extract_date(f.get("publication-date"))
        deadline_str = self._extract_date(f.get("deadline-receipt-tender-date-lot"))
        value_num = self._extract_float(f.get("estimated-value-cur-lot"))
        proc_type = self._extract_str(f.get("form-type"))
        
        # Parse deadline
        deadline_date = None
        is_active = False
        if deadline_str:
            try:
                deadline_date = datetime.strptime(deadline_str, "%Y-%m-%d")
                is_active = deadline_date >= datetime.now()
            except:
                pass
        
        # Source URL
        source_url = f"https://ted.europa.eu/en/notice/{notice_id}" if notice_id else ""
        
        return {
            "notice_id": notice_id,
            "title": title[:200],
            "buyer": buyer[:100],
            "country": country,
            "place_performance": place[:100],
            "cpv": cpv[:20],
            "cpv_list": cpv_list[:10],
            "publication_date": pub_date[:10],
            "deadline": deadline_str[:10] if deadline_str else "",
            "is_active": is_active,
            "estimated_value": value_num,
            "procedure_type": proc_type,
            "source_url": source_url
        }
    
    def _deduplicate(self, tenders):
        """Remove duplicate tenders by notice_id"""
        seen = set()
        unique = []
        for t in tenders:
            nid = t.get("notice_id", "")
            if nid and nid not in seen:
                seen.add(nid)
                unique.append(t)
        return unique
    
    def _calculate_kpis(self, tenders, total_retrieved, processing_time):
        """Calculate KPI metrics"""
        high = len([t for t in tenders if t.get("confidence") == "HIGH"])
        medium = len([t for t in tenders if t.get("confidence") == "MEDIUM"])
        low = len([t for t in tenders if t.get("confidence") == "LOW"])
        with_deadline = len([t for t in tenders if t.get("deadline")])
        with_value = len([t for t in tenders if t.get("estimated_value") is not None])
        
        total = len(tenders) if tenders else 1
        
        return {
            "total_retrieved": total_retrieved,
            "relevant": len(tenders),
            "high_priority": high,
            "medium_priority": medium,
            "low_priority": low,
            "with_deadline": with_deadline,
            "with_deadline_pct": (with_deadline / total) * 100,
            "with_value": with_value,
            "with_value_pct": (with_value / total) * 100,
            "processing_time": processing_time,
            "timestamp": datetime.now().isoformat()
        }


def create_test_profiles():
    """Create three realistic test profiles."""
    engine = ProfileEngine()
    
    profiles = [
        {
            "id": "sme_it_services",
            "company_name": "TechSolutions SRL (Hypothetical)",
            "industry": "IT Services",
            "cpv_codes": ["72", "48"],
            "cpv_detailed": ["72210000", "72220000", "72260000", "72510000", "48983000", "48730000"],
            "countries": ["ITA"],
            "value_min": 30000,
            "value_max": 500000,
            "excluded_categories": [],
            "keywords": ["software", "informatica", "cloud", "cybersecurity", "sviluppo", "integrazione", "digitale"],
            "excluded_keywords": ["farmaci", "medicinali", "costruzioni"],
            "preferred_buyers": ["ASST", "AZIENDA", "COMUNE", "REGIONE", "MINISTERO"],
            "notes": "Hypothetical IT services SME for testing"
        },
        {
            "id": "sme_construction",
            "company_name": "EdilPro SRL (Hypothetical)",
            "industry": "Construction",
            "cpv_codes": ["45"],
            "cpv_detailed": ["45234115", "45221211", "45233000", "45262522", "45233220"],
            "countries": ["ITA"],
            "value_min": 50000,
            "value_max": 2000000,
            "excluded_categories": [],
            "keywords": ["costruzioni", "edilizia", "manutenzione", "ristrutturazione", "opere", "lavori"],
            "excluded_keywords": ["software", "informatica", "medicinali"],
            "preferred_buyers": ["COMUNE", "REGIONE", "ANAS", "FERROVIE"],
            "notes": "Hypothetical construction SME for testing"
        },
        {
            "id": "sme_cleaning",
            "company_name": "PulizieVerde SRL (Hypothetical)",
            "industry": "Cleaning & Facility",
            "cpv_codes": ["90", "99"],
            "cpv_detailed": ["90511300", "90480000", "90511100", "90511000"],
            "countries": ["ITA"],
            "value_min": 10000,
            "value_max": 200000,
            "excluded_categories": [],
            "keywords": ["pulizie", "manutenzione", "igiene", "sanificazione", "facility", "rifiuti"],
            "excluded_keywords": ["software", "informatica", "costruzioni"],
            "preferred_buyers": ["COMUNE", "ASST", "OSPEDALE"],
            "notes": "Hypothetical cleaning/facility SME for testing"
        }
    ]
    
    created = []
    for p in profiles:
        profile = engine.create_profile(p)
        created.append(profile)
        print(f"Created profile: {profile['id']}")
    
    return created


if __name__ == "__main__":
    print("=" * 60)
    print("AppaltiMonitor — TED Concierge MVP")
    print("=" * 60)
    
    # Create test profiles
    print("\nCreating test profiles...")
    profiles = create_test_profiles()
    
    # Run pipeline for each profile
    orchestrator = PipelineOrchestrator()
    
    results = []
    for profile in profiles:
        print(f"\n{'='*60}")
        print(f"Running pipeline for: {profile['company_name']}")
        print(f"{'='*60}")
        
        status = orchestrator.run(profile["id"])
        results.append(status)
        
        if status.get("error"):
            print(f"ERROR: {status['error']}")
        else:
            print(f"High priority: {status['high_priority']}")
            print(f"Medium priority: {status['medium_priority']}")
            print(f"Low priority: {status['low_priority']}")
            print(f"Processing time: {status['processing_time']:.1f}s")
    
    # Save overall results
    summary_path = OUTPUT_DIR / f"pipeline_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n{'='*60}")
    print(f"ALL PIPELINES COMPLETE")
    print(f"Summary: {summary_path}")
