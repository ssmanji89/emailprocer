I need to build EmailBot, an AI-powered email classification and response system. 

CRITICAL: Use the following documentation files as the COMPLETE specification:
- docs/IMPLEMENTATION.md - Contains all code patterns, templates, and technical specs
- docs/INTEGRATIONS.md - Contains M365, CRM, and database setup procedures  
- docs/OPERATIONS.md - Contains monitoring, troubleshooting, and maintenance procedures
- docs/SECURITY.md - Contains security implementation and compliance requirements

DEVELOPMENT PHASES:
1. Core Infrastructure Setup (Docker, Database, Redis)
2. M365 Integration (Authentication, Email Reading, Teams)
3. LLM Service Integration (OpenAI GPT-4 for classification)
4. Email Processing Pipeline (State machine workflow)
5. Confidence-based Routing System
6. Security Implementation (Encryption, Audit, Access Control)
7. Monitoring and Health Checks
8. Testing and Validation

IMPLEMENTATION RULES:
- Follow EXACTLY the code patterns in IMPLEMENTATION.md
- Use the specific configurations in INTEGRATIONS.md
- Implement ALL security measures from SECURITY.md
- Include operational procedures from OPERATIONS.md
- Create working, production-ready code
- Add comprehensive error handling and logging
- Include proper async/await patterns
- Implement rate limiting and retries

Please review the relevant documentation section and implement the specified component with full production readiness.