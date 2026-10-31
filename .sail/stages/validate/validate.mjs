// Validates the branch in the workspace and prints the Validation: what is uncommitted, and how `scripts/gate.sh`
// ended (ruff check, ruff format --check, mypy src, the unit tests) on the change since the branch's base, or since its
// last validated commit when it has one, so the validation after a fix skips the gate when the fix touched only docs.
// The gate's output goes to stderr as it comes, so the call's log fills while it runs; a gate that outlasts
// GATE_SECONDS is stopped and fails the validation.
// A failing test is judged before it goes back to the implementer: one that passes when run again is flaky, and one
// that also fails on the branch's merge-base is the base's. When pytest is the only step that failed, failures that are
// all flaky pass, and failures that are all the base's, or flaky, set baseRed, which ends the run instead of another
// pass: no change of the branch fixes it. A failing lint or type check is always the change's: CI keeps staging clean.
// The failures come from pytest's short summary (`-rfE`): `FAILED <node id> - <message>` and `ERROR <node id> ...`.
import { spawn, spawnSync } from 'node:child_process';
import { appendFileSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';

const root = process.cwd();
const tail = (text, lines = 80) => text.split('\n').slice(-lines).join('\n').slice(-6000);
const GATE_SECONDS = Number(process.env.SAIL_GATE_SECONDS ?? 1200);
// The branch the pull request goes into. SAIL_VALIDATE_BASE stands in for it in a test of this script.
const BASE = process.env.SAIL_VALIDATE_BASE ?? 'origin/staging';
// The gate's step names, as it prints them in `gate: <step>` and `gate: <step> FAILED`.
const STEPS = ['ruff check', 'ruff format', 'mypy', 'pytest'];
// What the gate gives pytest, so a rerun runs the tests the way the gate did.
const PYTEST = ['-m', 'not integration', '-q', '-rfE', '--no-cov', '-p', 'no:cacheprovider'];
const PLACEHOLDERS = { API_KEY: 'gate-placeholder', CLAUDE_API_KEY: 'gate-placeholder' };

/** Runs git in `cwd`: its trimmed stdout, or undefined when it fails. */
function git(args, cwd = root) {
  const result = spawnSync('git', args, { cwd, encoding: 'utf8' });
  return result.status === 0 ? result.stdout.trim() : undefined;
}

const isAncestor = (commit, of) =>
  spawnSync('git', ['merge-base', '--is-ancestor', commit, of], { cwd: root }).status === 0;

const status = spawnSync('git', ['-c', 'core.quotePath=false', 'status', '--porcelain=v1', '--untracked-files=all'], {
  cwd: root,
  encoding: 'utf8',
});
if (status.status !== 0) throw new Error(`git status: ${status.stderr.trim()}`);
const uncommitted = status.stdout
  .split('\n')
  .filter(Boolean)
  .map((line) => line.slice(3));

// The commits that passed validation, oldest first, in the repository's common git directory: every run's workspace
// is a worktree of the same repository, so review sees the commits the factory validated.
const validated = join(resolve(root, git(['rev-parse', '--git-common-dir']) ?? '.git'), 'sail-validated');
const head = git(['rev-parse', 'HEAD']);
const mergeBase = git(['merge-base', 'HEAD', BASE]);

/** The branch's last validated commit. One already on the base doesn't count: its diff would hold the base's changes. */
function lastValidated() {
  let commits;
  try {
    commits = readFileSync(validated, 'utf8').split('\n').filter(Boolean);
  } catch {
    return undefined;
  }
  if (commits.length > 1000) writeFileSync(validated, `${commits.slice(-500).join('\n')}\n`);
  return commits.reverse().find((commit) => isAncestor(commit, 'HEAD') && !isAncestor(commit, BASE));
}

const since = lastValidated() ?? mergeBase;
if (since && since !== mergeBase) {
  process.stderr.write(`validate: checking what changed since ${since.slice(0, 12)}, validated last\n`);
}

/**
 * Runs `command` with `args` in `cwd`, passing its output through to stderr as it comes and collecting it. It leads a
 * process group of its own, so one past GATE_SECONDS is stopped with every process under it.
 */
function spawnLogged(command, args, cwd, env = {}) {
  return new Promise((done) => {
    const child = spawn(command, args, {
      cwd,
      stdio: ['ignore', 'pipe', 'pipe'],
      detached: true,
      env: { ...process.env, ...env },
    });
    const chunks = [];
    const pass = (chunk) => {
      chunks.push(chunk);
      process.stderr.write(chunk);
    };
    const stop = () => {
      try {
        process.kill(-child.pid, 'SIGKILL');
      } catch {}
    };
    // Its own group is out of reach of the stage's: a stopped validation stops the gate itself.
    for (const [signal, code] of [
      ['SIGTERM', 143],
      ['SIGINT', 130],
      ['SIGHUP', 129],
    ]) {
      process.once(signal, () => {
        stop();
        process.exit(code);
      });
    }
    let late = false;
    const timer = setTimeout(() => {
      late = true;
      stop();
    }, GATE_SECONDS * 1000);
    child.stdout.on('data', pass);
    child.stderr.on('data', pass);
    child.on('error', (error) => done({ code: null, log: `${error.message}\n` }));
    child.on('close', (code) => {
      clearTimeout(timer);
      const log = Buffer.concat(chunks).toString('utf8');
      done(
        late
          ? { code: null, log: `${log}\nvalidate: ${command} outlasted ${GATE_SECONDS} s and was stopped\n` }
          : { code, log },
      );
    });
  });
}

/** The gate's steps that failed, by the `gate: <step> FAILED` lines it printed. */
const failedSteps = (log) => STEPS.filter((step) => log.includes(`gate: ${step} FAILED`));

/** The gate's output for one step: from its `gate: <step>` line to its verdict line. */
function section(log, step) {
  const start = log.indexOf(`gate: ${step}\n`);
  if (start < 0) return '';
  const end = log.indexOf(`gate: ${step} FAILED`, start);
  return log.slice(start, end < 0 ? undefined : end).trim();
}

/** Each failing test in pytest's short summary, once: `{ test, message }`, `test` its node id. */
function failingTests(log) {
  const found = new Map();
  for (const line of log.split('\n')) {
    const match = /^(?:FAILED|ERROR) (\S+?(?:\[[^\]]*\])?)(?: - (.*))?$/.exec(line.trimEnd());
    if (match && !found.has(match[1])) found.set(match[1], { test: match[1], message: match[2] ?? '' });
  }
  return [...found.values()];
}

/**
 * The failing tests among `tests` when pytest runs them in `cwd` with this workspace's environment, or undefined when
 * the run didn't end or pytest didn't run them (exit 2 to 5: interrupted, an internal error, a usage error, or nothing
 * collected).
 */
async function rerun(tests, cwd) {
  const { code, log } = await spawnLogged(
    'uv',
    ['run', '--project', root, 'python', '-m', 'pytest', ...PYTEST, ...tests],
    cwd,
    PLACEHOLDERS,
  );
  if (code === null || (code !== 0 && code !== 1)) return undefined;
  return new Set(failingTests(log).map((each) => each.test));
}

/**
 * Each failing test's verdict: `flaky` when a rerun in the workspace doesn't fail it, `base` when it fails on the
 * branch's merge-base with the base too, and `change` otherwise. The base is checked out in a scratch worktree and its
 * tests run with this workspace's environment, then removed.
 */
async function classify(failing) {
  process.stderr.write(`validate: running ${failing.length} failing test(s) again\n`);
  const again = await rerun(
    failing.map((each) => each.test),
    root,
  );
  const still = failing.filter((each) => again === undefined || again.has(each.test));
  const verdict = (each, base) => ({
    test: each.test,
    verdict: !still.includes(each) ? 'flaky' : base?.has(each.test) ? 'base' : 'change',
  });
  if (still.length === 0 || mergeBase === undefined) return failing.map((each) => verdict(each, undefined));
  const dir = mkdtempSync(join(tmpdir(), 'life-organizer-be-validate-base-'));
  try {
    process.stderr.write(`validate: running ${still.length} test(s) on the base, ${mergeBase.slice(0, 12)}\n`);
    if (spawnSync('git', ['worktree', 'add', '--detach', dir, mergeBase], { cwd: root }).status !== 0) {
      return failing.map((each) => verdict(each, undefined));
    }
    const base = await rerun(
      still.map((each) => each.test),
      dir,
    );
    return failing.map((each) => verdict(each, base));
  } finally {
    spawnSync('git', ['worktree', 'remove', '--force', dir], { cwd: root });
    rmSync(dir, { recursive: true, force: true });
  }
}

/** What the implementer needs: each failed step's output, cut to its tail, pytest's led by its failing tests. */
function describeFailures(steps, failing, log) {
  if (steps.length === 0) return tail(log);
  const parts = steps.map((step) => {
    const text = section(log, step);
    if (step !== 'pytest' || failing.length === 0) return tail(text, 60);
    const summary = failing.map((each) => `${each.test}${each.message ? ` - ${each.message}` : ''}`).join('\n');
    return `${failing.length} failing test${failing.length === 1 ? '' : 's'}:\n${summary}\n\n${tail(text, 60)}`;
  });
  return parts.join('\n\n').slice(-8000);
}

const { code, log } = await spawnLogged('bash', [join(root, 'scripts', 'gate.sh'), '--base', since ?? BASE], root);
const steps = code === 0 || code === null ? [] : failedSteps(log);
const failing = steps.includes('pytest') ? failingTests(log) : [];
// Only pytest's failures are judged: a lint or type error is the change's, and judging tests beside one buys nothing.
const judged =
  failing.length > 0 && steps.length === 1
    ? await classify(failing)
    : failing.map((each) => ({ test: each.test, verdict: 'change' }));
const flaky = judged.filter((each) => each.verdict === 'flaky');
const red = judged.filter((each) => each.verdict === 'base');
const verdicts = [
  flaky.length > 0
    ? `validate: ${flaky.length} flaky, passing on a rerun: ${flaky.map((each) => each.test).join('; ')}`
    : '',
  red.length > 0 ? `validate: ${red.length} failing on the base too: ${red.map((each) => each.test).join('; ')}` : '',
]
  .filter(Boolean)
  .join('\n');
const verify = {
  ok: code === 0,
  exitCode: code ?? -1,
  failedSteps: steps,
  tail: [verdicts, code === 0 ? tail(log, 20) : describeFailures(steps, failing, log)].filter(Boolean).join('\n\n'),
  failures: judged,
};
// Only pytest failed, and every failing test is flaky: that passes. Every one is the base's, or flaky: staging's to fix.
const onlyPytest = steps.length === 1 && steps[0] === 'pytest' && judged.length > 0;
const onlyFlaky = onlyPytest && flaky.length === judged.length;
const baseRed = onlyPytest && red.length > 0 && red.length + flaky.length === judged.length;

const ok = uncommitted.length === 0 && (verify.ok || onlyFlaky);
if (ok && head) appendFileSync(validated, `${head}\n`);
console.log(JSON.stringify({ ok, uncommitted, verify, baseRed }));
process.exit(ok ? 0 : 1);
