# TaskFinisher AI - Google ADK Agents

This module defines the 8 specialized Google ADK agent roles orchestrated by `TaskFinisherOrchestrator`:

1. **PlannerAgent**: Converts requests into 8 auditable execution steps.
2. **DocumentAgent**: Ingests files with SHA-256 verification via `file_processor`.
3. **ResearchAgent**: Queries multi-source web evidence via `web_search` and `web_scraper`.
4. **VerificationAgent**: Checks evidence against the reliability threshold.
5. **RecoveryAgent**: Automatically retries failed steps using alternate providers/heuristics.
6. **HumanApprovalController**: Pauses execution when human decision is required.
7. **ReportAgent**: Compiles markdown and Word (.docx) report artifacts.
8. **FinalVerifierAgent**: Evaluates completion criteria truthfully (`DONE`, `PARTIALLY_DONE`, `FAILED`).

