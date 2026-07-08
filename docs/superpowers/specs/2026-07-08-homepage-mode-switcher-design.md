# Homepage Mode Switcher Design

## Overview
Add a segmented mode toggle inside the homepage chat input that allows users to switch between "Chat" and "Agent" modes before starting a new session.

## Architecture & State
- **State Management**: The selected mode will be preserved in Nuxt's `useState('composer-mode', () => 'chat')`. This ensures the mode persists during the current user session (e.g., navigating to another page and returning to the homepage).
- **Default State**: "chat"
- **API Payload**: The selected mode is injected into the POST body sent to `/api/session` (`{ name: "...", mode: "chat" | "agent" }`).

## Components

### `frontend/app/components/home/Composer.vue`
- Add the `useState` definition to the `<script setup>`.
- In the `<template>`, add a segmented control adjacent to the existing `Paperclip` attachment icon, within the bottom actions row of the composer.
- **Toggle UI**: 
  - Wrapper: `bg-stone-100 dark:bg-stone-800 rounded-lg p-1 flex items-center gap-1`.
  - Mode Buttons: Two options ("Chat", "Agent").
  - Active Button: `bg-white dark:bg-stone-700 shadow-sm text-stone-900 dark:text-stone-100`.
  - Inactive Button: `text-stone-500 dark:text-stone-400 hover:text-stone-700 dark:hover:text-stone-300`.
- **Disabled State**: When `creating` is true, the mode switch buttons will be disabled (opacity reduced, cursor not-allowed) to prevent mode changes mid-submission.

## Error Handling
- The existing error handling in `Composer.vue` remains unchanged. The backend endpoint will process the new `mode` parameter.

## Scope
- This UI change and payload update applies only to the `home/Composer.vue` component. The chat interface within an active session will not feature this mode switcher.
