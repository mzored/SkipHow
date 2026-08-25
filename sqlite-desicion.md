# Вердикт

**Нет, утверждать, что SQLite уже доказанно является лучшей финальной реализацией, нельзя.** Это смешивает два разных архитектурных решения:

```text
1. Где хранить durable state?
2. Кто реализует retries, timers, leases, recovery, cancellation и очереди?
```

SQLite хорошо решает первый вопрос, но сам по себе не решает второй.

Корректный вывод:

> **SQLite — наиболее обоснованный default state store для локального single-host режима SkipHow.**
>
> **Но лучшая реализация runner может оказаться либо `DBOS + SQLite`, либо узким собственным controller поверх SQLite. Это нужно определить executable fault-injection spike, а не декларацией в документе.**

В предыдущем ТЗ выбор фактически и не был зафиксирован: раздел 10.1 требует сравнить embedded controller, Restate, Temporal и provider-native execution до реализации. Поэтому формулировку «берём SQLite» следует заменить на «SQLite — baseline и наиболее вероятный default backend». [См. раздел 10.1 текущего ТЗ](sandbox:/mnt/data/SKIPHOW_FINAL_REFACTOR_SPEC_RU.md).

Это соответствует вашим собственным принципам: технический выбор должен принадлежать системе, но быть минимальным, проверяемым и не создавать лишнюю инфраструктуру.  Одновременно действует reuse-first: не следует самостоятельно писать workflow engine, пока не проверены подходящие maintained решения.

---

# Какие именно требования мы оптимизируем

Для default-режима SkipHow требования такие:

| Требование                                                    |                Приоритет |
| ------------------------------------------------------------- | -----------------------: |
| Установка одной командой                                      |                 критично |
| Нет обязательного облачного аккаунта                          |                 критично |
| Нет PostgreSQL/Redis/Docker как обязательных зависимостей     |                 критично |
| macOS, Linux и Windows                                        |                 критично |
| Работа офлайн с локальным repository                          |                 критично |
| Восстановление после process crash                            |                 критично |
| Сохранение подтверждённых переходов после перезагрузки машины |                 критично |
| Транзакционные task/run/attempt transitions                   |                 критично |
| Один локальный orchestrator на installation                   |   допустимое ограничение |
| Несколько параллельных субагентов                             |                требуется |
| Несколько независимых компьютеров, пишущих в одну БД          | не требуется для default |
| High availability database cluster                            | не требуется для default |
| Тысячи транзакций в секунду                                   |             не требуется |
| Простая диагностика и экспорт state                           |                    важно |
| Минимум собственного reliability-кода                         |                    важно |
| Открытая и долгоживущая архитектура                           |                    важно |

Особенно важно, что текущая архитектура уже предполагает одного владельца глобальной очереди: workers могут работать параллельно, но только root изменяет global queue и integration order.

Это почти идеально совпадает с моделью SQLite: много читателей, но только один writer в каждый момент. SQLite официально рекомендует client/server database при множестве одновременных writers или при доступе к данным по сети; для локального приложения с короткими транзакциями single-writer ограничение обычно не является проблемой. ([SQLite][1])

---

# Сравнение вариантов

| Вариант                         |  Zero-config |         Транзакции и запросы | Durable execution из коробки |   Multi-host |             Дополнительный процесс | Основной недостаток                                                               | Решение                             |
| ------------------------------- | -----------: | ---------------------------: | ---------------------------: | -----------: | ---------------------------------: | --------------------------------------------------------------------------------- | ----------------------------------- |
| JSON/YAML/files                 |           Да |                          Нет |                          Нет |          Нет |                                Нет | придётся самостоятельно писать atomicity, locking, indexes, migrations и recovery | Отклонить                           |
| Append-only file log            |           Да |                     Частично |                          Нет |          Нет |                                Нет | придётся писать собственную БД: framing, fsync, snapshots, compaction, indexes    | Только export/debug                 |
| Embedded KV: LMDB/RocksDB/redb  |           Да |                KV-транзакции |                          Нет |   Обычно нет |                                Нет | отношения, constraints, запросы и миграции переходят в application code           | Отклонить                           |
| **SQLite + bounded controller** |       **Да** |                       **Да** |            Нужно реализовать |          Нет |                                Нет | собственные retries, timers, queues и recovery logic                              | **Baseline**                        |
| **DBOS + SQLite**               |       **Да** |                       **Да** |                       **Да** |          Нет | Нет отдельного orchestrator server | молодой SQLite path, часть функций зависит от PostgreSQL                          | **Главный кандидат для spike**      |
| PostgreSQL + controller         |          Нет |                           Да |            Нужно реализовать |           Да |                                 Да | установка, lifecycle, credentials, backup и обновления сервера                    | Scale-up backend                    |
| DBOS + PostgreSQL               |          Нет |                           Да |                           Да |           Да |                         PostgreSQL | operational burden для solo installation                                          | Team/server mode                    |
| Restate single-node             |        Почти |             Встроенное state |                           Да | Cluster mode |                             **Да** | отдельный server, BSL, нет официальных Windows binaries                           | Optional advanced backend           |
| Temporal                        |          Нет |                Event history |                           Да |           Да |          Да, несколько компонентов | непропорционально тяжёлая эксплуатация                                            | Enterprise only                     |
| Redis/Streams/queue             |          Нет | Не полноценная relational БД |                     Частично |           Да |                                 Да | всё равно нужен authoritative store                                               | Не использовать как source of truth |
| GitHub Issues                   | Не автономно |                  Ограниченно |                          Нет |           Да |                         Remote API | latency, rate limits, отсутствие локальной атомарности                            | Только внешний tracker              |

## 1. JSON, YAML и собственный event log

Файлы выглядят проще только до первого реального требования:

```text
claim task
+ create attempt
+ increment revision
+ append audit event
+ reserve budget
+ register external effect
```

Эти изменения должны либо произойти все, либо не произойти ни одно.

SQLite уже предоставляет atomic commit: все изменения одной транзакции применяются целиком либо не применяются вообще. ([SQLite][2])

При использовании файлов SkipHow пришлось бы самостоятельно реализовать:

* блокировки между процессами;
* защиту от torn writes;
* WAL или журнал отката;
* checksums и framing;
* индексы;
* referential integrity;
* schema migrations;
* snapshots и compaction;
* recovery после падения во время compaction.

Это буквально создание более слабой версии SQLite. Поэтому отдельный append-only файл не должен быть вторым authoritative source. Event log должен быть **таблицей в той же SQLite-транзакции**, а JSON — только производным export.

## 2. Embedded KV

LMDB, RocksDB или redb могут быть быстрыми и crash-safe, но SkipHow не является key-value workload.

У него естественно реляционная модель:

```text
Run
 ├─ Tasks
 │   ├─ Attempts
 │   ├─ Leases
 │   ├─ Dependencies
 │   └─ External effects
 ├─ Findings
 ├─ Checkpoints
 ├─ Provider sessions
 └─ Events
```

В KV-store пришлось бы самостоятельно реализовать:

* secondary indexes;
* uniqueness;
* foreign keys;
* dependency queries;
* schema evolution;
* cascade rules;
* ad-hoc repair and inspection tooling.

KV не удаляет значимую эксплуатационную нагрузку по сравнению с SQLite, но добавляет application-level complexity. Поэтому SQLite его доминирует для этого domain.

## 3. PostgreSQL

PostgreSQL существенно лучше, когда:

* несколько hosts одновременно изменяют state;
* существует несколько независимых scheduler processes;
* нужен общий team control plane;
* требуется высокая write concurrency;
* требуется HA/failover;
* удалённые сервисы должны обращаться к общей БД.

PostgreSQL использует MVCC, позволяя множеству sessions читать и изменять данные с существенно лучшей multi-user concurrency. ([PostgreSQL][3])

Но для default SkipHow это не бесплатное преимущество. Оно требует:

* server process;
* установки или Docker;
* порта;
* credentials;
* lifecycle management;
* backup policy;
* обновлений;
* network configuration;
* дополнительного failure mode.

При одном локальном writer PostgreSQL не даёт полезной способности, которой не хватает SQLite, но добавляет эксплуатацию. Поэтому для default installation он строго хуже по total ownership cost.

PostgreSQL следует добавить позже как **scale-up backend**, а не использовать с первого дня.

## 4. Restate

Restate функционально очень близок к нужной системе:

* durable workflows;
* durable timers;
* retries;
* waits;
* state;
* cancellation;
* параллельные recoverable operations;
* single-node или cluster deployment.

Restate Server поставляется как один самостоятельный binary и выполняет durable execution перед пользовательскими services. ([Restate][4])

Но для universal default у него три проблемы.

Во-первых, это всё равно отдельный server process и отдельная runtime boundary, а не embedded library.

Во-вторых, официальный список prebuilt binaries сейчас включает macOS и Linux, но не Windows. ([Restate][5])

В-третьих, Restate Server распространяется под Business Source License 1.1. Лицензия разрешает широкий production use и через четыре года переводит конкретный release на Apache 2.0, но прямо указывает, что текущая BSL не является open-source license. Для долгоживущего универсального open-source инструмента это ненужная лицензионная зависимость. ([GitHub][6])

Поэтому Restate достоин spike, но не является лучшим default.

## 5. Temporal

Temporal предоставляет наиболее зрелую модель durable replay: workflow event history хранится как source of truth, а execution может быть восстановлено после сбоя. ([Документация Temporal][7])

Но собственная документация Temporal описывает self-hosted production как сложную систему, требующую:

* capacity planning;
* load testing;
* monitoring;
* server upgrades;
* persistence infrastructure;
* Kubernetes или эквивалентной инфраструктуры;
* опытных operators;
* иногда отдельного control plane.

Temporal прямо называет production Temporal Service сложным и потенциально дорогим в эксплуатации. ([Документация Temporal][8])

Это подходящее решение для централизованного enterprise SkipHow Cloud, но не для локального инструмента solo-основателя.

## 6. DBOS + SQLite

Это наиболее серьёзный конкурент собственной реализации.

DBOS является embedded library: отдельный orchestration server не требуется. Он предоставляет:

* durable workflows;
* durable steps;
* queues;
* scheduling;
* workflow recovery;
* cancellation;
* versioning;
* programmatic workflow management.

Python-версия DBOS по умолчанию использует SQLite и может использовать PostgreSQL через ту же конфигурационную границу. ([GitHub][9])

То есть потенциальная архитектура получается такой:

```text
SkipHow runner
  ├─ DBOS durable workflows
  ├─ SQLite system database
  ├─ provider adapters
  └─ Git/GitHub adapters
```

Это лучше собственного controller, **если DBOS действительно закрывает необходимые failure modes без создания второго source of truth**.

Но готового доказательства пока нет:

* документация DBOS рекомендует SQLite прежде всего для prototyping/testing и PostgreSQL для production/distributed deployment;
* SQLite mode использует polling вместо PostgreSQL `LISTEN/NOTIFY`;
* некоторые query/filter capabilities поддерживаются только с PostgreSQL;
* следовательно, SQLite path имеет не полную feature parity с PostgreSQL. ([DBOS Docs][10])

Для SkipHow generic-рекомендация «PostgreSQL в production» не обязательно является решающей: default SkipHow намеренно является single-host local application, а не distributed web service. Но DBOS должен быть фактически проверен на нужных сценариях.

---

# В каком смысле SQLite можно считать доказанно лучшим

Можно сделать не абсолютное, а **условное доказательство через dominance**.

Пусть выполняются условия:

```text
A1. State находится на одном физическом компьютере.
A2. Один coordinator является authoritative writer.
A3. Workers не изменяют global queue напрямую.
A4. Write transactions короткие.
A5. Нет обязательного HA и shared multi-host access.
A6. Установка без отдельного database service — product requirement.
A7. Нужны atomic transitions, relations, constraints и queryability.
```

Тогда:

1. Files не удовлетворяют A7 без значительного custom infrastructure.
2. KV-store удовлетворяет durability, но не даёт relational semantics и требует больше domain code.
3. PostgreSQL удовлетворяет все correctness requirements, но добавляет server operations ради multi-host concurrency, которая запрещена предпосылками.
4. SQLite удовлетворяет atomicity, relational state, queryability и zero-service requirement.
5. Его основное ограничение — один writer — уже совпадает с A2.
6. WAL позволяет readers продолжать работу одновременно с writer, пока все процессы находятся на одном host. ([SQLite][11])

Следовательно:

> **Среди raw storage engines SQLite является Pareto-optimal и фактически доминирует остальные варианты для заданного default profile.**

Но это доказательство относится к **storage engine**, а не к реализации workflow semantics. DBOS и Restate решают более широкую задачу, поэтому их нельзя исключить тем же аргументом.

---

# Рекомендуемая финальная архитектура

## 1. SQLite — default state backend

```text
Runner Core
    ↓ domain-level RunnerStore
SQLiteRunnerStore          ← default
PostgresRunnerStore        ← future server/team mode
```

Интерфейс должен быть domain-specific, а не абстракцией над SQL:

```text
create_run
append_intake_items
claim_ready_task
start_attempt
renew_lease
commit_task_transition
register_external_effect
record_checkpoint
request_pause
request_cancel
complete_attempt
reconcile_effect
```

Не нужно заранее поддерживать общий набор SQL dialects. PostgreSQL adapter добавляется только после появления соответствующего product mode.

## 2. Один SQLite database на installation

```text
<OS application-data directory>/
  skiphow/
    state.sqlite3
    runs/
      <run-id>/
        evidence/
        logs/
        artifacts/
        recovery/
```

В БД хранятся:

* состояние;
* идентификаторы;
* revisions;
* leases;
* budgets;
* references;
* hashes;
* material events;
* idempotency keys;
* compact recovery capsules.

Вне БД хранятся:

* длинные command logs;
* модели transcript;
* screenshots;
* diffs;
* test reports;
* большие evidence artifacts.

Это не должно быть по одной БД на run: одна installation database упрощает recovery, global queue, model budgets, listing и migrations. Run artifacts остаются изолированными по directories.

## 3. Single-writer architecture

Workers и субагенты не должны самостоятельно изменять SQLite.

```text
workers
  ↓ structured result / event
coordinator
  ↓ serialized transaction
SQLite
```

CLI/UI control commands предпочтительно идут через IPC coordinator:

```text
pause
resume
cancel
approve protected action
inspect
```

Read-only inspection может использовать отдельное SQLite connection.

Это делает single-writer ограничение SQLite не компромиссом, а намеренно обеспечиваемым invariant.

## 4. Правильные SQLite settings

Для runner state:

```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = FULL;
PRAGMA foreign_keys = ON;
PRAGMA busy_timeout = <bounded value>;
```

Почему `FULL`, а не распространённый `NORMAL`:

* в WAL mode `NORMAL` сохраняет согласованность при application crash;
* но последняя подтверждённая транзакция может быть потеряна при OS crash или power loss;
* `FULL` выполняет дополнительный sync WAL после каждого commit и обеспечивает ACID durability при power loss. ([SQLite][12])

Для высоконагруженного web application `NORMAL` часто разумнее. Для SkipHow write volume небольшой, а ложное утверждение «задача завершена» после потери commit значительно дороже дополнительного fsync. Поэтому здесь `FULL` — корректный trade-off.

Дополнительно:

* использовать `STRICT` tables;
* включать foreign keys на каждом connection;
* использовать `CHECK` constraints для status и revision;
* не держать transaction открытой во время model/API/Git calls;
* write transactions должны содержать только короткие state transitions;
* операции claim/lease должны атомарно проверять revision и fencing token;
* для write paths, где lock должен быть получен до чтения mutable state, использовать явную write transaction, например `BEGIN IMMEDIATE`; SQLite рекомендует это как способ не получить `SQLITE_BUSY` в середине транзакции. ([SQLite][13])

## 5. Event log внутри той же БД

Предыдущую формулировку:

```text
transactional store
+ append-only event log
+ JSON snapshot
```

следует уточнить:

```text
SQLite:
  current-state tables
  append-only events table
  external-effects/outbox table

Derived:
  JSON export
  human-readable run summary
```

При каждом material transition в одной транзакции:

```sql
UPDATE tasks ... WHERE revision = ?;
INSERT INTO events ...;
INSERT INTO external_effects ...; -- когда необходимо
UPDATE runs ...;
COMMIT;
```

Отдельная запись JSON рядом с DB не должна участвовать в correctness. Иначе возникает dual-write problem.

## 6. Внешние side effects

Ни SQLite, ни PostgreSQL, ни workflow engine не могут общей транзакцией атомарно объединить:

```text
local database commit
+
GitHub PR creation
+
provider API call
+
git push
```

Поэтому SkipHow не должен обещать абстрактный exactly-once.

Правильная модель:

```text
at-least-once execution
+ stable idempotency key
+ effect journal
+ external reconciliation
+ fencing token
```

Пример:

```text
1. Записать PLANNED effect с idempotency_key.
2. Выполнить GitHub operation вне DB transaction.
3. Сохранить external identifier.
4. При ambiguous crash найти существующий PR/Issue/comment.
5. Не создавать второй объект, пока reconciliation не завершён.
```

## 7. Backup и corruption handling

Нельзя просто копировать `state.sqlite3`, пока WAL активен. WAL является частью persistent state; отделение DB от WAL может привести к потере уже committed транзакций. SQLite рекомендует Online Backup API, `VACUUM INTO` либо согласованное копирование полного состояния. ([SQLite][14])

Нужны:

* Online Backup API перед schema migration;
* versioned migrations;
* startup integrity check после unclean shutdown;
* explicit export command;
* documented restore;
* отказ от размещения authoritative DB на NFS/network filesystem;
* cloud-synced directories считать unsupported, пока их конкретное поведение не проверено.

WAL официально требует, чтобы все процессы находились на одном host, и не работает поверх network filesystem. ([SQLite][11])

---

# Как действительно доказать выбор

Статическое сравнение недостаточно. Нужен один bounded spike с тремя реализациями:

```text
A. Raw SQLite + minimal controller
B. DBOS Python + SQLite
C. Restate single-node
```

Temporal достаточно оценить документально: он уже нарушает default operational constraints.

Каждый вариант должен выполнить один и тот же fault matrix.

| Fault scenario                                  | Требуемый результат                                                    |
| ----------------------------------------------- | ---------------------------------------------------------------------- |
| `kill -9` сразу после task claim                | task безопасно reclaim после lease expiry                              |
| crash после provider response, до local commit  | результат либо reconciled, либо повторён безопасно                     |
| crash после GitHub PR creation, до записи PR ID | существующий PR найден, duplicate не создаётся                         |
| stale worker завершился после reassignment      | fencing token отклоняет его mutation                                   |
| crash во время checkpoint                       | предыдущий valid checkpoint остаётся читаемым                          |
| context compaction                              | новая session получает полный recovery capsule и один следующий action |
| pause одновременно с task completion            | получается одно согласованное terminal состояние                       |
| cancel во время external wait                   | wait прекращается или помечается pending cancellation без потери state |
| runner upgrade при незавершённом run            | migration/versioning не ломает resume                                  |
| два campaigns и несколько независимых lanes     | нет потерянных transitions и неконтролируемых lock failures            |
| host reboot после acknowledged commit           | подтверждённый transition сохранён                                     |
| backup во время активной работы                 | восстановленная копия является consistent snapshot                     |
| повторный запуск команды                        | duplicate Issue, branch, PR, comment и model run не создаются          |
| Windows/macOS/Linux fresh install               | запуск без ручной установки database server                            |

## Жёсткие acceptance gates

Любой вариант отклоняется при наличии хотя бы одного из следующих результатов:

* committed state потерян после предусмотренного failure;
* stale worker может изменить reassigned task;
* возникает необнаруженный duplicate external side effect;
* recovery требует полного transcript;
* существуют два несогласованных authoritative state stores;
* для default installation требуется Docker или database service;
* database migration может молча сделать in-flight run невосстановимым;
* Windows/macOS/Linux не поддерживаются одинаковым user-facing flow;
* требуется общий custom framework вокруг выбранного framework.

Дополнительно измеряются:

```text
custom reliability code
dependency footprint
install time
startup time
idle resource usage
write latency with FULL durability
recovery latency
migration complexity
debuggability
number of background processes
```

---

# Правило выбора после spike

## Выбрать DBOS + SQLite, если

* все fault tests проходят;
* SQLite mode поддерживает необходимые queues, waits, cancellation и recovery;
* нет критичной зависимости от Postgres-only функций;
* DBOS system state не дублирует собственный authoritative task state;
* code upgrades незавершённых runs управляемы;
* установка остаётся одной командой;
* DBOS действительно удаляет существенную часть scheduler/retry/timer/recovery кода.

Это наиболее привлекательный исход с точки зрения reuse-first.

## Выбрать raw SQLite + bounded controller, если

* DBOS создаёт dual source of truth;
* SQLite mode имеет существенные ограничения;
* versioning/replay плохо сочетается с динамической agent orchestration;
* dependency добавляет почти столько же adapter code, сколько удаляет;
* собственный controller остаётся узким набором domain transitions, а не превращается в generic workflow engine.

## Выбрать Restate, только если

* первые два варианта не могут безопасно реализовать external waits и recovery без создания полноценного workflow engine;
* дополнительный process приемлем;
* Windows packaging решён;
* BSL соответствует выбранной модели распространения SkipHow.

## Перейти на PostgreSQL, когда появляется хотя бы одно требование

```text
multiple active controller hosts
shared team control plane
remote workers writing shared state
high availability
sustained write contention
server/SaaS deployment as primary mode
```

Это должно быть product-triggered migration, а не speculative scalability.

---

# Итоговое архитектурное решение

Финальный ADR следует сформулировать так:

> **SkipHow использует SQLite как default authoritative state backend для локального single-host режима.**
>
> Выбор обоснован zero-service installation, ACID transactions, relational integrity, cross-platform availability и соответствием single-writer coordinator architecture.
>
> SQLite не используется на network filesystems и не позиционируется как distributed database.
>
> Durable execution implementation выбирается после executable comparison:
>
> 1. `DBOS + SQLite` — предпочтительный reuse candidate;
> 2. bounded controller поверх SQLite — reference и fallback;
> 3. Restate — optional advanced backend;
> 4. PostgreSQL — будущий shared/server mode;
> 5. Temporal — не default, только enterprise deployment.
>
> SQLite event table является частью authoritative transaction. JSON и filesystem artifacts являются только производными данными.
>
> Внешние операции используют idempotency, fencing и reconciliation; система не обещает невозможную сквозную exactly-once транзакцию.

Таким образом, **SQLite действительно является лучшим текущим выбором для default persistence**, и это можно обосновать архитектурно. Но называть **raw SQLite controller** лучшей финальной реализацией пока преждевременно. Согласно вашему же reuse-first принципу, первым должен быть проверен `DBOS + SQLite`; только fault-injection результаты должны решить, удаляет ли он достаточно собственной инфраструктуры или создаёт новую сложность.

[1]: https://sqlite.org/whentouse.html "https://sqlite.org/whentouse.html"
[2]: https://www.sqlite.org/atomiccommit.html "https://www.sqlite.org/atomiccommit.html"
[3]: https://www.postgresql.org/docs/current/mvcc.html "https://www.postgresql.org/docs/current/mvcc.html"
[4]: https://docs.restate.dev/foundations/key-concepts "https://docs.restate.dev/foundations/key-concepts"
[5]: https://docs.restate.dev/installation "https://docs.restate.dev/installation"
[6]: https://github.com/restatedev/restate/blob/main/LICENSE "https://github.com/restatedev/restate/blob/main/LICENSE"
[7]: https://docs.temporal.io/workflows "https://docs.temporal.io/workflows"
[8]: https://docs.temporal.io/self-hosted-guide/production-checklist "https://docs.temporal.io/self-hosted-guide/production-checklist"
[9]: https://github.com/dbos-inc/dbos-transact-py "https://github.com/dbos-inc/dbos-transact-py"
[10]: https://docs.dbos.dev/python/tutorials/database-connection "https://docs.dbos.dev/python/tutorials/database-connection"
[11]: https://www.sqlite.org/wal.html "https://www.sqlite.org/wal.html"
[12]: https://sqlite.org/pragma.html "https://sqlite.org/pragma.html"
[13]: https://sqlite.org/rescode.html "https://sqlite.org/rescode.html"
[14]: https://sqlite.org/backup.html "https://sqlite.org/backup.html"
