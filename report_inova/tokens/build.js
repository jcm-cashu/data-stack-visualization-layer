/**
 * Style Dictionary build script.
 *
 * Reads the W3C DTCG design tokens from ../design_tokens.json and outputs:
 *   dist/css/variables.css   – CSS custom properties
 *   dist/python/tokens.py    – Python dict (can be imported by shared/styles.py)
 *
 * Usage:
 *   cd tokens && npm install && npm run build
 *
 * Figma integration loop:
 *   Figma Variables -> Tokens Studio plugin -> design_tokens.json -> npm run build -> CSS / Python
 */
const StyleDictionary = require("style-dictionary");

const sd = new StyleDictionary({
  source: ["../design_tokens.json"],
  platforms: {
    css: {
      transformGroup: "css",
      buildPath: "dist/css/",
      files: [
        {
          destination: "variables.css",
          format: "css/variables",
          options: {
            outputReferences: true,
          },
        },
      ],
    },
    python: {
      transformGroup: "js",
      buildPath: "dist/python/",
      files: [
        {
          destination: "tokens.json",
          format: "json/flat",
        },
      ],
    },
  },
});

sd.buildAllPlatforms();
