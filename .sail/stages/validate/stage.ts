// validate: everything is committed, and `scripts/gate.sh` passes: ruff check, ruff format --check, mypy src and the
// unit tests. A failing test that passes when run again is flaky and doesn't fail it; one that fails on the base too
// sets baseRed. Shared: the factory runs it after implement, and review will run it beside its reviewers and after each
// fix.
import { script, z } from 'sail';

export const Validation = z.object({
  ok: z.boolean(),
  /** Paths left uncommitted. */
  uncommitted: z.array(z.string()),
  /** How `scripts/gate.sh` ended. */
  verify: z.object({
    ok: z.boolean(),
    exitCode: z.number().int(),
    /** The gate's steps that failed: `ruff check`, `ruff format`, `mypy`, `pytest`. */
    failedSteps: z.array(z.string()).optional(),
    tail: z.string(),
    /**
     * Each failing test, by its pytest node id (`tests/path/test_file.py::TestClass::test_name`): the change's, flaky
     * (it passed when run again), or the base's (it fails there too).
     */
    failures: z.array(z.object({ test: z.string(), verdict: z.enum(['change', 'flaky', 'base']) })).optional(),
  }),
  /** Every failing test fails on the base too, or is flaky: staging is red, and no change of the branch fixes it. */
  baseRed: z.boolean().optional(),
});

export const validate = script('validate', {
  run: './run.sh',
  output: Validation,
  // The gate takes under a minute; a failure reruns its tests on the branch and the base.
  timeoutSeconds: 1800,
});

/** The tests a validation found failing on the base too, for a run's failure reason. */
export function redTests(validation: z.infer<typeof Validation>): string {
  const red = (validation.verify.failures ?? []).filter((each) => each.verdict === 'base');
  return red.map((each) => each.test).join('; ');
}
