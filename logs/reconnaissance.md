> In this repository, create `logs/reconnaissance.md` with my Support Ticket Triage reconnaissance notes. Record the actual behavior and assumptions below as observations from the disposable prototype, not as requirements for the final feature. Keep the test result attributed to the reconnaissance prototype; do not describe it as the full assignment test suite. Don’t change any other files.
>
> **Feature description:** Build a Support Ticket Triage feature that assigns each incoming ticket a category, priority, and suggested team, and drafts a first reply for a human to review.
>
> **Prototype observations:** The prototype added `POST /tickets/triage`, request and response models, route registration, and three tests. It accepted subject (default `""`, maximum 200 characters), body (default `""`, maximum 20,000 characters), and optional customer ID. Its response included category, priority, suggested team, draft reply, confidence, human-review flag, and model version (default `"recon-v1"`).
> 
> It used keyword matching on subject and body. Categories and keywords were billing (billing, charge, invoice, refund, payment, credit card, subscription), access (login, password, sign in, access, locked out, unable to log in, account), outage (outage, down, offline, server down, not working, cannot load, error page), and data (data, missing, export, report, sync, lost, duplicate records, records). Highest keyword score won; empty text or no category match became general.
> 
> Priorities were urgent for outage or urgent/down/critical/service unavailable text; high for access or billing, or blocked/cannot/immediately text; medium for data; and low by default. Teams were billing_team, identity_support, platform_operations, data_quality, and support_triage for billing, access, outage, data, and general respectively.
> 
> Empty or unclear tickets were marked for human review. The draft told the customer the issue was classified and routed, and that a human would confirm the next step; urgent drafts asked for impact confirmation and a prompt response.
> 
> Duplicate handling and model failure/timeout behavior were not specified by the code or tests. The code was keyword-based in this prototype, not a real model.
> 
> The prototype’s targeted test command reported **3 passed**. The tests checked an outage ticket, a billing ticket, and an empty ticket. These were prototype tests, not the full assignment test suite.
