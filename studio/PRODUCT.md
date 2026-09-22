# EduCore Enterprise RAG - Product Context (PRODUCT.md)

## Product Vision
EduCore Enterprise RAG is an access-controlled, multi-tenant retrieval-augmented generation and institutional operations platform designed for educational networks (Sentinel Kabitaka and Trident Solwezi campuses). It enforces strict zero-trust Role-Based Access Control (RBAC) compliant with **ISO/IEC 42001 (AI Management System)**, **ISO 27001**, and the **NIST AI Risk Management Framework (AI RMF)**.

## Core Personas & Access Boundaries
1. **Academic Intern (`m.banda` | Clearance: `PUBLIC`)**:
   - Scope: Public academic syllabi (Cambridge IGCSE Mathematics 0580) and general pedagogical assistance.
   - Guardrails: Strictly barred from faculty operational policies, student submissions, counseling records, and financial ledgers.
   - Dedicated Tools: AI Assistant Chat, Curriculum Explorer, Lesson Plan Generator.

2. **Senior Faculty (`m.mwale` | Clearance: `STAFF`)**:
   - Scope: Curriculum, internal faculty operational handbooks, student assignment submissions.
   - Guardrails: Strictly barred from pastoral safeguarding records and campus financial ledgers.
   - Dedicated Tools: AI Assistant Chat (with multi-turn memory), Curriculum Explorer, Faculty Policy Hub, Adversarial Submission Reviewer.

3. **Pastoral Counselor (`c.zulu` | Clearance: `COUNSELOR`)**:
   - Scope: Highly sensitive student welfare, pastoral safeguarding cases (e.g. Case #402), staff policies.
   - Guardrails: Barred from campus financial ledgers and executive budgets. Egress PII masking enforced.
   - Dedicated Tools: Confidential Pastoral RAG Chat, Safeguarding Dossier Viewer, Welfare Accommodation Planner, Live PII De-Identification Lab.

4. **Campus Head / Executive Admin (`d.phiri` | Clearance: `ADMIN`)**:
   - Scope: Executive institutional governance, multi-campus financial ledgers, system-wide telemetry, regulatory auditing.
   - Dedicated Tools: Executive AI Chat, Executive Financial Ledger, RBAC Corpus & ACL Matrix, PII De-ID Lab, ISO 42001 Immutable Audit Ledger, RAG Evaluation Studio (NIST Benchmark).

## Key User Journey & Interactions
- **Zero-Friction Authentication**: Single-click demo profile switcher with immediate role elevation, plus secure credential entry.
- **Continuous Multi-Turn AI Collaboration**: Natural conversational dialogue with pronoun resolution and contextual retrieval expansion, without losing access control guarantees.
- **Transparent Telemetry**: Instant feedback on response latency, retrieved document chunk provenance, and real-time RBAC policy decisions (`PERMITTED`, `CONVERSATIONAL`, `RESTRICTED`).
- **Role-Specific Tool Workspaces**: Purpose-built operational workflows that make each persona's daily workflow seamless and productive.
