/** Static site published on GitHub Pages under /<repo-name>. */
const base = process.env.BASE_PATH ?? "";
module.exports = { output: "export", basePath: base, assetPrefix: base || undefined, images: { unoptimized: true } };
