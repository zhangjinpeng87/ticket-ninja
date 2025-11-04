import React from 'react';
import ReactDOM from 'react-dom/client';
import { App } from './App';

function init() {
  const rootElement = document.getElementById('root');
  if (!rootElement) {
    console.error('Root element not found, retrying...');
    setTimeout(init, 100);
    return;
  }

  try {
    ReactDOM.createRoot(rootElement).render(
      <React.StrictMode>
        <App />
      </React.StrictMode>
    );
  } catch (error) {
    console.error('Failed to render app:', error);
    if (rootElement) {
      rootElement.innerHTML = `
        <div style="padding: 20px; color: red;">
          <h2>Error Loading App</h2>
          <p>${error instanceof Error ? error.message : String(error)}</p>
          <p>Check the browser console for more details.</p>
        </div>
      `;
    }
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
