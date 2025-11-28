import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'TAZCOM',
  description: 'Tactical Autonomous Zone Communications - P2P Decentralized Chat',
  
  base: '/tad/',
  
  head: [
    ['link', { rel: 'icon', href: '/tad/favicon.ico' }],
    ['meta', { name: 'theme-color', content: '#3eaf7c' }],
    ['meta', { name: 'apple-mobile-web-app-capable', content: 'yes' }],
    ['meta', { name: 'apple-mobile-web-app-status-bar-style', content: 'black' }]
  ],

  themeConfig: {
    logo: '/logo.svg',
    
    nav: [
      { text: 'Guide', link: '/guide/getting-started' },
      { text: 'Reference', link: '/reference/architecture' },
      { text: 'GitHub', link: 'https://github.com/fabriziosalmi/tad' }
    ],

    sidebar: {
      '/guide/': [
        {
          text: 'Introduction',
          items: [
            { text: 'Getting Started', link: '/guide/getting-started' },
            { text: 'Installation', link: '/guide/installation' },
            { text: 'Quick Start', link: '/guide/quick-start' }
          ]
        },
        {
          text: 'User Guide',
          items: [
            { text: 'Basic Usage', link: '/guide/basic-usage' },
            { text: 'Commands', link: '/guide/commands' },
            { text: 'Channels', link: '/guide/channels' },
            { text: 'Private Channels', link: '/guide/private-channels' },
            { text: 'Export & Import', link: '/guide/export-import' }
          ]
        },
        {
          text: 'Deployment',
          items: [
            { text: 'System-Wide Install', link: '/guide/deployment' },
            { text: 'Running as Service', link: '/guide/service' },
            { text: 'Docker', link: '/guide/docker' },
            { text: 'Raspberry Pi', link: '/guide/raspberry-pi' }
          ]
        },
        {
          text: 'Advanced',
          items: [
            { text: 'Network Configuration', link: '/guide/networking' },
            { text: 'Security Hardening', link: '/guide/security' },
            { text: 'Troubleshooting', link: '/guide/troubleshooting' }
          ]
        }
      ],
      '/reference/': [
        {
          text: 'Technical Reference',
          items: [
            { text: 'Architecture', link: '/reference/architecture' },
            { text: 'Protocol', link: '/reference/protocol' },
            { text: 'Cryptography', link: '/reference/cryptography' },
            { text: 'Database Schema', link: '/reference/database' }
          ]
        },
        {
          text: 'API Documentation',
          items: [
            { text: 'TAZCOMNode', link: '/reference/api-node' },
            { text: 'Discovery', link: '/reference/api-discovery' },
            { text: 'Gossip Protocol', link: '/reference/api-gossip' },
            { text: 'Encryption', link: '/reference/api-encryption' },
            { text: 'Database', link: '/reference/api-database' }
          ]
        },
        {
          text: 'Development',
          items: [
            { text: 'Testing', link: '/reference/testing' },
            { text: 'Contributing', link: '/reference/contributing' },
            { text: 'Changelog', link: '/reference/changelog' }
          ]
        }
      ]
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/fabriziosalmi/tad' }
    ],

    footer: {
      message: 'Released under the MIT License.',
      copyright: 'Copyright © 2024-2025 TAZCOM Contributors'
    },

    search: {
      provider: 'local'
    },

    editLink: {
      pattern: 'https://github.com/fabriziosalmi/tad/edit/main/docs/:path',
      text: 'Edit this page on GitHub'
    },

    lastUpdated: {
      text: 'Updated at',
      formatOptions: {
        dateStyle: 'full',
        timeStyle: 'medium'
      }
    }
  },

  markdown: {
    lineNumbers: true,
    theme: {
      light: 'github-light',
      dark: 'github-dark'
    }
  }
})
