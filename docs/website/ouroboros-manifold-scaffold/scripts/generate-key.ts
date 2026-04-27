// =============================================================================
// CLI: Generate Access Keys
// Usage: npx tsx scripts/generate-key.ts --type permanent --eras 1980s,roman
//
// Implements: webapp_architecture_1_00.md § Access Key System → Key Generation
// This is the admin-only key generation tool (no web dashboard in v1).
// =============================================================================

import { randomBytes } from "crypto";

// Key generation uses crypto.randomBytes — CSPRNG, not Math.random.
// 16-char alphanumeric = 62^16 ≈ 4.7 × 10^28 possible codes.
const ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
const DEFAULT_KEY_LENGTH = 20;

function generateKeyCode(length: number = DEFAULT_KEY_LENGTH): string {
  const bytes = randomBytes(length);
  let code = "";
  for (let i = 0; i < length; i++) {
    code += ALPHABET[bytes[i] % ALPHABET.length];
  }
  return code;
}

// Parse CLI args
const args = process.argv.slice(2);
const flags: Record<string, string> = {};
for (let i = 0; i < args.length; i += 2) {
  flags[args[i].replace("--", "")] = args[i + 1];
}

const keyType = flags.type || "permanent";
const eras = flags.eras ? flags.eras.split(",") : ["all"];
const count = parseInt(flags.count || "1", 10);
const durationDays = flags.duration ? parseInt(flags.duration, 10) : undefined;
const missionCount = flags.missions ? parseInt(flags.missions, 10) : undefined;

console.log(`\nGenerating ${count} ${keyType} key(s)...\n`);

for (let i = 0; i < count; i++) {
  const code = generateKeyCode();
  console.log(`  ${code}`);

  // In production, this would insert into the database:
  // await prisma.accessKey.create({
  //   data: {
  //     code,
  //     keyType,
  //     scope: { eras },
  //     durationDays,
  //     missionCount,
  //   },
  // });
}

console.log(`\nScope: ${JSON.stringify({ eras })}`);
if (durationDays) console.log(`Duration: ${durationDays} days`);
if (missionCount) console.log(`Missions: ${missionCount}`);
console.log("");
