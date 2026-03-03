/**
 * build_crossrefs.js
 * Merges all 5 cross-reference data files into a single crossrefs_all.js
 * Run: node build_crossrefs.js
 */
const fs = require('fs');
const path = require('path');

const SRC = path.join(__dirname, '..', 'Standard Works Project');
const OUT = path.join(__dirname, 'crossrefs_all.js');

// Simulate browser environment for the data files
const window = {};

// Load each data file
function loadDataFile(filePath, varName) {
  const code = fs.readFileSync(filePath, 'utf-8');
  // Extract the JSON object from the assignment
  const match = code.match(new RegExp(varName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\s*=\\s*'));
  if (!match) {
    console.error('Could not find', varName, 'in', filePath);
    return {};
  }
  const startIdx = match.index + match[0].length;
  // Use Function constructor to evaluate safely
  const fn = new Function('window', code + '\nreturn ' + varName + ';');
  return fn(window);
}

console.log('Loading cross-reference data files...');

const otData = loadDataFile(path.join(SRC, 'ot_crossrefs.js'), 'window._otCrossrefsData');
console.log('  OT:', Object.keys(otData).length, 'verses');

const ntData = loadDataFile(path.join(SRC, 'nt_crossrefs.js'), 'window._ntCrossrefsData');
console.log('  NT:', Object.keys(ntData).length, 'verses');

const bomData = loadDataFile(path.join(SRC, 'bom', 'crossrefs.js'), 'window._crossrefsData');
console.log('  BOM:', Object.keys(bomData).length, 'verses');

const dcData = loadDataFile(path.join(SRC, 'dc_crossrefs.js'), 'window._dcCrossrefsData');
console.log('  D&C:', Object.keys(dcData).length, 'verses');

const pgpData = loadDataFile(path.join(SRC, 'pgp_crossrefs.js'), 'window._pgpCrossrefsData');
console.log('  PGP:', Object.keys(pgpData).length, 'verses');

// Merge all into one object
const merged = Object.assign({}, otData, ntData, bomData, dcData, pgpData);
const totalVerses = Object.keys(merged).length;
console.log('\nTotal merged verses:', totalVerses);

// Write output
const output = 'window._volumeCrossrefsData = ' + JSON.stringify(merged) + ';\n';
fs.writeFileSync(OUT, output, 'utf-8');
console.log('Written to', OUT, '(' + (output.length / 1024 / 1024).toFixed(1) + ' MB)');
