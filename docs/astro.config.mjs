// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import rehypeExternalLinks from 'rehype-external-links';

// https://astro.build/config
export default defineConfig({
	integrations: [
		starlight({
			title: 'AssoCORE',
			customCss: [
				'./src/styles/custom.css',
			],
			social: [
				{ icon: 'github', label: 'GitHub', href: 'https://github.com/AssoCORE/AssoCORE' }
			],
			sidebar: [
				{
					label: 'Getting Started',
					autogenerate: { directory: 'getting-started' },
				},
				{
					label: 'Guides',
					items: [
						{ label: 'Overview', slug: 'guides' },
						{
							label: 'Tutorials',
							autogenerate: { directory: 'guides/tutorials' },
						},
						{
							label: 'How-To Guides',
							autogenerate: { directory: 'guides/how-to' },
						},
					],
				},
				{
					label: 'Reference',
					items: [
						{ label: 'Overview', slug: 'reference' },
						{
							label: 'API',
							autogenerate: { directory: 'reference/api' },
						},
						{
							label: 'Configuration',
							autogenerate: { directory: 'reference/configuration' },
						},
					],
				},
				{
					label: 'Architecture',
					autogenerate: { directory: 'architecture' },
				},
				{
					label: 'Proof of Concepts',
					autogenerate: { directory: 'pocs' },
				},
				{
					label: 'Studies',
					items: [
						{ label: 'Overview', slug: 'studies' },
						{
							label: 'Comparative Studies',
							autogenerate: { directory: 'studies/comparative' },
						},
						{
							label: 'Field Studies',
							autogenerate: { directory: 'studies/field' },
						},
					],
				},
				{
					label: 'Case Studies',
					autogenerate: { directory: 'case-studies' },
				},
				{
					label: 'Legal',
					autogenerate: { directory: 'legal' },
				},
				{
					label: 'Contributing',
					autogenerate: { directory: 'contributing' },
				},
			],
		}),
	],
	markdown: {
		rehypePlugins: [
			[
				rehypeExternalLinks,
				{
					target: '_blank',
					rel: ['noopener', 'noreferrer']
				}
			],
		],
	},
});
