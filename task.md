### Historical Data Import Service

Background

The platform is onboarding a company migrating off a legacy vendor. That vendor can export the company's historical parcel records, but the export is messy — some rows are incomplete or wrong, addresses need re-checking, and whoever runs the import needs to actually see what's happening instead of babysitting a spinner. Build the service that handles this.

Users Company staff — back-office users tied to a single company. They only ever deal with their own company's data. Platform admin — can see across all companies. Requirements Submitting an import

Staff can submit a file of historical parcel records for their company. The system accepts it and returns a reference to track it right away — it does not make the caller wait for the whole file to finish processing.

If the same submission is retried (network hiccup, double-click, whatever), it should not silently create two separate imports.

Processing the file

Every record is checked independently against a defined shape — required fields present, values sane for their type. Records that fail are collected as itemized errors; they don't abort the whole import, and they aren't silently dropped either.

Records that pass are then checked against an external address-verification service before being finalized. Treat this as a real network dependency: it has real latency, and it can fail or time out on individual records — that shouldn't take down the rest of the import. (Use a live **API** if you want, or simulate one with realistic delay — the dependency's behavior matters more than which one you pick.)

While this runs, the service tracks running totals — records processed so far, how many succeeded, how many failed.

Watching an import

Staff can list their company's imports, filter by status, and page through results rather than getting a full dump every time.

Staff can pull the full detail and error report for a specific import.

Staff watching an import that's currently running see it update live — processed count, error count — without needing to refresh or re-request the endpoint themselves.

An in-progress import can be cancelled by the staff member who owns it. A finished import cannot be.

Access control

Every endpoint above requires the caller to be logged in — authenticate requests with a bearer token issued at login.

A staff member can never see or act on another company's import, even if they know its exact reference. A platform admin can see across companies, and that shouldn't be handled as a pile of special-case checks scattered through the codebase — it should fall out of how access is structured.

Non-functional requirements Files can be large enough that processing one is genuinely **CPU**-intensive, and the per-record address check is genuinely latency-bound. Design for both — a solution that only handles one gracefully isn't done. While a large import is actively running, the rest of the **API** stays responsive to ordinary traffic — a login, a quick status check, another company's request. No noticeable degradation. You should be able to show this, not just claim it. The **API** is versioned, returns status codes that actually mean what they say, and its generated documentation matches its real shape — not a generic scaffold. Shared infrastructure (data storage, the current user/company context, configuration) is wired into request handlers rather than built inline inside them, so any piece of it can be swapped or overridden without touching the business logic around it. Configuration (secrets, external service settings, size limits) loads from outside the code, not hardcoded. Out of scope Frontend UI Deployment / infrastructure A full automated test suite Custom middleware or global exception handling Real async database access Definition of Done Staff can submit a messy legacy file, watch it process live, and get a final report of what succeeded and what failed — without any cross-company leakage. A large import is actively processing and the rest of the **API** is still fast, with something to show for it. Every response is predictable, correctly coded, and the docs are accurate. No shared resource is constructed directly inside a route handler. Notes Reasonable time-box: 4–6 days, part-time. Optional, ungraded, if you want more afterward: unified error handling across the **API**, or one test that swaps a dependency instead of faking the setup by hand.