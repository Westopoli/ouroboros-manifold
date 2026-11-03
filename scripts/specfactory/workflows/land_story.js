// H-079: one launch takes a Ready story to landed. Workflow({scriptPath, args: {id: 'H-0NN', channel: 'lab'}}).
// Resume after an ask is answered: Workflow({scriptPath, resumeFromRunId, args: {id, channel, skip: ['build']}}).
// args.skip is an array of stage names already done ('build'). The runtime has no filesystem: every wait (gate, play) is inside the clerk's Bash.
export const meta = {
  name: 'land-story',
  description: 'Ready story to landed on one launch: Build (one builder), Land (one clerk, which also runs the look review)',
  phases: [{ title: 'Build' }, { title: 'Land' }, { title: 'Review' }],
}
const ID = args.id
const CHANNEL = args.channel || 'lab'
const SKIP = args.skip || []
const ROOT = '/home/westopoli/Projects/ouroboros-manifold'
const STORY = ROOT + '/docs/stories/' + ID + '.md'

const BUILD_SCHEMA = {
  type: 'object',
  properties: {
    ok: { type: 'boolean' },
    pushed_sha: { type: 'string' },
    blocked: { type: 'boolean' },
    reason: { type: 'string' },
    test_defect: { type: 'string' },
  },
  required: ['ok', 'pushed_sha', 'blocked', 'reason', 'test_defect'],
}
const LAND_SCHEMA = {
  type: 'object',
  properties: {
    ok: { type: 'boolean' },
    landed: { type: 'string' },
    summary: { type: 'string' },
    played: { type: 'string' },
    worktrees: { type: 'string' },
  },
  required: ['ok', 'landed', 'summary', 'played', 'worktrees'],
}

if (!SKIP.includes('build')) {
  phase('Build')
  const b = await agent(
    'You are a Builder, model claude-sonnet-5-5. Spawn nothing. Think tersely. Read ' + ROOT + '/docs/method/builder.md (your card), then the story file ' + STORY + ', then nothing else unless the story sends you there. ' +
    'Story ' + ID + ', channel ' + CHANNEL + ': branch s/' + ID + '-<slug> from the story. Follow the card: worktree via wt.py new, make the fenced tests green, never edit a test, pre_gate must end PRE_GATE verdict OK, push the branch, wt.py done, stop. ' +
    'STOP rules: a test that looks wrong, a file outside the story list, or a number nobody gave stops you. Report once through StructuredOutput: ' +
    '{ok, pushed_sha, blocked, reason, test_defect}; on a stop set blocked true with the reason, and for a test defect fill test_defect with "test-defect: <id> <line> <contradiction>".',
    { phase: 'Build', label: 'Build ' + ID, model: 'claude-sonnet-5-5', schema: BUILD_SCHEMA })
  if (b.blocked || b.test_defect || !b.ok) {
    return { landed: false, sha: '', blocked: true, stage: 'build', reason: b.test_defect || b.reason || 'builder not ok', played: '', summary: '' }
  }
}

phase('Land')
const c = await agent(
  'You are a landing Clerk, model claude-sonnet-5-5. Read ' + ROOT + '/docs/method/clerk.md (your card) and the story file ' + STORY + '. Land story ' + ID + ' on channel ' + CHANNEL + ' exactly as the card says: gate lock, gate, merge, play, push via land_push.sh, worktree done. ' +
  'Include the look review the card describes when the story has a Scene (spawn the one read-only engineer it allows); put its LOOK OK or LOOK REJECT line in summary. A reject is not landed. ' +
  'Report once through StructuredOutput: {ok, landed (merge sha, empty if not landed), summary, played, worktrees}.',
  { phase: 'Land', label: 'Land ' + ID, model: 'claude-sonnet-5-5', schema: LAND_SCHEMA })

phase('Review')
const lookLine = (c.summary || '').split('\n').find((l) => /LOOK (OK|REJECT)/.test(l)) || ''
if (!c.ok || !c.landed) {
  return { landed: false, sha: '', blocked: true, stage: 'land', reason: c.summary || 'clerk did not land', played: c.played || '', summary: lookLine || c.summary || '' }
}
return { landed: true, sha: c.landed, blocked: false, stage: 'land', reason: '', played: c.played, summary: lookLine || c.summary }
