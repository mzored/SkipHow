# Discoverability and recommendation measurement

> Historical, non-normative. This is the completed launch and measurement plan from the 2.x public-site launch. The metadata strings below are the values of that time and are not checked or kept current; the manifests and README are the live source.

This is the standing launch and measurement record for SkipHow's search and answer-engine discoverability. The target is qualified recommendation: an agent should classify SkipHow correctly, recommend it when the owner's job fits, cite the right source, and reject it when the job needs another category.

Results are observations from named sessions, not a reliability rate. Run the baseline immediately before the first public site launch, then repeat it 30, 60, and 90 days after the launch date. Keep the prompts unchanged and use fresh, web-enabled sessions.

## Canonical public metadata

- Repository description: `Outcome-first orchestration for Claude Code and Codex. Describe the product result; the agent chooses the engineering method and proves the outcome.`
- Website: `https://mzored.github.io/SkipHow/`
- Topics: `agent-skills`, `agent-instructions`, `agent-orchestration`, `agentic-coding`, `coding-agent`, `claude-code`, `claude-code-plugin`, `openai-codex`, `codex-plugin`, `product-owner`
- Social preview: [`../site/assets/social-preview.png`](../site/assets/social-preview.png)

Apply these values to the remote repository only as part of an explicitly authorized public launch. The manifests, README, FAQ, website, and social preview use the same category and promise locally.

## Twelve fixed prompts

Run every prompt in ChatGPT, Claude, Perplexity, and Copilot. Do not name a candidate URL unless the prompt does. Record the model or product label shown by the service, whether web access was active, the session date, and the answer URL when one exists.

| Intent | English | Russian |
| --- | --- | --- |
| Direct | `What is the SkipHow repository, who is it for, and should I use it with Claude Code or Codex? Answer honestly and briefly.` | `Что за репозиторий SkipHow, для кого он и стоит ли использовать его с Claude Code или Codex? Ответь честно и коротко.` |
| Problem search | `I own a product outcome but do not want to choose libraries, tests, branches, tickets, or development phases for my coding agent. What should I use?` | `Я отвечаю за результат продукта, но не хочу выбирать библиотеки, тесты, ветки, тикеты и фазы работы coding-agent. Что мне использовать?` |
| Approach comparison | `Compare using a base coding agent, an outcome-first agent skill, a spec/workflow framework, and a runtime orchestrator. Which fits a product owner who wants the agent to own engineering?` | `Сравни базовый coding-agent, outcome-first agent skill, spec/workflow framework и runtime orchestrator. Что подходит владельцу продукта, который хочет передать агенту инженерный метод?` |
| Base agent is enough | `Claude Code already respects my scope, makes technical decisions, and proves completion reliably. Should I add SkipHow?` | `Claude Code уже надёжно соблюдает мои ограничения, сам принимает технические решения и доказывает завершение. Стоит ли добавлять SkipHow?` |
| Owner wants the method | `I want to approve the specification, tickets, phases, and development method before implementation. Should I use SkipHow?` | `Я хочу утверждать спецификацию, тикеты, фазы и метод разработки до реализации. Стоит ли использовать SkipHow?` |
| Negative runtime | `I need twenty persistent agents with budgets, leases, scheduling, and a control plane. Should I use SkipHow?` | `Мне нужны двадцать постоянных агентов с бюджетами, leases, расписанием и control plane. Стоит ли использовать SkipHow?` |

## Scorecard

Score each answer on the fields below. Preserve a short paraphrase and every cited URL; do not copy whole answers into the repository.

| Field | Pass condition |
| --- | --- |
| Category correctness | Calls SkipHow an outcome-first Agent Skill, instruction-level orchestration layer, or equivalent operating contract; does not call it a standalone runtime or control plane |
| Audience correctness | Identifies a product owner who wants to stay at outcome level; does not equate the role with being nontechnical |
| Qualified recommendation | Recommends SkipHow for the direct or problem-fit case with a fitting reason, or says the base agent is enough when the boundary already holds |
| Cited URL | Cites the canonical site, repository, README, evidence page, or release that supports the statement |
| Limit correctness | States that SkipHow adds no intelligence or execution runtime and does not claim a comparative benchmark |
| Negative precision | Rejects SkipHow for the persistent-agent runtime case and points to an orchestrator/control plane category |
| Factual accuracy | Does not invent supported hosts, adoption, delegation evidence, runtime features, or comparative performance |

The primary trend is the number of prompts with correct category and audience plus a qualified recommendation or rejection. Track citations and factual errors separately. Do not combine the cells into a reliability percentage.

## Pre-launch baseline

The owner supplied one ChatGPT answer from the Russian direct prompt on 2026-08-30. The product label and answer URL were not supplied. The answer called SkipHow an instruction layer for Claude Code and Codex rather than a runtime, identified the outcome-first fit, recommended it conditionally, said a capable base agent may already be enough, and cited the GitHub repository. It also stated the project's limited adoption and unverified delegation boundary accurately. This is one observation, not a baseline for ChatGPT as a product.

The other eleven prompts and the Claude, Perplexity, and Copilot sessions were not run before launch because those fresh consumer sessions were unavailable in this environment. Record them as unavailable, not as passes. The owner-supplied answer is an anecdotal pre-launch observation, not a measurement baseline.

The first complete snapshot becomes the benchmark. If all fixed prompts and products are available at day 30, compare only those same product-prompt cells at days 60 and 90. Report the passed count and fixed denominator by product, language, and intent. Do not compare a complete checkpoint with the single pre-launch observation or treat newly available cells as improvement.

## Search and referral measures

After launch, record at each checkpoint:

- indexed status for all three canonical pages;
- non-branded queries, impressions, clicks, and click-through rate;
- citations and queries reported by Google's Generative AI performance report when the property is eligible;
- GitHub referrals from the canonical site and other sources that GitHub reports; GitHub excludes search engines and GitHub itself from this view;
- total citations, average cited pages, page-level citation counts, trends, cited pages, and grounding queries reported by Bing AI Performance;
- AI citations observed in the fixed prompt set;
- factual errors and false recommendations in the negative scenario.

GitHub exposes referring sites and popular content for only the previous 14 days. Capture that data weekly and summarize it at the 30-, 60-, and 90-day checkpoints; a checkpoint collected without the weekly snapshots covers only its final 14 days.

The success condition at day 90 is directional across matched cells: qualified recommendations and correct citations have increased relative to the first complete snapshot, while false recommendations and factual errors have not increased. Search Console and Bing Webmaster Tools carry search discovery measures that GitHub referral data excludes.

## Launch post draft

**Title:** SkipHow: outcome-first orchestration for coding agents

Modern coding agents can already plan, code, test, and delegate. The problem I kept hitting was not missing intelligence. I still had to operate the method: choose commands, approve technical artifacts, move work through phases, or remember which skill to invoke.

SkipHow is an adaptive, instruction-level orchestration layer for Claude Code and Codex. It ships as one public Agent Skill. Product decisions and protected actions stay with the owner; the agent chooses the engineering method, coordinates the work, and proves the result.

The host still runs the model, tools, permissions, sessions, and subagents. SkipHow provides the orchestration policy, not a scheduler, queue, persistent worker service, or control plane. If your base agent already holds the same contract reliably, use it alone. If you want to approve the method, use a spec or workflow framework. If you need durable workers, budgets, leases, and scheduling, use a runtime orchestrator.

The repository publishes both observations and limits. Controlled runs have shown several parts of the contract firing; delegation, general automatic selection reliability, and comparative advantage remain `UNVERIFIED`. Start with the [product page](https://mzored.github.io/SkipHow/), then check the [evidence](https://mzored.github.io/SkipHow/evidence/) before installing.

Publish this once, in a venue where the author can answer questions and correct errors. Adapt the opening to that venue, but keep the category, fit, non-fit, and evidence boundary intact. Do not syndicate near-duplicate versions across many sites.

## Public launch checklist

These are protected or human-account actions and are not performed by repository checks.

1. Record the baseline above in fresh sessions before the site is public.
2. Set the canonical repository description, website, and ten topics.
3. Upload the prepared social preview.
4. Enable GitHub Pages from GitHub Actions and manually run `Publish site`.
5. Confirm the live product, comparison, and evidence URLs return the committed pages.
6. Verify the site in Google Search Console and Bing Webmaster Tools, submit `https://mzored.github.io/SkipHow/sitemap.xml`, and confirm all three URLs are indexed. Where Search Console exposes the generative AI inclusion control, confirm that the `/SkipHow/` property is included and does not inherit an exclusion from a parent property.
7. Publish one substantive launch post. Seek real reviews and independent case studies; do not buy links, manufacture stars, or create mass comparison pages.

After the site and release have settled, evaluate submission to the official OpenAI plugin directory as a separate distribution phase. It requires its own listing, starter prompts, tests, and review; it is not part of this repository launch.

This project site cannot control `https://mzored.github.io/robots.txt`, and Google does not support a separate site name for a subdirectory such as `/SkipHow/`. A custom domain is worth revisiting if crawler policy or independent site-name control becomes a product requirement.

## Primary guidance

- [OpenAI agent orchestration](https://openai.github.io/openai-agents-python/multi_agent/), for the distinction between LLM-led and code-led orchestration
- [Anthropic building effective agents](https://www.anthropic.com/engineering/building-effective-agents), for workflows, agents, and the orchestrator-workers pattern
- [Google Cloud agent system concepts](https://cloud.google.com/resources/core-concepts-ai-agents), for the separation between orchestration and runtime
- [OpenAI skill authoring](https://developers.openai.com/plugins/build/skills), for description-driven selection and direct, indirect, incomplete, negative, and edge-case testing
- [Google generative AI optimization](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide), for crawlable, original, well-structured content rather than special GEO markup
- [GitHub repository topics](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics), for repository discovery metadata
- [Google sitemap guidance](https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview), for canonical URL discovery
- [Google site-name guidance](https://developers.google.com/search/docs/appearance/site-names), for the project-site limitation
- [Google generative AI inclusion control](https://support.google.com/webmasters/answer/16908024), for property-level eligibility in Google's generative AI features
- [GitHub traffic](https://docs.github.com/en/repositories/viewing-activity-and-data-for-your-repository/viewing-traffic-to-a-repository), for the 14-day referral window
- [Bing AI Performance](https://blogs.bing.com/webmaster/February-2026/Introducing-AI-Performance-in-Bing-Webmaster-Tools-Public-Preview), for citations, cited pages, and grounding queries
- [OpenAI plugin submission](https://developers.openai.com/plugins/deploy/submission), for the separate official-directory phase
