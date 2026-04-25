const icons = require('fs').readFileSync('icons.txt', 'utf8').trim().split('\n');
let html = require('fs').readFileSync('index.html', 'utf8');
html = html.replace(/const icons = \[[\s\S]*?\];/, `const icons = ${JSON.stringify(icons)};`);
require('fs').writeFileSync('index.html', html);