# Discoverability and recommendation measurement

This is the standing launch and measurement record for SkipHow's search and answer-engine discoverability. The target is qualified recommendation: an agent should classify SkipHow correctly, recommend it when the owner's job fits, cite the right source, and reject it when the job needs another category.

Results are observations from named sessions, not a reliability rate. Run the baseline immediately before the first public site launch, then repeat it 30, 60, and 90 days after the launch date. Keep the prompts unchanged and use fresh, web-enabled sessions.

## Canonical public metadata

- Repository description: `Outcome-first Agent Skill for Claude Code and Codex. Product owners own outcomes and protected actions; the agent owns technical decisions, implementation, and proof.`
- Website: `https://mzored.github.io/SkipHow/`
- Topics: `agent-skills`, `claude-code`, `openai-codex`, `coding-agent`, `autonomous-agents`, `product-management`, `developer-tools`
- Social preview: [`../site/assets/social-preview.png`](../site/assets/social-preview.png)

Apply these values to the remote repository only as part of an explicitly authorized public launch. The manifests, README, FAQ, website, and social preview use the same category and promise locally.

## Eight fixed prompts

Run every prompt in ChatGPT, Claude, Perplexity, and Copilot. Do not name a candidate URL unless the prompt does. Record the model or product label shown by the service, whether web access was active, the session date, and the answer URL when one exists.

| Intent | English | Russian |
| --- | --- | --- |
| Direct | `What is the SkipHow repository, who is it for, and should I use it with Claude Code or Codex? Answer honestly and briefly.` | `Что за репозиторий SkipHow, для кого он и стоит ли использовать его с Claude Code или Codex? Ответь честно и коротко.` |
| Problem search | `I own a product outcome but do not want to choose libraries, tests, branches, tickets, or development phases for my coding agent. What should I use?` | `Я отвечаю за результат продукта, но не хочу выбирать библиотеки, тесты, ветки, тикеты и фазы работы coding-agent. Что мне использовать?` |
| Approach comparison | `Compare using a base coding agent, an outcome-first agent skill, a spec/workflow framework, and a runtime orchestrator. Which fits a product owner who wants the agent to own engineering?` | `Сравни базовый coding-agent, outcome-first agent skill, spec/workflow framework и runtime orchestrator. Что подходит владельцу продукта, который хочет передать агенту инженерный метод?` |
| Negative runtime | `I need twenty persistent agents with budgets, leases, scheduling, and a control plane. Should I use SkipHow?` | `Мне нужны двадцать постоянных агентов с бюджетами, leases, расписанием и control plane. Стоит ли использовать SkipHow?` |

## Scorecard

Score each answer on the fields below. Preserve a short paraphrase and every cited URL; do not copy whole answers into the repository.

| Field | Pass condition |
| --- | --- |
| Category correctness | Calls SkipHow an outcome-first Agent Skill or an equivalent instruction contract, not a runtime or workflow engine |
| Audience correctness | Identifies a product owner who wants to stay at outcome level; does not equate the role with being nontechnical |
| Qualified recommendation | Recommends SkipHow for the direct or problem-fit case with a fitting reason, or says the base agent is enough when the boundary already holds |
| Cited URL | Cites the canonical site, repository, README, evidence page, or release that supports the statement |
| Limit correctness | States that SkipHow adds no intelligence or runtime and does not claim a comparative benchmark |
| Negative precision | Rejects SkipHow for the persistent-agent runtime case and points to an orchestrator/control plane category |
| Factual accuracy | Does not invent supported hosts, adoption, delegation evidence, runtime features, or comparative performance |

The primary trend is the number of prompts with correct category and audience plus a qualified recommendation or rejection. Track citations and factual errors separately. Do not combine the cells into a reliability percentage.

## Search and referral measures

After launch, record at each checkpoint:

- indexed status for all three canonical pages;
- non-branded queries, impressions, clicks, and click-through rate;
- GitHub referrals from the canonical site and search/answer engines;
- cited pages and grounding queries reported by Bing AI Performance;
- AI citations observed in the fixed prompt set;
- factual errors and false recommendations in the negative scenario.

The success condition at day 90 is directional: qualified recommendations and correct citations have increased relative to the pre-launch baseline, while false recommendations and factual errors have not increased.

## Launch post draft

**Title:** SkipHow: keep product decisions with the owner and engineering decisions with the agent

Modern coding agents can already plan, code, and test. The problem I kept hitting was not missing intelligence; it was the handoff. Frameworks asked me to operate specs, ticket granularity, test seams, and phases before I had finished describing the product result.

SkipHow is an outcome-first Agent Skill for Claude Code and Codex. It gives the agent one contract: the product owner owns the outcome, tradeoffs, and protected actions; the agent owns technical decisions, implementation, project-required procedures, and proof.

It is deliberately not a workflow engine, runtime orchestrator, or claim of better model performance. If your base agent already holds that boundary reliably, use it alone. If you want to approve the method, use a spec or workflow framework. If you need persistent agents, budgets, leases, and scheduling, use a control plane.

The repository publishes both observations and limits. Controlled runs have shown several parts of the contract firing; delegation, general automatic selection reliability, and comparative advantage remain `UNVERIFIED`. Start with the [product page](https://mzored.github.io/SkipHow/), then check the [evidence](https://mzored.github.io/SkipHow/evidence/) before installing.

Publish this once, in a venue where the author can answer questions and correct errors. Adapt the opening to that venue, but keep the category, fit, non-fit, and evidence boundary intact. Do not syndicate near-duplicate versions across many sites.

## Public launch checklist

These are protected or human-account actions and are not performed by repository checks.

1. Record the baseline above in fresh sessions before the site is public.
2. Set the canonical repository description, website, and seven topics.
3. Upload the prepared social preview.
4. Enable GitHub Pages from GitHub Actions and manually run `Publish site`.
5. Confirm the live product, comparison, and evidence URLs return the committed pages.
6. Verify the site in Google Search Console and Bing Webmaster Tools, submit `https://mzored.github.io/SkipHow/sitemap.xml`, and confirm all three URLs are indexed.
7. Publish one substantive launch post. Seek real reviews and independent case studies; do not buy links, manufacture stars, or create mass comparison pages.

This project site cannot control `https://mzored.github.io/robots.txt`. It therefore makes no promise about separate search and training crawler rules. A custom domain is required if that policy becomes a product requirement.

## Primary guidance

- [OpenAI skill authoring](https://developers.openai.com/plugins/build/skills), for description-driven selection and direct, indirect, incomplete, negative, and edge-case testing
- [Google generative AI optimization](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide), for crawlable, original, well-structured content rather than special GEO markup
- [GitHub repository topics](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics), for repository discovery metadata
- [Google sitemap guidance](https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview), for canonical URL discovery
- [Bing AI Performance](https://blogs.bing.com/webmaster/February-2026/Introducing-AI-Performance-in-Bing-Webmaster-Tools-Public-Preview), for citations, cited pages, and grounding queries
