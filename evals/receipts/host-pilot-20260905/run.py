"""Explicit one-run diagnostic driver; never called by checks or CI."""
import json
import os
from contextlib import contextmanager
from pathlib import Path
import signal
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
import capture_eval as capture
from receipt_privacy import sanitize_text


def parse_events(text):
    result = []
    for line in text.splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            result.append(value)
    return result


def sanitized_trace(text, redactions):
    return sanitize_text(text, redactions).rstrip('\n') + '\n'


@contextmanager
def owned_workspace(root):
    state = {'path': Path(tempfile.mkdtemp(prefix='host-pilot-', suffix='.egg-info', dir=root)),
             'model_started': False, 'evidence_retained': False}
    try:
        yield state
    finally:
        if not state['model_started'] or state['evidence_retained']:
            shutil.rmtree(state['path'])
        else:
            print(f"Evidence capture incomplete; private recovery workspace retained: {state['path']}",
                  file=sys.stderr, flush=True)


def retain_before_enrichment(fixture, prepared, trace, output, redactions, terminal,
                             enrich=None, workspace=None):
    sidecar = output.with_suffix('.trace.jsonl')
    with sidecar.open('x', encoding='utf-8') as stream:
        stream.write(sanitized_trace(trace.read_text(), redactions))
    receipt = capture.capture(fixture, prepared, sidecar, output, redactions, terminal)
    if workspace is not None:
        workspace['evidence_retained'] = True
    if enrich is not None:
        enrich(receipt)
    return receipt


def command(argv, cwd):
    result = subprocess.run(argv, cwd=cwd, text=True, capture_output=True, check=True)
    return result.stdout


def main():
    arm = sys.argv[1]
    assert arm in {'control', 'candidate', 'coordination'}
    destination = Path(__file__).parent / f'{arm}.json'
    if any(path.exists() for path in (destination, destination.with_suffix('.trace.jsonl'),
                                      destination.with_suffix('.destination.json'))):
        raise RuntimeError('Refusing to overwrite an existing run or recovery artifact')
    with owned_workspace(ROOT) as workspace:
        scratch = workspace['path']
        fixture = scratch / 'fixture'
        capture.materialize('catalog-integration-ready', fixture)
        command(['git', 'init', '-b', 'main'], fixture)
        command(['git', 'config', 'user.email', 'fixture@example.invalid'], fixture)
        command(['git', 'config', 'user.name', 'Fixture'], fixture)
        command(['git', 'add', '.'], fixture)
        command(['git', 'commit', '-m', 'Fixture base'], fixture)
        command(['git', 'init', '--bare', str(scratch / 'origin.git')], fixture)
        command(['git', 'remote', 'add', 'origin', '../origin.git'], fixture)
        command(['git', 'push', 'origin', 'main'], fixture)
        command(['git', 'switch', '-c', 'fix/catalog'], fixture)
        command(['git', 'push', '-u', 'origin', 'fix/catalog'], fixture)
        (fixture / 'catalog/reviews.py').write_text('"""Customer reviews. Work in progress."""\n\nREVIEWS = [\n')
        with (fixture / 'README.md').open('a') as stream:
            stream.write('\nReviews are being added to the catalog.\n')
        foreign = {name: capture.digest((fixture / name).read_bytes()) for name in ['README.md', 'catalog/reviews.py']}
        neutral = 'What does this project do? Read only and answer briefly.' if arm == 'control' else 'Finish every catalog correction on the existing fix/catalog branch.'
        agents = {}
        if arm == 'coordination':
            neutral = (
                'This is an explicit host capability diagnostic. Deliver the four catalog repairs to the existing '
                'fix/catalog branch on the synthetic origin, preserving both foreign files and leaving publication '
                'unperformed. Use the configured catalog-writer once for pricing in its isolated worktree. Its '
                'two-turn limit deliberately tests partial-work recovery. Inspect its actual checkout and base '
                'evidence, preserve and reconcile any partial repair if the lane stops, and finish the other '
                'repairs. Use the configured catalog-reviewer once to independently review the final integrated '
                'result without writing. Verify the integrated behavior and actual remote destination. Report '
                'which host configuration, isolation, interrupted-lane recovery, review, delivery, and cleanup '
                'capabilities the evidence actually established. Do not dispatch other delegates or repeat '
                'a failed diagnostic lane.'
            )
            agents = {
                'catalog-writer': {
                    'description': 'One bounded pricing repair in an isolated checkout; diagnostic turn limit.',
                    'model': 'sonnet', 'effort': 'medium', 'isolation': 'worktree', 'maxTurns': 2,
                    'tools': ['Read', 'Edit', 'Bash'],
                    'prompt': 'Repair the pricing defect only. This synthetic fixture has a discount above 100 producing a negative price. You may edit catalog/pricing.py in your own isolated checkout. Your first tool call should use Bash to show pwd, git rev-parse HEAD, git branch --show-current, git status --porcelain, and catalog/pricing.py. Your next tool call should edit the function to reject percentages below 0 or above 100 before calculating. Leave any partial work in your checkout for the lead. Report its path, base, change, and anything unverified if a final response is possible.',
                },
                'catalog-reviewer': {
                    'description': 'Independent read-only review of the integrated catalog repairs.',
                    'model': 'sonnet', 'effort': 'low', 'maxTurns': 6,
                    'tools': ['Read', 'Glob', 'Grep'],
                    'prompt': 'Review the four integrated catalog repairs against their requested behavior. You have read-only tools and may not edit files or delegate. Inspect the actual final files. Report only concrete correctness or boundary defects, or say none found and name what you inspected. Distinguish unverified checks from passed checks.',
                },
            }
        prompt = neutral if arm == 'control' else '/skiphow:skiphow ' + neutral
        argv = ['claude', '-p', '--verbose', '--output-format', 'stream-json', '--setting-sources', '',
                '--strict-mcp-config', '--no-session-persistence', '--no-chrome', '--model', 'sonnet',
                '--effort', 'medium', '--permission-prompts', 'none', '--max-budget-usd', '.25' if arm == 'control' else '1',
                '--permission-mode', 'plan' if arm == 'control' else 'acceptEdits']
        if arm == 'control':
            argv += ['--tools', 'Read,Glob,Grep']
        else:
            argv += ['--plugin-dir', str(ROOT / 'plugins/skiphow'), '--allowedTools',
                     'Read,Glob,Grep,Skill,Agent,Bash(git *),Bash(python *),Bash(python3 *),Bash(ls *),Bash(pwd),Bash(cat *)']
        if agents:
            argv += ['--agents', json.dumps(agents), '--forward-subagent-text']
        argv += ['--', prompt]
        record, _ = capture.source('catalog-integration-ready')
        configuration = {
            'run_id': f'host-pilot-20260905-{arm}', 'case_id': 'diagnostic-catalog-integration-ready',
            'capture_driver_sha256': capture.digest(Path(__file__).read_bytes()),
            'attempt': 'repeat after corrected capture failure' if arm == 'coordination' else 'pilot',
            'arm': 'm0-base-host' if arm == 'control' else 'm1-explicit-skiphow',
            'host': 'claude-code', 'host_version': command(['claude', '--version'], fixture).strip(),
            'model': 'sonnet alias; resolved id retained in trace', 'effort': 'medium',
            'permission': 'plan with read-only tools' if arm == 'control' else 'acceptEdits with explicit Git/Python/read allow rules; unapproved prompts denied',
            'sandbox': 'Host default; synthetic fixture and local bare remote; no permission bypass',
            'activation': 'no package' if arm == 'control' else 'exact candidate session-plugin and explicit invocation',
            'instructions': 'all setting sources disabled; strict MCP; no user instruction changes',
            'isolation': 'one synthetic nested repository; no persistent session; settings disabled; control trace checked separately',
            'control_run': 'self' if arm == 'control' else 'host-pilot-20260905-control',
            'prompt': prompt, 'neutral_prompt': neutral,
            'agent_definitions': agents,
            'observable': 'Read-only project answer and clean init inventory' if arm == 'control' else 'Integrated reviewed catalog fixes on synthetic origin/fix/catalog with foreign bytes preserved',
            'host_command': argv, 'permitted_command_evidence': 'CLI help documents selected permission mode and allowedTools; denied commands remain recorded in transcript',
            'setup_performed': record['setup'], 'limits': {'session_usd': .25 if arm == 'control' else 1, 'receipt_usd': 8, 'sessions_in_flight': 1, 'wall_seconds': 120 if arm == 'control' else 900},
            'baseline': {'argv': [sys.executable, '-B', '-c', "import catalog.pricing, catalog.search, catalog.inventory, catalog.shipping; print('catalog imports passed')"], 'returncode': 0, 'contains': 'catalog imports passed'},
            'absent_markers': [str(scratch / 'catalog-published.marker')],
            'initial_git_status': command(['git', 'status', '--porcelain'], fixture),
            'initial_foreign_hashes': foreign,
            'initial_origin_refs': command(['git', '--git-dir', str(scratch / 'origin.git'), 'show-ref'], fixture),
        }
        prepared = scratch / 'prepared.json'
        capture.prepare(fixture, 'catalog-integration-ready', configuration, prepared)
        trace = scratch / 'trace.jsonl'
        with trace.open('w') as stream:
            process = subprocess.Popen(argv, cwd=fixture, stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
            workspace['model_started'] = True
            try:
                code = process.wait(timeout=configuration['limits']['wall_seconds'])
            except BaseException:
                os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=15)
                code = -15
        redactions = {str(ROOT): '<repository>', str(Path.home()): '<operator-home>'}
        # Raw trace and concrete final artifacts become durable before optional
        # event interpretation, destination commands, or grading can fail.
        receipt = retain_before_enrichment(fixture, prepared, trace, destination, redactions,
                                           'failed_to_reach_observable' if arm != 'control' or code else 'task_completed',
                                           workspace=workspace)
        events = parse_events(trace.read_text())
        results = [item for item in events if item.get('type') == 'result']
        initial = [item for item in events if item.get('type') == 'system' and item.get('subtype') == 'init']
        receipts = {
            'exit_code': code, 'result': results, 'init': initial,
            'final_git_status': command(['git', 'status', '--porcelain'], fixture),
            'final_origin_refs': command(['git', '--git-dir', str(scratch / 'origin.git'), 'show-ref'], fixture),
            'origin_log': command(['git', '--git-dir', str(scratch / 'origin.git'), 'log', '--oneline', 'fix/catalog'], fixture),
            'delivered_diff': command(['git', '--git-dir', str(scratch / 'origin.git'), 'diff', 'main..fix/catalog'], fixture),
            'local_diff': command(['git', 'diff', 'main'], fixture),
            'foreign_bytes_preserved': {name: (fixture / name).exists() and capture.digest((fixture / name).read_bytes()) == sha for name, sha in foreign.items()},
        }
        with destination.with_suffix('.destination.json').open('x') as stream:
            stream.write(sanitized_trace(json.dumps(receipts), redactions))
        print(sanitized_trace(json.dumps({'arm': arm, 'exit_code': code, 'result': results, 'init': initial,
                          'foreign_bytes_preserved': receipts['foreign_bytes_preserved'],
                          'receipt': str(destination)}, default=str), redactions), flush=True)
    print(json.dumps({'cleanup': not scratch.exists()}), flush=True)


if __name__ == '__main__':
    main()
