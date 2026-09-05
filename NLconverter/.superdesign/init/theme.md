# Theme

## globals.css
```css
@import "tailwindcss";

:root {
  /* Main Background - light gray for data density */
  --background: #F8FAFC;
  --foreground: #0F172A;
  
  /* Industrial Palette */
  --sidebar-bg: #0F172A;
  --sidebar-border: #1E293B;
  --accent-primary: #EAB308; /* Neon Yellow */
  --accent-secondary: #14B8A6; /* Teal */
  --status-win: #10B981;
  --status-loss: #F43F5E;
}

@theme inline {
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --font-industrial: var(--font-jetbrains), monospace;
}

body {
  background: var(--background);
  color: var(--foreground);
  font-family: var(--font-inter), sans-serif;
}

h1,
h2,
h3,
h4 {
  font-family: var(--font-inter), sans-serif;
  letter-spacing: -0.02em;
}

@layer components {
  /* Industrial Sidebar */
  .sidebar-item {
    @apply flex items-center gap-3 px-6 py-3 text-sm font-medium text-slate-400 hover:bg-slate-800/50 hover:text-white transition-all duration-200 border-r-2 border-transparent;
  }
  
  .sidebar-item-active {
    @apply bg-slate-800/80 text-yellow-400 border-r-2 border-yellow-400 font-semibold shadow-[inset_4px_0_0_0_rgba(234,179,8,0.1)];
  }

  /* Forms & Inputs */
  .input-field {
    @apply w-full px-3 py-2 bg-white border border-slate-200 rounded-md text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-yellow-400/30 focus:border-yellow-400 transition-all font-industrial;
  }

  .label-text {
    @apply block text-[11px] font-bold text-slate-500 uppercase tracking-widest mb-1.5;
  }

  /* Metric Cards */
  .metric-card {
    @apply bg-white border border-slate-200 rounded-xl p-6 shadow-sm hover:shadow-md hover:border-slate-300 transition-all relative overflow-hidden;
  }

  /* Badges & Indicators */
  .status-badge-win {
    @apply inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-emerald-50 text-emerald-700 text-xs font-industrial font-semibold border border-emerald-200;
  }

  .status-badge-loss {
    @apply inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-rose-50 text-rose-700 text-xs font-industrial font-semibold border border-rose-200;
  }

  /* Original classes preserved with styling tweaks */
  .assumption-box {
    @apply bg-white border border-slate-200 rounded-2xl p-6 md:p-8 shadow-sm mb-4 transition-all hover:shadow-md hover:border-teal-200 relative;
  }

  .ai-badge {
    @apply inline-flex items-center gap-2 px-6 py-3 bg-slate-900 text-yellow-400 rounded-lg text-sm font-bold tracking-wider uppercase shadow-md mb-8 cursor-default transition-transform hover:-translate-y-0.5 hover:shadow-lg font-industrial;
  }

  .radio-group {
    @apply flex flex-wrap gap-3;
  }

  .radio-option {
    @apply relative;
  }

  .radio-label {
    @apply flex items-center gap-3 px-5 py-3 bg-white border border-slate-200 rounded-lg cursor-pointer transition-all hover:bg-slate-50 hover:border-yellow-200;
  }

  .radio-input:checked+.radio-label {
    @apply border-yellow-500 bg-yellow-50/30 text-slate-900 ring-1 ring-yellow-500 shadow-sm;
  }

  .radio-custom-circle {
    @apply w-4 h-4 rounded-full border border-slate-300 flex items-center justify-center transition-all bg-white;
  }

  .radio-input:checked+.radio-label .radio-custom-circle {
    @apply border-yellow-500;
  }

  .radio-inner-dot {
    @apply w-2 h-2 bg-yellow-500 rounded-full scale-0 transition-transform;
  }

  .radio-input:checked+.radio-label .radio-inner-dot {
    @apply scale-100;
  }

  .validation-card {
    @apply bg-teal-50/50 border-l-4 border-teal-500 rounded-r-lg p-4 flex items-center gap-4 transition-all;
  }
}
```

## tailwind config
```js
Error reading: [Errno 2] No such file or directory: 'frontend/tailwind.config.ts'const config = {
  plugins: ["@tailwindcss/postcss"],
};

export default config;

```
