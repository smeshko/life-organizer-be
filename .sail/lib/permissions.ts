// The two permission profiles every agent stage of this .sail/ runs under, so a command the agents reach for is
// allowed once, here, and not stage by stage. What guards a run is the worktree it works in, the write globs, the
// engine's deny set, and the outward actions (push, pull request, merge, ticket moves) living in script stages: so a
// stage may run any command, and `deny` names only what reaches out of the run, touches the machine's shared services
// (the local Postgres, Docker, the dev server on port 8000) or, for a reader, changes the branch.
import type { Permissions } from 'sail';

/** What no agent of this repository runs: anything that reaches outside the run, or another process on the machine. */
const OUTWARD = [
  'git push *',
  'git remote *',
  'git worktree *',
  'git config *',
  'gh *',
  'curl *',
  'wget *',
  'ssh *',
  'scp *',
  'rsync *',
  'nc *',
  'npm *',
  'npx *',
  'brew *',
  'pip *',
  'pip3 *',
  'uv pip *',
  'uvx *',
  'uv tool *',
  'pre-commit install *',
  'pre-commit uninstall *',
  'sail *',
  'security *',
  'defaults *',
  'open *',
  'osascript *',
  'kill *',
  'pkill *',
  'killall *',
  // The machine's shared services: `make stop` and `make run` kill whatever holds port 8000, the docker targets drive
  // the shared containers, and migrations and psql reach the local database. The gate runs everything a change needs.
  'make *',
  'docker *',
  'docker-compose *',
  'psql *',
  'alembic upgrade *',
  'alembic downgrade *',
  'alembic stamp *',
  'uv run alembic upgrade *',
  'uv run alembic downgrade *',
  'uv run alembic stamp *',
  'railway *',
];

/** The repository's own paths, which a stage that changes the branch writes. */
const REPOSITORY = [
  'src/**',
  'tests/**',
  'alembic/**',
  'alembic.ini',
  'config/**',
  'pyproject.toml',
  'uv.lock',
  'models.yaml',
  'openapi.yaml',
  'scripts/**',
  'docs/**',
  '.sail/**',
  '.gitignore',
  '.pre-commit-config.yaml',
  '.editorconfig',
  '.env.example',
  'Makefile',
  'Dockerfile',
  'docker-compose.yml',
  '.dockerignore',
  // CI and the project's Claude Code settings.
  '.github/**',
  '.claude/**',
  // The abandoned tooling LIFE-39 deletes.
  '_bmad/**',
  '_bmad-output/**',
  '.adw/**',
  'AGENTS.md',
  'CLAUDE.md',
  'README.md',
  'DOCKER.md',
];

/**
 * A stage that reads the change and writes only its own files: it runs the gate, tests and any read it needs, and
 * never commits, moves files, changes the dependencies or rewrites the branch.
 */
export const readonly: Permissions = {
  read: ['**'],
  write: ['$STAGE_OUT/**'],
  commands: ['*'],
  deny: [
    ...OUTWARD,
    'git add *',
    'git commit *',
    'git rm *',
    'git mv *',
    'git restore *',
    'git stash *',
    'git reset *',
    'git rebase *',
    'git merge *',
    'git cherry-pick *',
    'git revert *',
    'git am *',
    'git apply *',
    'git tag *',
    'uv add *',
    'uv remove *',
    'uv lock *',
    'ruff format *',
    'uv run ruff format *',
    'rm *',
    'mv *',
    'sed -i*',
  ],
};

/**
 * A stage that changes the branch: it writes the repository's own paths, commits, adds dependencies with `uv add` and
 * runs anything else, but never pushes or reaches outside the run. Files go with `git rm` and `git mv`, so a removal is
 * always in a commit.
 */
export const builder: Permissions = {
  read: ['**'],
  write: [...REPOSITORY, '$STAGE_OUT/**'],
  commands: ['*'],
  deny: [...OUTWARD, 'rm *'],
};

/** `profile` with `tools` added, such as WebFetch for a stage that reads an outside API's docs. */
export function withTools(profile: Permissions, tools: readonly string[]): Permissions {
  return { ...profile, tools: [...(profile.tools ?? []), ...tools] };
}
