// @ts-check
import { defineConfig } from "astro/config";
import starlight from "@astrojs/starlight";
import rehypeExternalLinks from "rehype-external-links";

// https://astro.build/config
export default defineConfig({
  integrations: [
    starlight({
      title: "AssoCORE",
      customCss: ["./src/styles/custom.css"],
      social: [
        {
          icon: "github",
          label: "GitHub",
          href: "https://github.com/AssoCORE/AssoCORE",
        },
      ],
      sidebar: [
        {
          label: "Getting Started",
          autogenerate: { directory: "getting-started" },
        },
        {
          label: "Guides",
          autogenerate: { directory: "guides" },
        },
        {
          label: "Reference",
          autogenerate: { directory: "reference" },
        },
        {
          label: "Architecture",
          autogenerate: { directory: "architecture" },
        },
        {
          label: "Proof of Concepts",
          autogenerate: { directory: "pocs" },
        },
        {
          label: "Studies",
          items: [
            { label: "Overview", slug: "studies" },
            {
              label: "Comparative Studies",
              autogenerate: { directory: "studies/comparative" },
            },
            {
              label: "Field Studies",
              autogenerate: { directory: "studies/field" },
            },
          ],
        },
        {
          label: "Case Studies",
          autogenerate: { directory: "case-studies" },
        },
        {
          label: "Legal",
          autogenerate: { directory: "legal" },
        },
        {
          label: "Contributing",
          autogenerate: { directory: "contributing" },
        },
      ],
    }),
  ],
  markdown: {
    rehypePlugins: [
      [
        rehypeExternalLinks,
        {
          target: "_blank",
          rel: ["noopener", "noreferrer"],
        },
      ],
    ],
  },
});
