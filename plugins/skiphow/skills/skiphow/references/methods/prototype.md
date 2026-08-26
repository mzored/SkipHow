# Disposable prototypes

Use a prototype to answer one named product or technical question that direct inspection cannot settle cheaply.

Write down the question, the smallest artifact that can answer it, the evidence to observe, the time or attempt limit, and the disposal plan. Leave out production hardening, migrations, compatibility layers, broad tests, and abstractions that do not affect the question. Keep it isolated from the release candidate, free of secrets and customer data, and never deployed or connected to production without a separate exact grant.

End with one verdict: adopt, reject, or record what remains unknown. Remove the prototype before delivery. Code that deserves promotion is rewritten or reviewed under normal product, design, testing, security, and compatibility rules; the experimental artifact never ships unchanged.
