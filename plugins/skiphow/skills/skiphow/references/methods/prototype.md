# Disposable prototypes

Use a prototype to answer one named product or technical question when direct inspection cannot settle it cheaply.

Write the question, the smallest artifact that can answer it, the evidence to observe, the time or attempt limit, and the disposal plan. Omit production hardening, migrations, compatibility layers, broad tests, and abstractions that do not affect the question.

Keep the prototype isolated from the release candidate. Do not place secrets or customer data in it. Do not deploy it or connect it to production without a separate exact grant.

End with one verdict: adopt the tested idea, reject it, or record what remains unknown. Remove the prototype before delivery. If any code deserves promotion, rewrite or review it under normal product, design, testing, security, and compatibility rules. Do not ship the experimental artifact unchanged.
