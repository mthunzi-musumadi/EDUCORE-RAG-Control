# ==============================================================================
# EDUCORE SERVICES - FRAMEWORK CORPUS BUILDER
# Ingests all documents from EDUCORE_AI_FRAMEWORK into structured enterprise corpus
# Tags with Microsoft Purview Sensitivity Labels, Clearance Tiers, Roles, and Campuses
# Compliance: ISO/IEC 42001:2023, Zambian Data Protection Act No. 3 of 2021, EU AI Act
# ==============================================================================
import os
import json
import docx

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMEWORK_DIR = os.path.join(BASE_DIR, "EDUCORE_AI_FRAMEWORK")
OUTPUT_FILE = os.path.join(BASE_DIR, "production_setup", "enterprise_data.json")

def read_docx(path):
    doc = docx.Document(path)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    tables = []
    for t in doc.tables:
        t_data = []
        for row in t.rows:
            t_data.append([c.text.strip().replace("\n", " ") for c in row.cells])
        tables.append(t_data)
    return paragraphs, tables

def build_corpus():
    # Load existing records if any
    existing = []
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)

    # Keep initial non-framework test records
    base_records = [r for r in existing if not r.get("id", "").startswith("EDU-FW-")]

    framework_docs = []

    # 1. Organizational AI Governance Policy
    pol_path = os.path.join(FRAMEWORK_DIR, "01_SPOKES_POLICIES", "educore-organizational-ai-governance-policy-v1.docx")
    if os.path.exists(pol_path):
        paras, tables = read_docx(pol_path)
        
        # Section 1: Authority & Dual-Track Charter
        framework_docs.append({
            "id": "EDU-FW-POL-001",
            "title": "Educore AI Governance Policy: Authority, Scope & Dual-Track Architecture",
            "content": (
                "EDUCORE SERVICES ORGANIZATIONAL AI GOVERNANCE POLICY (EDU-AIMS-POL-v1.0):\n"
                "Applicable network-wide across Central Administration, Educore Teacher Academies, and campuses "
                "(Sentinel Kabitaka, Trident College / Trident Solwezi, Frontier).\n"
                "Dual-Track Governance Architecture:\n"
                "• Track 1: Enterprise Business Operations - Governs Finance, Procurement, IT Infrastructure, HR, Legal, Facilities, "
                "and Operations. Enforces strict zero-leakage data security, financial calculation accuracy, vendor vetting, "
                "PII protection, and statutory compliance under the Zambian Data Protection Act (No. 3 of 2021).\n"
                "• Track 2: Academic & Pedagogical Learning - Governs Teaching Faculty, Curriculum Leads, Academy Instructors, "
                "and Students. Enforces process-based learning, human-in-the-loop verification, Adelaide-style intellectual ownership declarations, "
                "and oral defense evaluations (Viva Voce)."
            ),
            "campus": "all",
            "clearance": "public",
            "category": "governance",
            "classification": "INTERNAL - GOVERNANCE POLICY",
            "purview_label": "Internal - Educational",
            "allowed_roles": ["public", "staff", "counselor", "admin"]
        })

        # Section 2: Tooling Classification Registry (Tiers 1, 2, 3)
        framework_docs.append({
            "id": "EDU-FW-POL-002",
            "title": "Educore AI Tooling Registry: Classification Tiers (Tier 1 Authorized, Tier 2 SSO, Tier 3 Prohibited)",
            "content": (
                "EDUCORE AI SOFTWARE CLASSIFICATION REGISTRY:\n"
                "• Tier 1: Authorized Enterprise AI (M365 Copilot Enterprise, Azure OpenAI Services, Azure AI Search / SharePoint RAG, M365 Copilot Finance). "
                "Fully authorized for work purposes under Enterprise Data Protection agreements with ZERO model retraining on Educore data. "
                "Authenticated via Entra ID SSO with Purview container controls.\n"
                "• Tier 2: Conditionally Permitted SSO (Grammarly Business Enterprise, Canva AI Enterprise, Zoom AI Companion Enterprise). "
                "Permitted EXCLUSIVELY using official Educore M365 SSO logins. Strictly prohibited using personal accounts or for processing unencrypted student PII, health notes, or financial ledgers.\n"
                "• Tier 3: Strictly Prohibited Consumer LLMs (ChatGPT Free/Plus personal accounts, Gemini Free personal accounts, Claude Personal, DeepL Free, Midjourney personal). "
                "STRICTLY BANNED for inputting any Educore work data, financial spreadsheets, payroll records, student PII, HR files, or proprietary code. "
                "Violations constitute a major enterprise security breach."
            ),
            "campus": "all",
            "clearance": "staff",
            "category": "policy",
            "classification": "INTERNAL - IT GOVERNANCE",
            "purview_label": "Internal - Educational",
            "allowed_roles": ["staff", "counselor", "admin"]
        })

        # Departmental Non-Software Guardrails
        guardrails_data = [
            ("Fin-01, Fin-02, Fin-03", "Finance, Accounting & Bursar Guardrails", "finance", "admin", "Confidential - Admin / Finance", ["admin"],
             "FINANCE & BURSAR OPERATIONAL GUARDRAILS:\n"
             "• Permitted: Routine spreadsheet formatting, financial variance analysis, memo summarization using M365 Copilot Finance.\n"
             "• Failure Edge: Model hallucinating formula syntax, rounding errors, skewing student fee arrear ledgers, cash flow forecasts, or subsidy allocations.\n"
             "• Guardrail Fin-01 (Dual-Key Manual Audit): Independent human manual verification required for all AI-assisted financial calculations and balance sheet entries before ledger posting.\n"
             "• Guardrail Fin-02 (PII & Commercial Data Masking): Mandatory depersonalization of all student NRC numbers, names, and First Quantum Minerals (FQM) mining partner subsidy data prior to AI prompt submission.\n"
             "• Guardrail Fin-03 (Hardship Allocation Committee): Financial hardship or bursary decisions cannot rely on AI scoring and require unanimous human committee sign-off."),

            ("Pro-01, Pro-02, Pro-03", "Procurement & Supply Chain AI Guardrails", "procurement", "admin", "Confidential - Admin / Finance", ["admin"],
             "PROCUREMENT & SUPPLY CHAIN GUARDRAILS:\n"
             "• Permitted: Summarizing vendor contracts, drafting RFP templates, market research across educational suppliers.\n"
             "• Failure Edge: Trojan AI SaaS features ingesting enterprise data for retraining, leaking competitive tender pricing.\n"
             "• Guardrail Pro-01 (Pre-Procurement Vendor AI Addendum): Mandatory vendor sign-off certifying zero data retention, zero model retraining, and IP indemnification before software purchase.\n"
             "• Guardrail Pro-02 (Air-Gapped Tender Evaluations): Sealed tender bids, competitive pricing, and supplier proposals must be evaluated on offline, air-gapped spreadsheets.\n"
             "• Guardrail Pro-03 (Legal Counsel Contract Sign-off): Legal Counsel must inspect all AI-assisted procurement contracts for IP liability before execution."),

            ("IT-01, IT-02, IT-03", "IT Infrastructure & Software Development Guardrails", "it_systems", "admin", "Restricted - IT / Systems", ["admin"],
             "IT INFRASTRUCTURE & DEVOPS GUARDRAILS:\n"
             "• Permitted: Boilerplate code generation, shell script debugging, network documentation via GitHub Copilot Enterprise.\n"
             "• Failure Edge: Accidental insertion of database connection strings, API keys, passwords, internal server IPs, or buggy scripts.\n"
             "• Guardrail IT-01 (Pre-Commit Secret Scanning): Automated git pre-commit hooks and local secret-scanning pipelines to block prompts containing API keys or credentials.\n"
             "• Guardrail IT-02 (Mandatory SAST & Senior Peer Review): All AI-generated scripts require automated security testing and Senior Engineer peer review sign-offs before production release.\n"
             "• Guardrail IT-03 (48-Hour Staging Sandbox Isolation): AI-generated network or system scripts must undergo 48 hours of testing in isolated staging sandboxes before live execution."),

            ("HR-01, HR-02, HR-03", "Human Resources & Personnel Guardrails", "hr", "admin", "Confidential - Admin / Finance", ["admin"],
             "HUMAN RESOURCES & PERSONNEL GUARDRAILS:\n"
             "• Permitted: Drafting job descriptions, anonymizing employee survey responses, structuring staff professional development modules.\n"
             "• Failure Edge: Algorithmic bias in candidate CV screening leading to unfair rejection, employee privacy violations, or statutory liability under Zambian Law.\n"
             "• Guardrail HR-01 (Ban on Automated Candidate Rejection): Absolute prohibition on automated candidate rejection; human HR officers must conduct all shortlisting and performance appraisals.\n"
             "• Guardrail HR-02 (Statutory Zambian DPIA Compliance): Mandatory Data Protection Impact Assessment (DPIA) for all HR data processing systems under Act No. 3 of 2021.\n"
             "• Guardrail HR-03 (Appraisal Observation Evidence Logs): Annual employee appraisals must reflect direct human supervisor observation logs, not AI-summarized feedback."),

            ("Leg-01, Leg-02", "Legal, Compliance & Executive Guardrails", "legal", "admin", "Confidential - Admin / Finance", ["admin"],
             "LEGAL, COMPLIANCE & EXECUTIVE GUARDRAILS:\n"
             "• Permitted: Contract clause extraction, regulatory tracking, formatting executive board briefing materials.\n"
             "• Failure Edge: AI hallucinating false Zambian statutory acts, legal precedents, or court rulings; delegating executive governance decisions to predictive models.\n"
             "• Guardrail Leg-01 (Statutory Legal Verification): Legal Counsel must verify all AI-extracted legal references against official Republic of Zambia statutory books.\n"
             "• Guardrail Leg-02 (Executive Non-Delegable Accountability): Board risk decisions and institutional policies cannot be delegated to AI models under ISO 42001 Clause 5.1."),

            ("Edu-01, Edu-02, Edu-03", "Academic Faculty & Classroom Educator Guardrails", "curriculum", "staff", "Internal - Educational", ["staff", "counselor", "admin"],
             "ACADEMIC FACULTY & EDUCATOR GUARDRAILS:\n"
             "• Permitted: Azure-hosted lesson planning, rubric criteria design, formatting differentiated reading materials.\n"
             "• Failure Edge: AI generating incorrect academic facts in student handouts; automated grading tools mis-scoring summative exams.\n"
             "• Guardrail Edu-01 (Prohibition of Automated Summative Grading): Summative exam scoring and final report card marks must be assigned by human educators.\n"
             "• Guardrail Edu-02 (Human-in-the-Loop Syllabus Verification): Faculty must verify all AI-generated teaching resources against official Cambridge and Zambian syllabi.\n"
             "• Guardrail Edu-03 (Student Depersonalization Rule): Educators must strip all student names, IDs, and pastoral notes before using AI for lesson differentiation."),

            ("Stu-01, Stu-02, Stu-03", "Student & Learner Guardrails (Tier C)", "curriculum", "public", "Public / Educational", ["public", "staff", "counselor", "admin"],
             "STUDENT & LEARNER GUARDRAILS (TIER C):\n"
             "• Permitted: Interactive study guidance via Azure Socratic RAG tutors (Math/Physics) providing step-by-step diagnostic hints without direct answers.\n"
             "• Failure Edge: Cognitive bypass (students generating complete essays or fake prompt logs using AI); using 4G mobile hotspots to bypass campus firewalls.\n"
             "• Guardrail Stu-01 (Process-Based Viva Voce Oral Defenses): Educators conduct unassisted in-class oral defenses and timed synoptic writes to verify genuine student mastery.\n"
             "• Guardrail Stu-02 (Declaration of Intellectual Ownership): Students attach signed Adelaide-model sole-authorship pledges to all major assignments, taking full responsibility for submitted ideas.\n"
             "• Guardrail Stu-03 (Individual Viva Voce for Group Work): Group project submissions require individual oral spot-checks to ensure equal contribution and prevent AI free-riding."),

            ("Fac-01, Fac-02", "Facilities, Physical Security & Safety Guardrails", "facilities", "staff", "Internal - Educational", ["staff", "counselor", "admin"],
             "FACILITIES, PHYSICAL SECURITY & CAMPUS SAFETY GUARDRAILS:\n"
             "• Permitted: Campus maintenance route optimization, energy tracking, containerized IT helpdesk ticket triage.\n"
             "• Failure Edge: Deploying facial recognition or emotion tracking at campus gates; AI bots auto-closing critical physical safety hazard tickets.\n"
             "• Guardrail Fac-01 (EU AI Act Article 5 Emotion/Facial Ban): Strict prohibition on facial recognition or emotion tracking at school gates or workplaces.\n"
             "• Guardrail Fac-02 (Immediate Human Emergency Dispatch): Physical safety, electrical hazard, or security tickets automatically bypass AI triage and dispatch human responders instantly.")
        ]

        for i, (g_code, g_title, cat, clr, purv, roles, content) in enumerate(guardrails_data, 1):
            framework_docs.append({
                "id": f"EDU-FW-GR-{i:03d}",
                "title": f"Educore Guardrail [{g_code}]: {g_title}",
                "content": content,
                "campus": "all",
                "clearance": clr,
                "category": cat,
                "classification": f"INTERNAL - {purv.upper()}",
                "purview_label": purv,
                "allowed_roles": roles
            })

        # Microsoft Purview Sensitivity Labels Container Specification
        framework_docs.append({
            "id": "EDU-FW-PURVIEW-001",
            "title": "Educore Microsoft Purview Data Sensitivity Containers & AI Boundaries",
            "content": (
                "MICROSOFT PURVIEW SENSITIVITY CONTAINERS & AI PROCESSING BOUNDARIES:\n"
                "1. Confidential - Admin / Finance: Financial ledgers, payroll, bursaries, executive board papers, legal contracts, HR personnel records. Restricted exclusively to M365 Copilot Enterprise and Azure AI Search within secure admin tenants.\n"
                "2. Restricted - IT / Systems: Network topologies, API keys, database schemas, security script repositories, server configurations. Restricted to authenticated IT personnel using GitHub Copilot Enterprise with pre-commit secret scanning.\n"
                "3. Internal - Educational: Curriculum plans, assessment rubrics, teaching guides, internal staff announcements, academy modules. Accessible to teaching faculty for lesson design and resource formatting via M365 Copilot.\n"
                "4. Public / Educational: Published syllabi, textbook indices, public school announcements, general educational resources. Approved for read-only access by student-facing Azure Socratic RAG tutors and public web portals."
            ),
            "campus": "all",
            "clearance": "staff",
            "category": "policy",
            "classification": "INTERNAL - DATA CLASSIFICATION",
            "purview_label": "Internal - Educational",
            "allowed_roles": ["staff", "counselor", "admin"]
        })

        # Statutory Red Lines & Incident SLA
        framework_docs.append({
            "id": "EDU-FW-REDLINES-001",
            "title": "Educore Statutory Prohibitions & Incident Reporting SLA",
            "content": (
                "STATUTORY SAFEGUARDS & PROHIBITED RED LINES (EU AI Act Art. 5, Zambian Act No. 3 of 2021, ISO 42001):\n"
                "❌ Emotion Tracking Prohibitions: Strictly banning all AI systems designed to analyze or track student or staff emotional states at campus gates or workplaces.\n"
                "❌ Subliminal Manipulation & Profiling: Prohibiting AI applications that use subliminal techniques to manipulate student behavior or build secret risk profiles.\n"
                "❌ Un-Bounded PII Export: Prohibiting transmission of unencrypted Zambian NRC numbers, health data, or financial records to external public servers.\n"
                "❌ Unassisted High-Risk Decision Making: Prohibiting fully automated AI systems from executing employment termination, candidate rejection, or final student exam scoring.\n\n"
                "INCIDENT REPORTING & GOVERNANCE SLA:\n"
                "• Proposed Central Governance Intake Portal: ai-governance@educoreservices.com / ai-governance@educore.ac.zm\n"
                "• Initial Acknowledgment SLA: Within 24 Hours of submission.\n"
                "• Steering Committee Resolution SLA: Within 5 business days, including full investigation and corrective action logging under ISO 42001 Clause 10.1."
            ),
            "campus": "all",
            "clearance": "public",
            "category": "governance",
            "classification": "PUBLIC - STATUTORY POLICY",
            "purview_label": "Public / Educational",
            "allowed_roles": ["public", "staff", "counselor", "admin"]
        })

    # 2. Master Implementation Handbook (ISO 42001 AIMS & 6-Step AIIA SOP)
    hbk_path = os.path.join(FRAMEWORK_DIR, "00_HUB_MASTER", "educore-ai-framework-implementation-handbook-v1.docx")
    if os.path.exists(hbk_path):
        framework_docs.append({
            "id": "EDU-FW-HBK-001",
            "title": "Educore AI Framework Implementation Handbook: ISO 42001 AIMS & 6-Step AIIA Protocol",
            "content": (
                "EDUCORE AI FRAMEWORK IMPLEMENTATION HANDBOOK (EDU-AIMS-HBK-v1.0):\n"
                "Master governing authority establishing a certifiable Artificial Intelligence Management System (AIMS) "
                "aligned with ISO/IEC 42001:2023, EU AI Act, and Zambian Data Protection Act (No. 3 of 2021).\n"
                "Incorporates all 38 ISO/IEC 42001:2023 Annex A reference controls and mandates the 6-Step AI System Impact Assessment (AIIA):\n"
                "AIIA 6-Step Sequence:\n"
                "1. Trigger Screening: Identify proposed AI use-case, classification tier, and user base.\n"
                "2. Data Provenance & Purview Review: Verify data sources, licensing, and Purview sensitivity container mapping.\n"
                "3. Rights & Harm Mapping: Assess risks of bias, cognitive bypass, student privacy violations, or financial error.\n"
                "4. Safeguard & DLP Stop Conditions: Configure technical guardrails, egress regex, and non-software procedural checks.\n"
                "5. Unanimous Steering Approval: Requires formal sign-off from Academic, IT/Security, and Legal/Operations leads.\n"
                "6. Risk Registration & 12+ Month Purview Event Logging: Register in ISO 42001 AIMS Inventory and retain immutable logs for at least 12 months."
            ),
            "campus": "all",
            "clearance": "staff",
            "category": "governance",
            "classification": "INTERNAL - AIMS HANDBOOK",
            "purview_label": "Internal - Educational",
            "allowed_roles": ["staff", "counselor", "admin"]
        })

    # 3. 180-Day Implementation Action Plan
    plan_path = os.path.join(FRAMEWORK_DIR, "01_SPOKES_POLICIES", "educore-ai-implementation-action-plan-v1.docx")
    if os.path.exists(plan_path):
        framework_docs.append({
            "id": "EDU-FW-PLN-001",
            "title": "Educore 180-Day Implementation Action Plan: Phased ISO 42001 Roadmap",
            "content": (
                "EDUCORE AI 180-DAY IMPLEMENTATION ACTION PLAN (EDU-AIMS-PLN-v1.0):\n"
                "Phased operational roadmap for ISO 42001 certification and enterprise rollout across 5 phases:\n"
                "• Phase 1: Governance Scaffolding & Pre-Rollout Audit (Days 1–30) - Formalize Steering Committee, CASB/DNS discovery, Purview NRC scans, 10-Question Discovery Survey, AIMS Asset Inventory.\n"
                "• Phase 2: Policy Codification & 6-Step AIIA Protocol (Days 31–60) - Publish Governance Policy v1.0, ISO 42001 Statement of Applicability (SoA) across 38 controls, operationalize 6-step AIIA, statutory Zambian DPIA.\n"
                "• Phase 3: Staff Pilots, Literacy Workshops & SLA Intake (Days 61–90) - Tier A Admin pilot (M365 Copilot), Tier B Educator pilot (Azure Lesson Planning), Michigan-style literacy workshops, launch governance portal with 24-hr SLA.\n"
                "• Phase 4: Student Socratic Rollout & Viva Voce Auditing (Days 91–120) - Azure Socratic RAG tutors with diagnostic study hints, Adelaide declaration of intellectual ownership, 4-vector cognitive bypass audits.\n"
                "• Phase 5: ISO 42001 Internal Audit & Certification (Days 121–180) - Comprehensive internal audit, Clause 9.3 Top-Management Review, Stage 1 documentation audit, Stage 2 operational audit and accreditation."
            ),
            "campus": "all",
            "clearance": "admin",
            "category": "governance",
            "classification": "INTERNAL - EXECUTIVE ROADMAP",
            "purview_label": "Confidential - Admin / Finance",
            "allowed_roles": ["admin"]
        })

    # 4. Pre-Rollout Discovery Survey & Audit Methodology
    aud_path = os.path.join(FRAMEWORK_DIR, "02_SPOKES_AUDIT", "educore-pre-rollout-ai-audit-and-discovery-survey-v1.docx")
    if os.path.exists(aud_path):
        framework_docs.append({
            "id": "EDU-FW-AUD-001",
            "title": "Educore Pre-Rollout Audit Strategy: 3-Vector Methodology & 10-Question Survey",
            "content": (
                "PRE-ROLLOUT AI AUDIT STRATEGY & DISCOVERY SURVEY (EDU-AIMS-AUD-v1.0):\n"
                "Establishes Phase 1 discovery framework under ISO 42001 Clause 4.3 & Annex A.4.4:\n"
                "• Vector 1: Technical & Network Traffic Discovery - Firewall, DNS, and CASB traffic analysis for commercial AI endpoints (api.openai.com, chatgpt.com, gemini.google.com); corporate credit card expense audits.\n"
                "• Vector 2: Data Sensitivity & SharePoint Scoping - Automated Microsoft Purview scans across SharePoint Online using Zambian NRC regex matching and financial/pastoral risk keywords.\n"
                "• Vector 3: Departmental Survey & Risk Mapping - 10-Question instrument assessing tool usage, M365 SSO vs personal logins, data sensitivity, SharePoint uploads, hardware access points, student AI observations, and training needs."
            ),
            "campus": "all",
            "clearance": "staff",
            "category": "audit",
            "classification": "INTERNAL - AUDIT INSTRUMENT",
            "purview_label": "Internal - Educational",
            "allowed_roles": ["staff", "counselor", "admin"]
        })

    # 5. Academic Cognitive Bypass Audit Checklist
    chk_path = os.path.join(FRAMEWORK_DIR, "03_SPOKES_AUDIT_TECH", "educore-cognitive-bypass-audit-checklist-v1.docx")
    if os.path.exists(chk_path):
        framework_docs.append({
            "id": "EDU-FW-CHK-001",
            "title": "Educore Academic Cognitive Bypass Audit Checklist: 4-Vector Verification Matrix",
            "content": (
                "ACADEMIC COGNITIVE BYPASS AUDIT CHECKLIST (EDU-AIMS-CHK-v1.0):\n"
                "Internal quality verification matrix ensuring AI supports genuine student learning rather than cognitive bypass:\n"
                "• Vector 1: Artifact Sampling - Comparing submitted coursework against raw student prompt logs and draft histories.\n"
                "• Vector 2: System Guardrails - Auditing Azure Socratic RAG bot logs in Microsoft Purview to verify diagnostic hint enforcement.\n"
                "• Vector 3: Viva Voce Oral Defenses - Conducting 3-minute unassisted oral spot-checks where students explain their submitted reasoning.\n"
                "• Vector 4: Gradebook Variance Benchmarking - Comparing take-home AI-assisted assignment marks against unassisted in-class exam baselines."
            ),
            "campus": "all",
            "clearance": "staff",
            "category": "curriculum",
            "classification": "INTERNAL - ACADEMIC AUDIT",
            "purview_label": "Internal - Educational",
            "allowed_roles": ["staff", "counselor", "admin"]
        })

    total_records = base_records + framework_docs
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(total_records, f, indent=2, ensure_ascii=False)

    print(f"Successfully generated {len(total_records)} total records ({len(framework_docs)} framework documents added).")

if __name__ == "__main__":
    build_corpus()
