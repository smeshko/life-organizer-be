// close-ticket: moves the merged pull request's ticket to Done through `sail port ticket-source update`. It runs after
// the merge, so a move that fails is reported, not fatal: the pull request is already on the base.
import { script, value, z } from 'sail';

export const close = script('close-ticket', {
  run: './run.sh',
  ports: ['ticket-source'],
  consumes: { ticketKey: value(z.string()) },
  output: z.object({ closed: z.boolean(), error: z.string().nullable() }),
  exitCodes: { passed: [0], failed: [] },
});
