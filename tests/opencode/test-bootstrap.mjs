import assert from 'node:assert/strict';
import { ResearchflowPlugin } from '../../.opencode/plugins/researchflow.js';

const plugin = await ResearchflowPlugin({});

const config = {};
await plugin.config(config);
assert.ok(config.skills?.paths?.length, 'skills.paths should be populated');
assert.ok(
  config.skills.paths.some((p) => p.endsWith('/reference/researchflow/skills')),
  'skills path should include researchflow/skills'
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
