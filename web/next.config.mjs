/** Static site published on GitHub Pages under /<repo-name>. */
const base = process.env.BASE_PATH ?? "";
export default {
  output: "export", basePath: base, assetPrefix: base || undefined, images: { unoptimized: true },
  env: { NEXT_PUBLIC_BASE_PATH: base },
};
