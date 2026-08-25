# SkipHow vNext: финальное техническое задание на системную доработку

**Дата анализа:** 2026-08-25
**База анализа:** SkipHow 0.7.0, архив `SkipHow-external-analysis-2026-08-25.zip`, приложенные `AGENTS.md` и предыдущее внешнее заключение
**Назначение документа:** передать агенту как нормативное задание на переработку проекта
**Статус:** архитектурное заключение и implementation backlog; это не утверждение, что описанный runtime уже существует

---

## 0. Финальный вывод

Текущий SkipHow уже содержит сильную основу: компактный контракт полномочий, корректную mutation boundary, outcome-first delivery, smallest coherent scope, reuse-first, proportional evidence, scoped re-review и обязательное disposition материальных находок.

Но текущий продукт **не является тем автономным инструментом, который требуется Owner**. Версия 0.7.0 является policy/skill plugin для сильного coding-agent host. Она не содержит исполняемого оркестратора, не управляет длительными фоновыми запусками, не восстанавливает их независимо от контекста модели, не выбирает модели по стоимости и цене ошибки, не реализует полный GitHub delivery lifecycle и не имеет live outcome evals.

Правильная целевая архитектура:

> **Тонкое семантическое ядро + необязательный исполняемый control plane для длительной работы + provider adapters + tracker/delivery adapters.**

Не надо превращать SkipHow в ещё одну методологию, «команду из 17 агентов» или библиотеку обязательных skills. В prompt/runtime-контексте должно оставаться мало правил. Надёжность, восстановление, idempotency, бюджеты, GitHub lifecycle, очистка и model routing должны обеспечиваться кодом и проверяемым состоянием, а не дополнительным prose.

Финальная формула продукта:

```text
Owner specifies the outcome.
SkipHow decides the technical path.
Strong models do the reasoning and implementation.
The runtime preserves authority, state, evidence, cost, and recovery.
```

---

## 1. Что фактически проверено в текущей версии

### 1.1. Состояние архива

Архив содержит чистый snapshot ветки `main` с HEAD `c621e8211393e3229c1812d235fc4ebc565b2a72` по собственному `_analysis/README.md` проекта. Git internals в архив не включены.

### 1.2. Тесты

В распакованном архиве прямой `pytest` дал:

```text
74 passed, 2 failed
```

Оба падения связаны не с runtime policy, а с тем, что release checks вызывают Git-команды, а архив не содержит `.git`.

После копирования файлов в временный Git-репозиторий и создания commit:

```text
76 passed
```

Следовательно:

- контрактные и repository-тесты текущей версии проходят в поддерживаемом Git-контексте;
- standalone-архив пока не является полностью поддерживаемым test surface, хотя README архива предлагает запуск checks прямо из него;
- это надо либо исправить, либо честно исключить из обещаний.

`scripts/check.py` в изолированной offline-среде не был полностью независимо подтверждён: при отсутствии уже подготовленного cache он пытается установить pinned dependencies из сети. Прямые тесты с доступными зависимостями прошли.

### 1.3. Фактический runtime context budget

Текущая версия 0.7.0 загружает:

| Route | Words |
|---|---:|
| Router only | 591 |
| Clear/common software change | 1,862 |
| Repair | 2,210 |
| Testing capability | 2,217 |
| Codebase design capability | 2,261 |
| Technical review capability | 2,279 |
| Diagnosis | 2,655 |

Предыдущее заключение называло 2,442 слова для обычного change. Это устаревшая оценка от более ранней версии. Вывод о необходимости lean context остаётся верным, но исходная цифра должна быть исправлена.

### 1.4. Что реально реализовано

Реализованы:

- единый conversational skill;
- intent routing;
- read-only mutation boundary;
- Owner/Product/Technical authority split;
- direct execution для обычной работы;
- instruction-only durable campaign contract;
- локальная конфигурация;
- GitHub Issue/Project helper scripts;
- doctor и package checks;
- deterministic policy/repository tests;
- context-budget ratchet;
- source-only prior art с licenses и commit pins.

Не реализованы:

- исполняемый campaign runner;
- supervisor/background execution;
- provider session orchestration;
- context-window telemetry и automatic handoff;
- model catalog и model routing;
- outcome feedback/calibration для routing;
- batch intake идей, багов и product signals;
- полный Issue → branch/worktree → PR → CI → merge → cleanup lifecycle;
- safe cancellation и crash recovery как код;
- live multi-trial model evals;
- proof того, что текущие инструкции действительно дают заявленное поведение на Codex/Claude.

---

## 2. Проверка логики предыдущего агента

### 2.1. Что в его выводах правильно и должно остаться

Предыдущее заключение правильно разделило:

1. полезные наблюдения из prior art;
2. eval scenarios;
3. инструкции, которые реально должны загружаться модели.

Также правильно:

- SkipHow не должен быть суммой GSD, OpenSpec, Superpowers, BMAD и Matt Pocock skills;
- runtime должен быть outcome-first, а не process-first;
- технические решения нельзя перекладывать на нетехнического Owner;
- generic skill должен появляться только как исправление измеренного failure mode;
- build-vs-reuse является реальным системным invariant;
- subagents нужны для context isolation, независимого исследования и реально параллельной работы, а не для симуляции организации;
- evidence должно соответствовать утверждению, а не обязательной методологии;
- review должен сходиться через delta verification, а не перезапускать lifecycle;
- `UNVERIFIED` является допустимым честным результатом;
- tracker должен быть lazy adapter;
- anti-ceremony evals и ablation обязательны.

### 2.2. Где его вывод неполон

Предыдущее заключение оптимизирует прежде всего prompt stack. Это необходимо, но недостаточно для целевого продукта.

Оно не закрывает главные требования Owner:

- «запустить на ночь»;
- пережить context compact или процессный crash;
- продолжить после restart;
- автоматически вести множество GitHub tasks;
- контролировать параллельные worktrees;
- дожидаться CI и корректно merge/cleanup;
- выбирать разные модели по стоимости и цене ошибки;
- хранить независимые найденные дефекты;
- давать статус и принимать pause/resume/cancel;
- завершать Epic, а не только формулировать правильные инструкции модели.

### 2.3. Что в нём надо отменить

Нельзя сохранять как окончательную позицию утверждение, что durable campaign не должен иметь background process, controller или executable runtime. Для обычной задачи это верно. Для реально автономной многосессионной работы — нет.

Нужна не постоянная тяжёлая платформа, а **ленивый transient runner**, который запускается только для durable work и завершается после reconciliation.

Также недостаточно оставить campaign как Markdown/JSON contract. Инструкция «используй leases, checkpoints и idempotency» не создаёт настоящие leases, atomic transitions, process supervision или recovery.

### 2.4. Итоговая корректировка

```text
Previous recommendation:
thin prompt kernel, almost no runtime

Correct final recommendation:
thin prompt kernel
+
small executable runtime only where durability is a real product requirement
```

---

## 3. Целевое позиционирование продукта

### 3.1. Для кого

SkipHow ориентирован на:

- product owner;
- solo founder;
- solo developer;
- небольшую продуктовую команду;
- разработчика, который хочет делегировать execution без управления agent workflow;
- нетехнического пользователя, который понимает желаемый продуктовый результат, но не обязан понимать архитектуру, библиотеки, тестовые стратегии или Git.

### 3.2. Что пользователь должен уметь делать

Пользователь формулирует обычным языком:

```text
«Вот список багов и идей. Разбери, объедини дубли и сохрани корректно».

«Реализуй все готовые P0/P1 задачи. Работай автономно до утра».

«Платёж иногда списывается дважды. Найди причину, исправь и проверь».

«Стоит ли добавлять эту функцию? Исследуй и дай одну рекомендацию».

«Продолжай предыдущую работу».

«Покажи статус».

«Поставь на паузу».
```

Пользователь **не должен** выбирать:

- архитектуру;
- библиотеку;
- схему базы;
- test framework;
- модель конкретного субагента;
- количество субагентов;
- branching strategy;
- способ compaction;
- формат state store;
- retry/backoff implementation.

### 3.3. Основное обещание

SkipHow должен:

1. понять результат;
2. изучить продукт и репозиторий;
3. решить, нужна ли research/reuse проверка;
4. выбрать минимальный законченный scope;
5. выбрать execution shape;
6. подобрать достаточные модели и capabilities;
7. выполнить работу;
8. проверить фактический результат;
9. исправить найденные проблемы;
10. сохранить независимые материальные находки;
11. довести GitHub lifecycle до разрешённого terminal state;
12. убрать только созданные им временные ресурсы;
13. честно сообщить blocked/unverified остаток.

### 3.4. Что продуктом не является

SkipHow не должен становиться:

- SDD framework с обязательным PRD/design/tasks для каждого change;
- role-playing organization;
- универсальным workflow engine;
- новым IDE;
- альтернативой GitHub/Linear/Jira;
- коллекцией сотен всегда загружаемых skills;
- model benchmark leaderboard;
- системой, которая автоматически выполняет необратимые внешние действия без authority;
- системой, которая создаёт Issue, PR, review или campaign для каждой мелочи.

---

## 4. Нормативные принципы vNext

### 4.1. One natural-language interface

Публичный API — обычный язык. Внутренние intents и execution shapes не должны становиться обязательными командами пользователя.

### 4.2. Direct by default

Простая завершённая задача выполняется одним агентом без:

- campaign;
- tracker;
- issue;
- plan document;
- subagent;
- external review;
- persistent state.

### 4.3. Durable only when durability is required

Campaign включается, когда хотя бы одно из следующего является реальной частью проблемы:

- работа должна пережить context reset/session restart;
- есть несколько независимо исполняемых tracked items;
- dependency graph влияет на порядок;
- требуется unattended wait/retry/reconciliation;
- параллельные mutable lanes дают существенную пользу;
- нужно продолжить после process crash;
- пользователь явно просит длительный/background run.

Размер diff, важность, риск или количество файлов сами по себе не выбирают campaign.

### 4.4. Risk changes evidence, not orchestration

Маленький auth fix может быть direct, но иметь сильные security gates. Большая документационная миграция может быть low-risk campaign.

### 4.5. Strong model owns the method

Core задаёт:

- полномочия;
- границы;
- исходный outcome;
- минимальный scope;
- evidence contract;
- finding disposition;
- truthful completion.

Модель выбирает:

- способ исследования;
- архитектуру;
- реализацию;
- debugging method;
- test seams;
- review strategy;
- последовательность локальной работы.

### 4.6. Reuse-first

Перед material custom subsystem модель обязана проверить:

```text
existing project primitive
→ native platform capability
→ official SDK/integration
→ mature maintained solution
→ thin custom integration
→ custom build
```

Это не обязательный отчёт для каждой функции. Это gate только для material build-vs-reuse decision.

### 4.7. No orphan findings, no scope explosion

Каждая материальная находка получает terminal disposition:

```text
RESOLVED
PERSISTED
DUPLICATE
DISMISSED
```

Независимая находка не расширяет текущий scope автоматически.

### 4.8. Evidence invalidates proportionally

Локальный fix reviewer finding инвалидирует только затронутое evidence. Full review повторяется только при материальном изменении архитектуры, product semantics, public contract, blast radius или protected surface.

### 4.9. Verification ceiling

Недоступный необязательный verifier остаётся `UNVERIFIED`. Нельзя строить новый subsystem только для того, чтобы искусственно закрыть необязательную проверку.

### 4.10. Eval-driven rules

Любое новое всегда загружаемое правило должно иметь:

- конкретный повторяющийся failure mode;
- behavioral eval;
- доказанный положительный эффект;
- отсутствие дублирования;
- план удаления, когда правило перестало быть load-bearing.

---

## 5. Целевая архитектура

```text
                         OWNER
                           │
                    ordinary language
                           │
                           ▼
                ┌────────────────────┐
                │  SEMANTIC KERNEL   │
                │ intent / authority │
                │ scope / evidence   │
                └─────────┬──────────┘
                          │
            ┌─────────────┴─────────────┐
            ▼                           ▼
    ┌───────────────┐          ┌──────────────────┐
    │ DIRECT PATH   │          │ DURABLE RUNNER   │
    │ current host  │          │ optional/transient│
    └───────┬───────┘          └────────┬─────────┘
            │                            │
            └────────────┬───────────────┘
                         ▼
              ┌─────────────────────┐
              │ PROVIDER ADAPTERS   │
              │ Codex / Claude / ...│
              └──────────┬──────────┘
                         ▼
              ┌─────────────────────┐
              │ INTEGRATION ADAPTERS│
              │ Git / GitHub / CI   │
              │ local tracker / ... │
              └─────────────────────┘
```

### 5.1. Layer A — Semantic Kernel

Всегда загружается только высокосигнальный контракт:

- Owner authority;
- mutation boundary;
- intent;
- smallest coherent outcome;
- direct vs durable selection;
- reuse-first trigger;
- evidence proportionality;
- finding disposition;
- final intent alignment;
- truthful completion.

Цель первой итерации: снизить common software route с 1,862 примерно до **1,200–1,300 слов или ниже**, не ухудшив outcome evals. Это release target, а не вечная догма. Дальнейшее сокращение проводится только по ablation.

### 5.2. Layer B — Durable Runner

Runner существует только для campaign/background work. Он отвечает не за инженерный метод, а за:

- durable run/task state;
- scheduling ready tasks;
- provider sessions;
- context checkpoints;
- attempt IDs и leases;
- retry/circuit breaking;
- budgets;
- pause/resume/cancel;
- process crash recovery;
- Git/worktree ownership;
- external wait reconciliation;
- final cleanup;
- audit trail.

Runner не должен быть обязательным для обычного plugin use.

### 5.3. Layer C — Provider Adapters

Core не знает названий моделей, CLI flags или provider-specific session formats.

Минимальный adapter contract:

```text
discover_capabilities()
list_available_models_or_profiles()
start_session(input, cwd, permissions, model_profile)
resume_session(session_id, checkpoint)
fork_session(session_id, checkpoint?)
send_turn(session_id, input)
stream_events(session_id)
interrupt(session_id)
compact(session_id)
usage(session_id)
cleanup(session_id)
```

Адаптер может использовать официальный SDK/App Server или CLI fallback. Официальный SDK предпочтительнее, если он даёт structured events, session IDs, interruption и usage.

### 5.4. Layer D — Integrations

Adapters реализуют механические протоколы:

- Git;
- GitHub Issues/PR/Checks/Merge Queue;
- локальный tracker;
- CI;
- optional deployment;
- future Linear/Jira/GitLab.

Они не принимают product/architecture решения.

### 5.5. Layer E — Repository Policy

Конкретный проект определяет:

- архитектурные источники истины;
- обязательные checks;
- protected surfaces;
- merge policy;
- release/deploy constraints;
- canonical tracker;
- допустимые external actions.

Core не копирует эти правила.

---

## 6. Публичные intents и UX

Внутренний intent set должен быть расширен без превращения в меню для пользователя.

| Intent | Назначение | Mutation по умолчанию |
|---|---|---|
| `ANSWER` | анализ, research, review, diagnosis-only | нет |
| `INTAKE` | разобрать один или много signals, классифицировать, dedupe, при разрешении сохранить | только при явном сохранении или настроенной campaign-authority |
| `DECIDE` | продуктовая рекомендация | нет, если не попросили сохранить/реализовать |
| `CHANGE` | реализовать ясный outcome | да |
| `REPAIR` | найти и исправить дефект | да |
| `CONTINUE` | продолжить уже разрешённую работу | существующая authority |
| `CONTROL` | status/pause/resume/cancel | только состояние принадлежащего SkipHow run |

`CAPTURE` становится частным простым случаем `INTAKE`, а не отдельной моделью продукта.

### 6.1. Simple path

```text
request
→ inspect
→ resolve routine details
→ implement
→ verify
→ report
```

Никаких persistent artifacts, если они не нужны результату.

### 6.2. Bounded substantial path

```text
request
→ inspect
→ lightweight internal plan when useful
→ bounded implementation
→ affected verification
→ review only if required
→ delta fixes
→ final evidence
```

Это всё ещё direct execution, не campaign.

### 6.3. Campaign path

```text
request / ready backlog
→ immutable outcome
→ durable task graph
→ route + dispatch
→ checkpointed execution
→ verify + integrate
→ wait/retry/recover
→ reconcile findings and GitHub
→ cleanup
→ terminal report
```

### 6.4. User-visible progress

Система не должна молчать длительное время. В interactive mode она даёт редкие полезные updates:

- что сейчас выполняется;
- что завершено;
- что ждёт внешнего события;
- существенное изменение scope/risk;
- возникший Owner decision;
- сколько приблизительно потрачено времени/бюджета, если данные надёжны.

Нельзя транслировать весь внутренний chain of thought или каждый tool call.

---

## 7. Новый first-class workflow: Product Intake

Это один из главных отсутствующих product surfaces.

### 7.1. Вход

Пользователь может прислать:

- хаотичный список идей;
- баги;
- голосовую расшифровку;
- feedback клиентов;
- observations;
- сомнения;
- пожелания;
- несколько противоречащих заметок.

### 7.2. Обработка

```text
raw signals
→ atomize without losing provenance
→ inspect product/repo when decision-relevant
→ classify
→ merge related signals
→ search candidate duplicates
→ distinguish evidence from speculation
→ recommend disposition/priority
→ persist when authorized
```

### 7.3. Типы signal

Минимальная семантика:

- `BUG` — наблюдаемое несовпадение с ожидаемым поведением;
- `IDEA` — возможное улучшение;
- `QUESTION` — продуктовая или техническая неопределённость;
- `RISK` — возможный ущерб, требующий проверки;
- `TECH_DEBT` — конкретная ownership/maintenance проблема;
- `FEEDBACK` — внешний сигнал, ещё не обязательно work item.

Не добавлять обязательную label taxonomy в GitHub. Это внутренние types; adapter использует native Issue Types только когда они доступны и настроены.

### 7.4. Signal ≠ Issue

Raw signal сначала сохраняет:

```text
source
verbatim excerpt
context
observed evidence
confidence
```

Только actionable work становится Issue/Task. Несколько signals могут поддерживать один work item.

### 7.5. Dedupe

Текущий exact normalized title search недостаточен.

Правильная граница:

- adapter возвращает bounded candidate set через GitHub/local search;
- product controller принимает semantic duplicate decision;
- при уверенном duplicate добавляется provenance к существующему item;
- при частичном overlap создаётся related item, а не ложный duplicate.

### 7.6. Приоритизация

Система может рекомендовать:

```text
NOW / NEXT / LATER / DECLINE / INVESTIGATE
```

Но это recommendation, а не изменение portfolio priority без Owner authority.

### 7.7. Минимальный work item

```markdown
## Outcome / problem

## Why it matters

## Acceptance

## Non-goals

## Evidence and provenance

## Relationships / dependencies
```

Не создавать автоматически PRD, architecture design, предполагаемый список файлов или подробный implementation plan.

### 7.8. Epic

Epic создаётся только если есть один связный outcome и несколько независимо deliverable work items с реальными dependencies. «Большой список идей» не является Epic автоматически.

### 7.9. Acceptance criteria для Intake

- принимает минимум 20 смешанных signals за один запрос;
- сохраняет исходную формулировку и источник;
- не теряет отдельные замечания;
- не создаёт Issue на каждую фразу;
- находит материальные дубли;
- не выдаёт speculation за доказанный bug;
- создаёт parent/subissue/dependency relationships, когда host поддерживает их;
- работает с GitHub и локальным fallback;
- не спрашивает технических вопросов;
- выдаёт Owner одну понятную итоговую сводку.

---

## 8. Engineering Controller vNext

### 8.1. Controller должен отвечать на пять вопросов

```text
What outcome is requested?
What is the smallest coherent scope?
Is there unresolved causal/product uncertainty?
Does execution require durable orchestration?
What evidence does the changed surface require?
```

Не материализовать Cartesian state machine из десятков risk/mode combinations.

### 8.2. Direct vs campaign

`EXECUTE` остаётся основным режимом. `CAMPAIGN` — механизм durability, а не «более серьёзная разработка».

### 8.3. Diagnosis

Оставить только load-bearing invariant:

```text
When the cause is materially uncertain, establish it before committing to a repair.
```

Подробный generic debugging skill хранить как remediation/reference, а не обязательный runtime method.

### 8.4. Review

Review запускается при:

- repository requirement;
- high-impact changed surface;
- большой интеграционной неопределённости;
- hard-to-verify behavior;
- consequential architecture change;
- необходимости независимого verdict.

После fixes:

```text
original findings
+ fix delta
→ scoped re-review
```

Не review untouched code заново.

### 8.5. Product acceptance

Один раз после technical convergence и только если изменился Owner-visible product contract, high-impact/regulated flow или repository policy этого требует.

Internal refactor, CI, metadata или validator fix не инвалидирует product acceptance.

### 8.6. Build-vs-reuse receipt

Для material решения сохранить короткую запись:

```text
Decision: ADOPT | INTEGRATE | BUILD | DEFER | SPIKE
Options checked
Material constraint
Why selected
Exit/replacement boundary
Unverified material checks
```

Это не должно появляться для trivial local logic.

---

## 9. Model Routing: модель-независимая архитектура

### 9.1. Что нельзя делать

Не кодировать правила вида:

```text
search = cheap model
code = expensive model
review = strongest model
```

Они полезны как cold-start heuristic, но недостаточны:

- поиск может требовать сложного синтеза;
- код может быть механическим;
- маленький auth fix имеет высокую цену ошибки;
- дорогая модель может быть лишней при сильном deterministic verifier;
- конкретные модели и их relative strengths меняются;
- стоимость delegation/context transfer иногда выше экономии.

### 9.2. Логические profiles

Core знает только:

- `ECONOMY` — дешёвая достаточная capability;
- `BALANCED` — основной implementation profile;
- `FRONTIER` — максимальная доступная reasoning/judgment capability.

Это не конкретные model IDs.

Отдельно задаются required capabilities:

```text
code_edit
long_context
vision
browser
structured_output
subagents
tool_use
computer_use
local_execution
```

### 9.3. Task feature record

```json
{
  "task_kind": "research|implementation|debug|review|integration|intake",
  "mutation": "none|local|remote|protected",
  "uncertainty": "low|medium|high",
  "error_cost": "low|medium|high",
  "reversibility": "easy|bounded|hard",
  "blast_radius": "local|module|system|external",
  "verification_strength": "strong|partial|weak",
  "context_volume": "small|large|unknown",
  "parallelizable": true,
  "required_capabilities": [],
  "latency_priority": "normal",
  "budget_remaining": null
}
```

Эти поля не должны превращаться в пользовательскую форму. Controller формирует их автоматически и сохраняет только для campaign/telemetry.

### 9.4. Model catalog

Provider adapter поддерживает versioned catalog:

```json
{
  "provider": "...",
  "model_id": "...",
  "model_version": "...",
  "profiles": ["BALANCED"],
  "capabilities": [],
  "context_limit": null,
  "pricing": null,
  "latency_class": null,
  "availability": "available|restricted|unknown",
  "deprecated": false
}
```

Model IDs, prices и provider flags находятся в adapter/user config, а не в global `AGENTS.md` или semantic kernel.

### 9.5. Routing rule

```text
eligible = models satisfying hard capability and authority constraints

expected_utility(model) =
    P(verified_success | task, model, repo, recent outcomes) * task_value
  - expected_error_loss
  - expected_model_cost
  - expected_latency_cost
  - delegation_and_context_transfer_overhead
```

Выбирается самый дешёвый eligible model, который проходит safety/quality floor.

### 9.6. Cold-start heuristic

До накопления данных:

| Situation | Profile |
|---|---|
| read-only extraction/inventory, сильный verifier | `ECONOMY` |
| обычная реализация, тесты, bounded debugging | `BALANCED` |
| architecture, campaign decomposition, weak verifier, security, money, public contract, final integration | `FRONTIER` |

Root orchestrator для material campaign использует `FRONTIER` только на decomposition/integration/judgment boundaries. Большая часть read-only exploration может выполняться `ECONOMY`, а обычные writer lanes — `BALANCED`.

### 9.7. Не создавать router call ради router call

Для простой задачи текущая host model выполняет работу напрямую. Отдельная model-routing inference запускается только если ожидаемая экономия превышает:

- startup latency;
- duplicated context;
- serialization cost;
- review/escalation risk.

Controller уже формирует task features; отдельный «router agent» по умолчанию не нужен.

### 9.8. Escalation

Повысить profile при:

- failed verifier;
- повторном no-progress с тем же failure signature;
- неожиданном расширении changed surface;
- material ambiguity;
- high-impact finding;
- недостаточной capability/context;
- reviewer finding, указывающем на системное непонимание;
- внешнем side effect с высокой ценой ошибки.

Не повторять бесконечно на той же модели.

### 9.9. Downgrade

Downgrade разрешён:

- до начала substantive mutation;
- на новой независимой lane;
- для механического follow-up с сильной проверкой.

Не менять модель внутри незавершённой reasoning chain без checkpoint/handoff.

### 9.10. Sticky lane

Одна coherent mutable lane остаётся на выбранном profile, пока нет причины escalation. Это снижает context loss и routing oscillation.

### 9.11. Advisor pattern

Provider-specific возможность «дешёвый executor + сильный advisor» может использоваться как оптимизация. Core не должен требовать её. Когда adapter поддерживает такой режим, advisor вызывается на:

- initial architecture/decomposition;
- material course correction;
- no-progress;
- final integration judgment.

### 9.12. Feedback loop

Для каждого campaign task сохранять:

```text
provider/model/version/profile
route reason
input/output usage when reliable
cost estimate when reliable
latency
verifier result
review findings
retries/promotions
terminal outcome
```

Calibration должна быть version-aware и использовать recency decay. Старые результаты не считаются вечной истиной после обновления модели или harness.

Начать с простой статистики по task taxonomy и repository. Не строить trained router/contextual bandit до накопления достаточного execution-verified dataset.

### 9.13. User-facing cost preference

Пользователь выбирает максимум один понятный режим:

```text
auto (default)
economy
balanced
quality
```

Реальные модели скрыты в advanced local config.

Отдельно один раз настраиваются продуктовые лимиты:

- максимальная стоимость run;
- максимальная длительность;
- разрешённый parallelism;
- merge policy.

Это допустимые Owner decisions. Они не являются техническими вопросами.

### 9.14. Model-routing acceptance

- ни одного model ID в global/kernel files;
- provider adapter может заменить модель без изменения core;
- route decision объясним одной короткой reason string;
- high-impact задачи не уходят ниже configured safety floor;
- verifier failure приводит к bounded escalation;
- route telemetry связывается с фактическим terminal outcome;
- live eval показывает экономию против all-frontier baseline без статистически заметного ухудшения success rate;
- при отсутствии данных система выбирает консервативный profile, а не притворяется уверенной.

---

## 10. Durable Runner

### 10.1. Сначала build-vs-reuse spike

Перед написанием собственного scheduler/retry/state engine провести time-boxed spike минимум по четырём вариантам:

1. bounded local controller + embedded transactional store;
2. Restate или другой maintained single-binary durable runtime;
3. Temporal local/Cloud;
4. provider-native managed sessions/automations без cross-provider controller.

Проверить:

- one-command install;
- macOS/Linux/Windows;
- local repository access;
- no mandatory cloud account;
- crash recovery;
- idempotent external actions;
- pause/resume/cancel;
- durable timers/external waits;
- auditability;
- integration с Codex/Claude adapters;
- packaging size и operational burden;
- license/maintenance;
- safe upgrade/migration.

Предварительный вывод: Temporal является сильной durable platform, но может быть слишком тяжёлым default для solo users; Restate заслуживает реального spike как single-binary вариант; bounded embedded controller может оказаться оптимальным, если domain остаётся узким. Не фиксировать выбор до executable recovery prototype.

### 10.2. Process model

- direct task: никакого runner process;
- campaign: один supervised process на run;
- `--detach`/background возможен;
- process завершается после terminal reconciliation;
- постоянный daemon, server и dashboard не обязательны;
- auto-resume после reboot — P1, если подтверждён спрос.

### 10.3. State ownership

Рекомендуемая модель:

- transactional embedded store для authoritative controller state;
- append-only event log;
- compact JSON snapshot/export для human inspection;
- Git/GitHub/CI остаются authoritative для их собственных состояний;
- provider transcript/session не является единственным источником истины.

Не строить общую event-sourcing framework. Нужен минимальный журнал material transitions.

### 10.4. Run state

```text
NEW
READY
RUNNING
WAITING_EXTERNAL
PAUSED
VERIFYING
COMPLETED
BLOCKED
FAILED
CANCELLED
```

### 10.5. Task state

```text
PROPOSED
READY
CLAIMED
RUNNING
WAITING_EXTERNAL
VERIFYING
DONE
BLOCKED
CIRCUIT_BROKEN
FAILED
CANCELLED
SUPERSEDED
```

Transitions должны быть monotonic и revision-checked. Stale worker не может вернуть terminal task назад.

### 10.6. Минимальный run record

```json
{
  "run_id": "...",
  "schema_version": 1,
  "original_request": "verbatim",
  "authority": {},
  "status": "RUNNING",
  "revision": 0,
  "created_at": "...",
  "updated_at": "...",
  "budget": {},
  "cancel_requested": false,
  "task_graph": [],
  "findings": [],
  "provider_sessions": [],
  "checkpoints": [],
  "integrations": {},
  "next_action": "..."
}
```

### 10.7. Attempt and lease

Каждый mutable task attempt имеет:

- `attempt_id`;
- `idempotency_key`;
- `worker/session_id`;
- owned worktree/paths;
- base/head state identity;
- lease expiry;
- last progress event;
- failure signature;
- exact next action.

### 10.8. Checkpoints

Checkpoint записывается:

- перед spawn/delegation;
- после material mutation;
- после verification;
- перед external wait;
- перед integration/merge;
- перед compaction/handoff;
- при interruption/error;
- перед process exit.

### 10.9. Recovery capsule

Новая/возобновлённая model session получает не полный transcript, а:

```text
immutable outcome
current task and parent goal
applicable constraints
accepted decisions
current Git/worktree state
completed evidence
open findings/blockers
provider/session history identifiers
one exact next action
```

Raw logs остаются доступными по ссылке, но не загружаются автоматически.

### 10.10. Context-window management

Provider adapter сообщает usage/context health, если host даёт надёжные данные.

Core использует semantic states:

```text
HEALTHY
APPROACHING_LIMIT
UNKNOWN
```

Не хранить universal token threshold в core. Threshold/provider event принадлежит adapter.

При `APPROACHING_LIMIT`:

1. остановить новый large subtask;
2. завершить safe boundary;
3. checkpoint;
4. вызвать provider-native compact/resume или создать fresh session;
5. загрузить recovery capsule;
6. продолжить тот же task idempotently.

### 10.11. External wait

CI, rate limit, human action и external service wait представлены явным state. Runner не держит модель активной во время ожидания. Он планирует bounded recheck или завершает affected lane как `WAITING_EXTERNAL`, продолжая независимые tasks.

### 10.12. Cancellation

`pause`:

- прекращает новые dispatch;
- даёт активным операциям дойти до safe boundary;
- сохраняет checkpoint.

`cancel`:

- ставит durable flag;
- interrupt provider sessions;
- прекращает retries;
- сохраняет partial work;
- не удаляет уникальные commits;
- выполняет safe cleanup только system-owned временных ресурсов;
- выдаёт reconciled terminal summary.

### 10.13. Circuit breaker

При повторении одной failure signature без прогресса:

- task → `CIRCUIT_BROKEN`;
- сохранить diagnostics;
- попробовать один material course correction или stronger profile;
- не повторять бесконечно;
- продолжить независимые tasks;
- при исчерпании вариантов — `BLOCKED` с точным action.

### 10.14. Status

Пользовательский status показывает:

```text
Outcome
Completed / active / waiting / blocked
Current task
Last verified progress
Saved findings
Budget/time used
Next action
Owner action, only if required
```

Не показывать внутренние prompts или chain of thought.

---

## 11. Полный GitHub lifecycle

### 11.1. Общие правила

- GitHub необязателен;
- Issue — canonical work identity, когда tracked lifecycle действительно нужен;
- Project — optional view;
- Git branch/PR создаются только для implementation;
- controller принимает решения, GitHub adapter исполняет.

### 11.2. Intake и backlog

Adapter должен уметь:

```text
find_candidates
create_issue
update_issue
link_duplicate
create_subissue_or_parent_relation
create_blocking_dependency
record_provenance
```

Использовать native GitHub relationships, когда доступны. Не дублировать их самодельными labels/Markdown state machines.

### 11.3. Ready queue

Campaign controller формирует ready frontier из:

- issue state;
- native dependencies/subissues;
- repository policy;
- active leases;
- branch/PR/CI state;
- Owner priority.

Project board не читается «на всякий случай» и не является lifecycle authority.

### 11.4. Branch/worktree

Для независимых mutable lanes:

- отдельный system-owned branch;
- отдельный worktree;
- один writer на owned scope;
- branch metadata связывается с run/task/issue;
- user branches и dirty user worktrees не трогать.

Не форсировать worktree для одной последовательной задачи.

### 11.5. PR

PR создаётся для coherent deliverable slice, а не обязательно для каждого raw signal.

PR должен:

- ссылаться на Issue;
- использовать native closing relation (`Closes #N`) только когда PR действительно завершает item;
- описывать outcome, verification и material limits;
- не копировать внутренний transcript;
- не объявлять completion до green required checks.

### 11.6. CI и review

Runner:

- отслеживает required checks;
- классифицирует failure как own change / external / flaky / unavailable;
- исправляет own failures;
- повторяет только invalidated checks;
- не создаёт новый verifier ради optional gap;
- ожидает required human review без блокировки независимых tasks.

### 11.7. Merge policy

User/repository-level setting:

```text
never
when_green
when_green_and_approved
auto_merge_or_queue
```

Default до явной настройки — `never` или repository-defined conservative policy.

Автономный merge разрешён только когда:

- Owner/config предоставил authority;
- branch protections выполнены;
- required checks green;
- required reviews получены;
- нет unresolved blocking finding;
- final delivered-state evidence относится к exact head;
- merge action reversible/authorized в рамках policy.

### 11.8. Cleanup

После подтверждённого merge:

- использовать repository auto-delete branch policy или удалить system-owned remote branch;
- удалить только чистый system-owned worktree;
- удалить local branch только если merged и без unique commits;
- prune stale refs/worktrees;
- остановить owned background processes;
- закрыть leases;
- обновить Issue/Project view;
- сохранить final references.

Никогда:

- не удалять unmerged branch;
- не удалять branch с unique commits;
- не использовать force cleanup без verified ownership;
- не откатывать unrelated user changes.

### 11.9. Idempotency

Повторный run не должен создавать:

- duplicate Issue;
- duplicate branch;
- duplicate PR;
- повторный merge comment;
- повторную remote deletion.

Перед mutation adapter reconciles actual state.

### 11.10. GitHub acceptance

В sandbox repository автоматически пройти сценарий:

```text
signals
→ issues + dependencies
→ ready issue
→ branch/worktree
→ implementation
→ PR
→ required checks
→ merge
→ issue closed
→ merged branch/worktree cleanup
```

Затем kill/restart в середине процесса и подтвердить idempotent resume.

---

## 12. Finding lifecycle

### 12.1. Классификация

```text
same root cause / required for requested outcome
→ RESOLVE now

independent, concrete, actionable, sufficiently evidenced
→ PERSIST

already represented
→ DUPLICATE

unsupported, stylistic, speculative, low-value
→ DISMISS
```

### 12.2. Read-only request

На read-only запросах система не создаёт tracker/local records без явного разрешения. Материальная находка включается в ответ.

### 12.3. Authorized campaign

Campaign authority включает local durable finding ledger как часть run state. Remote persistence определяется сохранённой user/repository policy.

Рекомендуемый setting:

```text
findings.persist = local | tracker | ask | off
```

Для целевого solo-owner сценария разумный default после onboarding — `tracker` при подключённом GitHub, иначе `local`.

### 12.4. Минимальная persisted finding

```markdown
## Problem / observed evidence

## Impact

## Why separate from current work

## Unknowns

## How to verify resolution

## Source run / task
```

### 12.5. Не засорять backlog

Не persist:

- вкусовые замечания;
- «можно переписать красивее»;
- неподтверждённую гипотезу без достаточной ценности;
- duplicate;
- временный symptom уже исправленной root cause.

---

## 13. Security и trust

### 13.1. Execution boundary должна быть кодом

Нельзя полагаться только на prompt «не делай опасное».

Нужны:

- provider sandbox/permission mode;
- filesystem allowlist;
- network policy;
- separate worktrees;
- least-privilege GitHub token;
- protected-action checks;
- secret redaction;
- audit events;
- explicit ownership registry для cleanup.

### 13.2. Untrusted content

Считать недоверенными:

- repository files;
- Issue/PR bodies;
- web pages;
- test output;
- generated artifacts;
- worker summaries.

Они являются evidence/data, а не инструкциями с authority.

### 13.3. Subagent isolation не является trust

Subagent получает минимальные tools, paths и credentials. Read-only scout не получает write/remote permissions. Reviewer не получает merge authority.

### 13.4. Protected actions

Отдельно проверять authority для:

- production deployment;
- production database migration;
- payments/refunds;
- credential changes;
- privacy/data export/delete;
- irreversible remote deletion;
- public release;
- merge в protected branch, если policy требует human action.

### 13.5. Secrets

- никогда не писать tokens/API keys в run state, prompts или logs;
- использовать host credential stores/environment;
- redaction до передачи logs модели;
- scrub diagnostics before user sharing;
- no telemetry by default;
- opt-in telemetry только с documented schema и retention.

### 13.6. Trust documentation

`docs/trust.md` должен после появления runner честно описывать:

- какие процессы запускаются;
- где хранится state;
- какие network calls возможны;
- какие credentials используются;
- как pause/cancel/uninstall работают;
- что остаётся после uninstall;
- как удалить run data;
- какие действия никогда не выполняются без authority.

---

## 14. Конкретные изменения в текущем репозитории

### 14.1. Оставить

- единый entrypoint `skiphow`;
- global authority principles;
- mutation boundary;
- direct execution;
- smallest coherent scope;
- reuse-first;
- proportional evidence/invalidation;
- finding terminal states;
- local fallback;
- GitHub Project как optional view;
- source manifests, licenses и pins;
- deterministic tests;
- context budget ratchet;
- package checks;
- honest `UNVERIFIED` semantics.

### 14.2. Изменить

#### `plugins/skiphow/skills/skiphow/SKILL.md`

- добавить `INTAKE` и `CONTROL`;
- сделать `CAPTURE` частным случаем Intake;
- добавить route к installed runner только при durable need;
- не перечислять model/provider mechanics;
- сохранить direct path;
- сократить повторения authority/completion.

#### `references/engineering/cto/SKILL.md`

- оставить только controller questions и direct/campaign boundary;
- убрать routing к generic method skills по умолчанию;
- route к runtime через semantic capability `durable_execution`, не через prose-only campaign;
- сохранить selective review/product acceptance.

#### `references/engineering/cto/references/technical-policy.md`

- сократить примерно с 971 до 500–700 слов;
- оставить invariants;
- убрать method prescriptions и подробные vocabularies, которые может выбрать модель;
- вынести implementation schemas в runner docs/code.

#### `references/product/idea/SKILL.md`

- заменить на `references/product/intake/SKILL.md`;
- поддержать batch signals, dedupe, provenance, recommendation, persistence;
- сохранить simple single-capture fast path.

#### `references/campaign/cto-run/`

- оставить короткий semantic contract;
- state machine, schemas, leases, retries и recovery реализовать в code;
- убрать ложное впечатление, что Markdown сам является runtime;
- rename возможно на `campaign`/`runner` после migration, не обязательно для первой версии.

#### `references/host-capabilities.md`

Удалить blanket prohibition:

```text
Do not emulate ... by building an App Server client, background daemon, universal controller...
```

Заменить:

```text
Do not build an ad-hoc replacement inside an unrelated task.
Use the installed SkipHow runner and provider adapters when durable execution is required.
If unavailable, bounded work may continue in-session; durable/background claims remain UNVERIFIED.
```

#### `references/trackers/github-task/SKILL.md`

Сохранить его «тупым adapter», но расширить operations:

- semantic candidate search support;
- update/provenance;
- native relationships;
- PR/check/merge/cleanup;
- idempotent reconciliation;
- ownership guards.

Не давать adapter решать scope, priority, review depth или campaign.

#### `docs/architecture.md`

Переписать под dual-plane architecture.

#### `docs/trust.md`

Добавить runner, provider sessions, state, credentials, cancellation, cleanup.

#### `README.md`

До реализации runner честно позиционировать 0.7 как lean policy plugin. После P0 release gate заменить на target README.

#### Root `AGENTS.md`

- deterministic CI остаётся без model calls;
- разрешить отдельный opt-in live eval harness с explicit credentials/budget;
- после product decision разрешить optional bundled runner;
- package proof и behavior proof по-прежнему разделять.

#### Приложенный global `AGENTS.md`

Он в целом уже оптимален. Удалить или сделать capability-neutral строку `You can use subagents`, потому что availability должна обнаруживаться текущим host. Остальное не раздувать.

### 14.3. Переместить из runtime

Generic capabilities:

- `prototype`;
- `testing`;
- `codebase-design`;
- `resolving-merge-conflicts`;
- подробный `diagnose`;
- подробный `technical-review`.

Не удалять upstream sources/licenses. Переместить в:

```text
docs/prior-art/
remediation/
evals/failure-corpus/
```

В runtime возвращать только конкретный компактный remediation skill после доказанного failure mode и ablation.

### 14.4. Добавить

Рекомендуемая логическая структура:

```text
README.md
AGENTS.md

plugins/
  skiphow/
    skills/
      skiphow/

src/ or packages/
  kernel/
  runner/
  routing/
  store/
  cli/
  adapters/
    codex/
    claude/
    git/
    github/
    local/

schemas/
  config.schema.json
  run.schema.json
  task.schema.json
  event.schema.json
  finding.schema.json
  route.schema.json

evals/
  deterministic/
  live/
  scenarios/
  graders/
  fixtures/

docs/
  architecture.md
  trust.md
  operations.md
  model-routing.md
  intake.md
  github-lifecycle.md
  evals.md
  prior-art.md
```

Язык реализации runner не фиксировать в prompt policy. Implementation agent должен сделать короткий spike между Python и TypeScript с учётом:

- текущей Python codebase;
- официальных provider SDK;
- cross-platform packaging;
- one-command install;
- standalone executable;
- maintenance burden.

Acceptance важнее языка.

---

## 15. Configuration

### 15.1. Разделить project-safe и personal config

Project config, commit-safe:

```text
.skiphow/config.json
```

Personal config, не в repo:

```text
~/.config/skiphow/config.json
```

Provider credentials остаются в host/provider stores.

### 15.2. Project config v2

Пример семантики, не окончательный schema:

```json
{
  "schema_version": 2,
  "tracker": {
    "type": "auto",
    "project": null
  },
  "delivery": {
    "merge_policy": "never",
    "cleanup": "merged_only"
  },
  "findings": {
    "persist": "local"
  },
  "campaign_root": ".skiphow/runs"
}
```

### 15.3. Personal config

```json
{
  "execution_preference": "auto",
  "cost_preference": "balanced",
  "max_cost_per_run": null,
  "max_duration": null,
  "max_parallelism": "auto",
  "providers": {}
}
```

Model IDs и provider-specific flags допустимы только здесь или в adapter manifests.

### 15.4. UX

Пользователь не должен редактировать JSON. Настройка происходит conversationally или одной командой setup с понятными product-level choices.

### 15.5. Migration

- читать v1 config;
- предложить/выполнить reversible migration при explicit setup/update;
- сохранить неизвестные будущие поля только если schema это допускает осознанно;
- backup до rewrite;
- не менять config в read-only request.

---

## 16. Evals и release evidence

### 16.1. Исправить текущую крайность

Deterministic CI не должен запускать платные модели. Но полное удаление live model evals оставляет продукт без evidence для главного обещания.

Нужно два контура:

```text
CI / PR:
  deterministic, local, fast, no paid model calls

Nightly / release candidate / manual:
  opt-in live multi-provider outcome evals
  explicit credentials and budget
  machine-readable receipts
```

### 16.2. Что оценивать

Оценивать final environment state и forbidden side effects, а не соблюдение конкретного процесса.

### 16.3. Обязательные scenarios

1. **Simple anti-ceremony** — маленький fix без campaign/issue/subagent.
2. **Nontechnical Owner** — ни одного engineering-choice вопроса.
3. **Reuse-first** — commodity subsystem не переписывается с нуля.
4. **Trivial local logic** — не добавляется лишняя dependency.
5. **Unknown bug** — root cause исследуется до repair.
6. **Batch intake** — mixed signals корректно atomized/deduped/persisted.
7. **No orphan finding** — independent confirmed issue сохраняется, scope не расширяется.
8. **Scoped re-review** — local reviewer fix не перезапускает full lifecycle.
9. **Verification ceiling** — unavailable optional verifier остаётся `UNVERIFIED`.
10. **Long campaign** — kill/restart/context reset и корректный resume.
11. **GitHub lifecycle** — Issue → PR → CI → merge → cleanup.
12. **Idempotent rerun** — нет duplicate external mutations.
13. **Pause/resume/cancel** — safe terminal state.
14. **Prompt injection** — repo/Issue/web content не захватывает authority.
15. **Protected action** — без authority не выполняется.
16. **Model routing** — cheaper models используются там, где success сохраняется.
17. **Escalation** — weak model failure корректно поднимает profile.
18. **Scope restraint** — соседняя идея не включается автоматически.
19. **Context handoff** — original outcome/constraints не теряются после compaction.
20. **Cleanup safety** — user branches/dirty files не удаляются.

### 16.4. Trials

Для nondeterministic behavior использовать несколько trials. Один удачный запуск не является release evidence.

### 16.5. Метрики

Primary:

- terminal task success;
- correctness of final environment;
- unauthorized mutations;
- unresolved blocking findings;
- recovery success;
- cleanup correctness.

Secondary economy:

- tokens;
- estimated/actual cost;
- latency;
- tool calls;
- subagents;
- campaign creation;
- tracker touches;
- documents/artifacts created;
- model promotions;
- duplicate external actions;
- Owner questions.

### 16.6. Ablation

Сравнить на одинаковых real tasks:

```text
0.7 prompt-only stack
vs
vNext thin kernel without runner
vs
vNext kernel + runner + routing
```

Измерить не только correctness, но и overhead.

### 16.7. Rule registry

Для каждого core rule хранить:

```text
rule id
owner file
failure mode
eval scenario
measured effect
last revalidated model/harness versions
```

Правило без failure/eval не добавлять.

### 16.8. Archive test

Добавить отдельный supported scenario:

- либо checks корректно работают без `.git`;
- либо archive README явно говорит, что release checks требуют Git checkout;
- тест подтверждает выбранный контракт.

### 16.9. Offline check

`scripts/check.py` должен:

- использовать prepared cache;
- давать точный `UNVERIFIED/BLOCKED` при отсутствии сети и dependencies;
- не выдавать network bootstrap failure за project test failure;
- иметь documented offline path.

---

## 17. Что взять из prior art

| Project | Взять | Не брать |
|---|---|---|
| GSD | durable context, fresh session for independent work, model resolution as configuration | обязательный Discuss→Plan→Execute→Verify→Ship для каждого change |
| OpenSpec | intent/delta traceability для material long work | proposal/spec/design/tasks directory на каждое изменение |
| Superpowers | failure corpus, worktree/review/finish techniques, scoped re-review | mandatory brainstorming, approval, strict TDD dogma |
| Matt Pocock skills | progressive disclosure, context/cognitive load discipline, remediation references | всегда загружаемую библиотеку generic engineering methods |
| BMAD | right-sized depth, durable epic loop | personas, handoffs, обязательные briefs/specs |
| Paperclip | control-plane/execution-plane separation, budgets, audit, adapter thinking | org chart, budgets/governance UI и always-on server как default |
| Mesa | local-first/single-binary simplicity, embedded durable state | фиксированные шесть ролей и company simulation |
| Autonomous PM | batch signal intake, evidence/provenance, disconfirming evidence | 17-agent topology и formal scoring по умолчанию |
| Restate/Temporal | durable execution, retries, waits, recovery primitives после spike | тяжёлую operational platform без доказанной необходимости |

SkipHow не должен утверждать, что «содержит всё из них». Честное позиционирование:

> Built after using and studying these systems. SkipHow is not a superset; it deliberately keeps only mechanisms that improve measured outcomes for an Owner-driven autonomous delivery workflow.

---

## 18. Implementation backlog

Работу выполнять последовательными coherent slices. Не объединять весь roadmap в один diff.

### P0-A — Product truth и lean kernel

#### A1. Обновить architecture decision

**Deliverable:** dual-plane architecture document.
**Acceptance:** явно разделены plugin kernel, direct path, durable runner, provider adapters и integrations; README claims соответствуют реальности.

#### A2. Исправить host capability contract

**Deliverable:** убрать blanket prohibition на официальный runtime/adapters.
**Acceptance:** ad-hoc subsystem внутри обычной задачи запрещён; installed durable runner разрешён как product capability.

#### A3. Сократить common runtime route

**Deliverable:** kernel/CTO/technical policy refactor.
**Acceptance:** common route ≤1,300 words или documented ablation показывает, почему больше необходимо; behavioral contracts не ухудшены.

#### A4. Перевести generic skills в source/remediation layer

**Deliverable:** runtime больше не читает generic methods по умолчанию; licenses/pins сохранены.
**Acceptance:** context-budget tests и source attribution проходят.

### P0-B — Product Intake

#### B1. Добавить `INTAKE`

**Acceptance:** single и batch capture, classify, dedupe, provenance, recommendation, local/GitHub persistence.

#### B2. Добавить semantic duplicate flow

**Acceptance:** adapter возвращает candidates; controller решает duplicate; exact-title-only ограничение устранено.

#### B3. Добавить Epic/dependency mapping

**Acceptance:** parent/subissue/blocking relations feature-detected; fallback честный.

### P0-C — Runtime build-vs-reuse spike

#### C1. Prototype 3–4 вариантов durable substrate

**Acceptance:** executable crash/resume demo; documented ADOPT/INTEGRATE/BUILD decision; no architecture by preference alone.

#### C2. Выбрать implementation language/package strategy

**Acceptance:** one-command install, cross-platform plan, official provider SDK fit, standalone packaging proof.

### P0-D — Durable Runner MVP

#### D1. Run/task/event schemas

**Acceptance:** schema validation, migration versioning, monotonic transitions.

#### D2. Store и atomic operations

**Acceptance:** simulated process kill не corrupt state; journal/snapshot reconcile.

#### D3. Scheduler/frontier

**Acceptance:** dependencies, leases, ready tasks, bounded parallelism, no duplicate claim.

#### D4. Pause/resume/cancel/circuit breaker

**Acceptance:** automated integration tests.

#### D5. Checkpoint/context handoff

**Acceptance:** fresh session продолжает exact task без потери outcome/constraints.

#### D6. Status и final reconciliation

**Acceptance:** terminal report generated from actual state, not model assertion.

### P0-E — Provider adapters

#### E1. Codex adapter

Использовать официальный App Server/SDK, если capability доступна; CLI fallback только для недоступных SDK features.

**Acceptance:** start/resume/fork/stream/interrupt/compact/usage capability matrix; no hardcoded model in core.

#### E2. Claude adapter

Использовать Agent SDK/structured CLI mode.

**Acceptance:** session resume, streaming, subagent attribution, interrupt, budgets, permission mode, pre/post compact hooks where available.

#### E3. Provider-neutral conformance suite

**Acceptance:** один набор adapter contract tests для обоих providers.

### P0-F — Model routing

#### F1. Semantic profiles и catalog

**Acceptance:** model IDs только в adapters/local config.

#### F2. Heuristic router

**Acceptance:** task features, safety floor, cost/latency/context overhead, explainable route reason.

#### F3. Escalation и sticky lanes

**Acceptance:** verifier failure promotes; no oscillation; checkpoint before switch.

#### F4. Telemetry/calibration store

**Acceptance:** execution-verified outcomes; version/recency aware; no secret/prompt leakage.

### P0-G — GitHub delivery

#### G1. Issue lifecycle expansion

**Acceptance:** create/update/provenance/relationships/idempotency.

#### G2. Branch/worktree ownership

**Acceptance:** concurrent writers isolated; user state preserved.

#### G3. PR/check/review flow

**Acceptance:** required checks and scoped fixes; exact-head evidence.

#### G4. Merge authority

**Acceptance:** configurable policy; no unauthorized merge.

#### G5. Cleanup

**Acceptance:** only merged system-owned branches/worktrees removed; unique commits preserved.

### P0-H — Security

#### H1. Threat model

**Acceptance:** repo/Issue/web prompt injection, credentials, protected actions, cleanup, supply-chain risk covered.

#### H2. Sandbox/permission adapter policy

**Acceptance:** read-only/writer/reviewer profiles enforce different permissions.

#### H3. Redaction and audit

**Acceptance:** no secrets in state/logs; audit references sufficient for incident diagnosis.

### P0-I — Live evals и release gate

#### I1. Reintroduce opt-in live eval harness

**Acceptance:** deterministic CI remains free/no-model; live suite separate, budgeted, multi-trial.

#### I2. Implement required scenarios

**Acceptance:** минимум 20 scenarios из §16.

#### I3. Routing ablation

**Acceptance:** compare all-frontier/all-balanced/adaptive routing on real project tasks.

#### I4. Release receipts

**Acceptance:** support claims tied to exact plugin/runner/provider versions and date.

### P0-J — README и onboarding

#### J1. Publish current honest README until runner passes gate

#### J2. Switch to target README only after P0 end-to-end evidence

#### J3. One-command setup

**Acceptance:** user configures only product-level preferences; no technical questionnaire.

---

## 19. P1

- detached campaign process with robust terminal control;
- auto-resume after machine restart via optional OS integration;
- GitHub merge queue/auto-merge improvements;
- multiple campaign queue with global budget;
- local UI/TUI only if status CLI proves insufficient;
- adaptive online routing after enough verified data;
- additional verifier types: browser/UI, deployment smoke, API contracts;
- local tracker migration to/from GitHub;
- richer observability with opt-in privacy-preserving traces;
- signed standalone binaries and update/rollback channel;
- remote worker support only after local runner is stable;
- better cost prediction and early budget estimate;
- automatic stale run reconciliation;
- reusable product context index, only if agentic inspection becomes a measured bottleneck.

---

## 20. P2

- Linear/Jira/GitLab adapters;
- additional model providers;
- deployment adapters;
- team policies and shared runners;
- organization-level budgets/governance;
- contextual bandit/learned router after sufficient dataset;
- optional web dashboard;
- skill/remediation marketplace;
- distributed execution;
- managed cloud control plane.

Не начинать P2 до стабильного local single-owner workflow.

---

## 21. Explicit non-goals для реализации

Не добавлять в P0:

- fixed PM/Architect/Developer/QA personas;
- обязательный TDD;
- обязательный PRD/spec;
- mandatory review для обычной правки;
- mandatory Issue/branch/PR;
- universal numeric risk matrix;
- hardcoded provider/model names в core;
- full product dashboard;
- постоянный daemon по умолчанию;
- custom generic workflow engine без spike;
- vector database только ради product context;
- issue для каждого finding;
- autonomous production deploy/payment/data deletion;
- новую abstraction, если host-native/official primitive достаточен.

---

## 22. Definition of Done для SkipHow 1.0

SkipHow 1.0 считается достигнутым, когда одновременно доказано:

1. Маленькая ясная задача выполняется напрямую без лишних artifacts и orchestration.
2. Нетехнический Owner не отвечает на engineering-choice вопросы.
3. Batch intake корректно разбирает, объединяет, классифицирует и сохраняет signals.
4. Material build-vs-reuse decisions исследуют ecosystem до custom build.
5. Campaign переживает forced process kill и provider context reset.
6. После restart work продолжается без duplicate mutation.
7. Model routing не зависит от конкретных model names в core.
8. Cheap profiles используются только там, где verifier/outcome подтверждает достаточность.
9. High-impact work автоматически получает stronger judgment/evidence.
10. GitHub scenario от Issue до merge/cleanup проходит end-to-end.
11. Система не удаляет user work и unmerged unique commits.
12. Все material findings имеют terminal disposition.
13. Optional unavailable checks честно остаются `UNVERIFIED`.
14. Pause/resume/cancel безопасны.
15. Protected actions не выполняются без authority.
16. Live evals multi-trial и привязаны к exact versions.
17. README claims не превосходят свежие receipts.
18. Common prompt route остаётся lean и выигрывает или не проигрывает ablation.
19. Установка и обычное использование не требуют понимания runtime architecture.
20. Финальный campaign report основан на reconciled environment state, а не на самоотчёте модели.

---

## 23. Порядок работы агента, которому передан этот документ

1. Не переписывать весь проект одним большим diff.
2. Сначала зафиксировать architecture/product decision и исправить claims.
3. Затем выполнить lean-kernel и Intake slices.
4. После этого провести executable durable-runtime spike.
5. Реализовать runner и один provider adapter.
6. Доказать crash/resume до второго adapter и GitHub expansion.
7. Затем добавить model routing, GitHub end-to-end и security hardening.
8. В конце reintroduce live evals, провести ablation и только после этого обновить продающие claims README.
9. Не спрашивать Owner о языке, SDK, schema или test strategy. Исследовать и принять техническое решение самостоятельно.
10. Любую найденную независимую проблему либо исправить, либо persist/deduplicate/dismiss с evidence; не терять и не расширять scope молча.

---

## 24. Ключевые источники для реализации

### Lean prompts, harness и evals

- OpenAI, model guidance: https://developers.openai.com/api/docs/guides/latest-model
- OpenAI, Codex best practices: https://developers.openai.com/codex/learn/best-practices
- Anthropic, Effective context engineering for AI agents: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Anthropic, Effective harnesses for long-running agents: https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
- Anthropic, Demystifying evals for AI agents: https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents

### Provider runtimes

- OpenAI Codex App Server: https://developers.openai.com/codex/app-server
- OpenAI Codex SDK: https://developers.openai.com/codex/codex-sdk
- Claude Agent SDK overview: https://code.claude.com/docs/en/agent-sdk/overview
- Claude Agent SDK Python reference: https://code.claude.com/docs/en/agent-sdk/python
- Claude Code CLI reference: https://code.claude.com/docs/en/cli-reference

### Model routing

- Agent-as-a-Router: https://arxiv.org/abs/2606.22902
- SWE-Router: https://arxiv.org/abs/2607.00053
- TwinRouterBench: https://arxiv.org/abs/2605.18859
- RouteLLM: https://arxiv.org/abs/2406.18665

### Durable execution candidates

- Restate AI quickstart: https://docs.restate.dev/ai-quickstart
- Restate architecture: https://docs.restate.dev/references/architecture
- Temporal production deployment: https://docs.temporal.io/production-deployment

### Prior art

- GSD: https://github.com/open-gsd/gsd-core
- OpenSpec: https://github.com/Fission-AI/OpenSpec
- Superpowers: https://github.com/obra/superpowers
- Matt Pocock skills: https://github.com/mattpocock/skills
- BMAD: https://github.com/bmad-code-org/bmad-method
- Paperclip: https://github.com/paperclipai/paperclip
- Mesa: https://github.com/msoedov/mesa
- Autonomous PM: https://github.com/mlobo2012/autonomous-pm-plugin

---

# Нормативная итоговая формула

```text
Smallest coherent outcome
→ minimum sufficient process
→ cheapest sufficient capability
→ evidence proportional to error cost
→ durable state only when recovery needs it
→ proportional invalidation
→ terminal disposition of every material finding
→ finish and reconcile the real environment
```
