// node asar.js pack <dir> <out.asar>   |   node asar.js hash <file.asar>
// hash = SHA256 of the archive's header, what Electron checks against Info.plist ElectronAsarIntegrity
const asar = require('@electron/asar'), crypto = require('crypto');
const [cmd, a, b] = process.argv.slice(2);
const hash = f => crypto.createHash('sha256').update(asar.getRawHeader(f).headerString).digest('hex');
if (cmd === 'hash') console.log(hash(a));
else if (cmd === 'pack') asar.createPackageWithOptions(a, b, { unpackDir: 'node_modules/steamworks.js' }).then(() => console.log(hash(b)));
