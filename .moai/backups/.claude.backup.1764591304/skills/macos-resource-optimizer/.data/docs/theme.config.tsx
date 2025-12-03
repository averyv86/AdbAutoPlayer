import React from 'react'
import { DocsThemeConfig } from 'nextra-theme-docs'

const config: DocsThemeConfig = {
  logo: (
    <span style={{ fontWeight: 'bold', fontSize: '1.2em' }}>
      macOS Resource Optimizer v7.0
    </span>
  ),

  project: {
    link: 'https://github.com/moai-adk/macos-resource-optimizer'
  },

  docsRepositoryBase: 'https://github.com/moai-adk/macos-resource-optimizer/tree/main/.claude/skills/macos-resource-optimizer/.data/docs',

  footer: {
    text: 'macOS Resource Optimizer v7.0 - MoAI-ADK Integration'
  },

  navigation: {
    prev: true,
    next: true
  },

  toc: {
    float: true,
    title: 'On This Page'
  },

  search: {
    placeholder: 'Search documentation...'
  },

  head: (
    <>
      <meta name="description" content="Professional macOS resource optimization with MoAI-ADK integration" />
      <meta name="og:title" content="macOS Resource Optimizer v7.0" />
      <meta name="og:description" content="Enterprise-grade macOS resource optimization with MoAI-ADK integration" />
    </>
  ),

  useNextSeoProps() {
    return {
      titleTemplate: '%s – macOS Resource Optimizer'
    }
  }
}

export default config
