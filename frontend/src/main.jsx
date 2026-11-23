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

// The API serialises one description; the kit's cards expect a bilingual pair.
const toKitPlace = (place) => ({
  ...place,
  desc: place.desc || { id: place.description || '', en: place.description || '' },
})

async function loadCatalogue() {
  const base = window.__API__
  try {
    const [placesRes, metaRes] = await Promise.all([
      fetch(`${base}/api/places?limit=4000&sort=rating`),
      fetch(`${base}/api/meta`),
    ])
    if (!placesRes.ok || !metaRes.ok) throw new Error('api')

    const [places, meta] = await Promise.all([placesRes.json(), metaRes.json()])
    if (!places.items || !places.items.length) throw new Error('empty')

    window.JJ.PLACES = places.items.map(toKitPlace)
    window.JJ.TOTAL = places.total
    window.JJ.OFFLINE = false

    // Counts come from the dataset, never from a number typed into the markup.
    const categoryCounts = new Map(meta.categories.map((c) => [c.name, c.count]))
    window.JJ.CATEGORIES = window.JJ.CATEGORIES.map((category) => ({
      ...category,
      count: categoryCounts.get(category.id) ?? 0,
    })).filter((category) => category.count > 0)

    const regencyCounts = new Map(meta.regencies.map((r) => [r.name, r.count]))
    window.JJ.REGENCIES = window.JJ.REGENCIES.map((regency) => ({
      ...regency,
      count: regencyCounts.get(regency.name) ?? 0,
    }))
  } catch (err) {
    // Keep the curated sample so the site still works, but say so in the UI.
    // Counts are recomputed from the sample rather than left at their old
    // hardcoded values, so the page never quotes a catalogue it cannot see.
    window.JJ.OFFLINE = true
    window.JJ.TOTAL = null
    window.JJ.CATEGORIES = window.JJ.CATEGORIES.map((category) => ({
      ...category,
      count: window.JJ.PLACES.filter((p) => p.category === category.id).length,
    })).filter((category) => category.count > 0)
    window.JJ.REGENCIES = window.JJ.REGENCIES.map((regency) => ({
      ...regency,
      count: window.JJ.PLACES.filter((p) => p.regency === regency.name).length,
    }))
    console.warn('YOGA API offline — showing the built-in sample instead.', err)
  }
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

  // Replace the curated sample with the real catalogue + counts from the API.
  // If the API is offline the kit keeps working on its sample data.
  await loadCatalogue()

  await import('./kit/app.jsx')          // mounts into #app
}

boot()
