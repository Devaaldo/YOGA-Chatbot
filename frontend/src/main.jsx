/* Jelajah Jogja — Vite entry point.
 *
 * The UI kit (src/kit/*) was authored as global-IIFE modules that expect
 * `React`, `ReactDOM`, `window.JJUI`, `window.JJSCREENS`, `window.JJ` and
 * `window.__resources` to exist. We provide those globals first, then import
 * the kit files in order for their side effects, fetch real places from the
 * YOGA backend, and finally mount the app.
 */
import React from 'react'
import * as ReactDOMClient from 'react-dom/client'
import * as ReactDOMFull from 'react-dom'

// Design-system + kit styles (Vite bundles these and their @imports/url()).
import './styles/styles.css'
import './styles/kit.css'
import './styles/kit-screens.css'
import './styles/chatpage.css'
import './styles/meetyoga.css'

// --- Provide the globals the kit expects -----------------------------------
window.React = React
window.ReactDOM = { ...ReactDOMFull, ...ReactDOMClient }
window.__API__ = import.meta.env.VITE_API_URL || 'http://localhost:8000'
window.__resources = {
  jjMark: '/assets/logo/jj-mark.svg',
  jjMarkBadge: '/assets/logo/jj-mark-badge.svg',
  yogaAvatar: '/assets/logo/yoga-avatar.svg',
}

async function boot() {
  // Order matters: data + primitives + screens + chat must register on window
  // before the app shell (which reads them) is imported and mounted.
  await import('./kit/places.js')        // -> window.JJ (structure + sample fallback)
  await import('./kit/ui.jsx')           // -> window.JJUI
  await import('./kit/screen-home.jsx')
  await import('./kit/screen-explore.jsx')
  await import('./kit/screen-detail.jsx')
  await import('./kit/screen-planner.jsx')
  await import('./kit/screen-regency.jsx')
  await import('./kit/screen-about.jsx')
  await import('./kit/chat.jsx')         // -> window.JJSCREENS.ChatPanel

  // Replace the ~20 curated sample places with the real 3,399 from the backend.
  // If the API is offline the kit keeps working on its sample data.
  try {
    const res = await fetch(window.__API__ + '/api/places?limit=2000&sort=rating')
    if (res.ok) {
      const data = await res.json()
      if (data.items && data.items.length) window.JJ.PLACES = data.items
    }
  } catch (err) {
    console.warn('YOGA API offline — using built-in sample data.', err)
  }

  await import('./kit/app.jsx')          // mounts into #app
}

boot()
