import {execFileSync} from 'node:child_process';
const python=process.env.GSJ_PYTHON||'python';
execFileSync(python,['scripts/room_model.py'],{stdio:'inherit'});
await import('./apply-verified-capacities.mjs');
await import('./build-seo-expansion.mjs');
execFileSync(python,['scripts/build_v31.py'],{stdio:'inherit'});
