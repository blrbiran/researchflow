import assert from 'node:assert/strict';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { ResearchflowPlugin } from '../../.opencode/plugins/researchflow.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const expectedSkillsPath = path.resolve(__dirname, '../../skills');
const plugin = await ResearchflowPlugin({});

const config = {};
await plugin.config(config);
assert.ok(config.skills?.paths?.length, 'skills.paths should be populated');
assert.ok(
  config.skills.paths.some((p) => path.resolve(p) === expectedSkillsPath),
  `skills path should include ${expectedSkillsPath}`
);

const output = {
  messages: [
    {
      info: { role: 'user' },
      parts: [{ type: 'text', text: 'I need help with a paper.' }]
    }
  ]
};

await plugin['experimental.chat.messages.transform']({}, output);
assert.equal(output.messages[0].parts[0].type, 'text');
assert.match(output.messages[0].parts[0].text, /using-researchflow/);
assert.match(output.messages[0].parts[0].text, /literature-discovery/);

console.log('ok - opencode bootstrap injects using-researchflow');
