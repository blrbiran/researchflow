import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const skillsDir = path.resolve(__dirname, '../../skills');
let bootstrapCache;

const extractBody = (content) => {
  const match = content.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
  return match ? match[2] : content;
};

const getBootstrap = () => {
  if (bootstrapCache !== undefined) return bootstrapCache;

  const skillPath = path.join(skillsDir, 'using-researchflow', 'SKILL.md');
  if (!fs.existsSync(skillPath)) {
    bootstrapCache = null;
    return null;
  }

  const body = extractBody(fs.readFileSync(skillPath, 'utf8'));
  const toolMapping = `**Tool Mapping for OpenCode:**
- Create or update todos → \`todowrite\`
- Invoke a skill → OpenCode's native \`skill\` tool
- Read files → \`read\`
- Create, edit, or delete files → \`apply_patch\`
- Run shell commands → \`bash\`
- Search files → \`grep\`, \`glob\`
- Fetch a URL → \`webfetch\`
- Dispatch a subagent → \`task\``;

  bootstrapCache = `<EXTREMELY_IMPORTANT>\nYou have researchflow.\n\n**IMPORTANT: The using-researchflow skill content is included below. It is already loaded. Do not use the skill tool to load \"using-researchflow\" again.**\n\n${body}\n\n${toolMapping}\n</EXTREMELY_IMPORTANT>`;
  return bootstrapCache;
};

export const ResearchflowPlugin = async () => ({
  config: async (config) => {
    config.skills = config.skills || {};
    config.skills.paths = config.skills.paths || [];
    if (!config.skills.paths.includes(skillsDir)) {
      config.skills.paths.push(skillsDir);
    }
  },

  'experimental.chat.messages.transform': async (_input, output) => {
    const bootstrap = getBootstrap();
    if (!bootstrap || !output.messages.length) return;

    const firstUser = output.messages.find((m) => m.info.role === 'user');
    if (!firstUser || !firstUser.parts.length) return;
    if (firstUser.parts.some((p) => p.type === 'text' && p.text.includes('EXTREMELY_IMPORTANT'))) return;

    const ref = firstUser.parts[0];
    firstUser.parts.unshift({ ...ref, type: 'text', text: bootstrap });
  }
});
