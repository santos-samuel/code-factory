#!/usr/bin/env node
// validate-jsonc.mjs -- Parse a JSONC file and exit non-zero on syntax errors.
//
// Strips comments and trailing commas in a string-aware way so that // inside
// JSON string values (e.g., "https://example.com") is not mistaken for a line
// comment.
//
// Usage: node validate-jsonc.mjs <file>

import { readFileSync } from "node:fs";

const file = process.argv[2];
if (!file) {
    console.error("usage: validate-jsonc.mjs <file>");
    process.exit(2);
}

const src = readFileSync(file, "utf8");
let out = "";
let inString = false;
let escape = false;

for (let i = 0; i < src.length; i++) {
    const c = src[i];
    const next = src[i + 1];

    if (escape) {
        out += c;
        escape = false;
        continue;
    }

    if (inString) {
        if (c === "\\") {
            out += c;
            escape = true;
            continue;
        }
        if (c === '"') {
            inString = false;
        }
        out += c;
        continue;
    }

    if (c === '"') {
        inString = true;
        out += c;
        continue;
    }

    if (c === "/" && next === "/") {
        while (i < src.length && src[i] !== "\n") i++;
        if (src[i] === "\n") out += "\n";
        continue;
    }

    if (c === "/" && next === "*") {
        i += 2;
        while (i < src.length - 1 && !(src[i] === "*" && src[i + 1] === "/")) i++;
        i++;
        continue;
    }

    out += c;
}

const stripped = out.replace(/,(\s*[}\]])/g, "$1");

try {
    JSON.parse(stripped);
    process.exit(0);
} catch (err) {
    console.error(`${file}: ${err.message}`);
    process.exit(1);
}
