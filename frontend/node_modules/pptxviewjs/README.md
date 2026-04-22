# PptxViewJS

**PowerPoint presentations, rendered in the browser.**

PptxViewJS is a client-side JavaScript library that parses `.pptx` files and renders slides using HTML5 Canvas — no server, no file uploads, no conversion services required.

👉 **[Product page](https://gptsci.com/pptxviewjs/)** · **[Interactive Demo](https://gptsci.com/pptxviewjs/demos/interactive.html)** · **[All demos](https://gptsci.com/pptxviewjs/demos/)**

---

## 🎮 Interactive Demo — PptxGenJS + PptxViewJS

> **[Try it live →](https://gptsci.com/pptxviewjs/demos/interactive.html)**

The interactive demo showcases the full client-side presentation round-trip:

1. **Generate** — pick a template (charts, tables, shapes, text, full deck) and click **Run**. [PptxGenJS](https://gitbrent.github.io/PptxGenJS/) builds the `.pptx` file entirely in the browser.
2. **Render** — PptxViewJS instantly renders the generated presentation on an HTML5 Canvas.
3. **Download** — save the `.pptx` file at any time.

The live code panel shows the exact PptxGenJS source used to generate each slide. No server involved at any step.

**Available templates:** Bar/Line/Pie/Area charts · Sales & comparison tables · Shapes · Text formatting · Full multi-slide deck (~18 slides)

---

## 🌐 All Demos

| Demo | Description |
|---|---|
| [🎮 Interactive Demo](https://gptsci.com/pptxviewjs/demos/interactive.html) | Generate with PptxGenJS → render with PptxViewJS, live in the browser |
| [📄 Simple Viewer](https://gptsci.com/pptxviewjs/demos/simple.html) | Minimal drag-and-drop viewer — perfect starting point |
| [🖥️ Full Featured UI](https://gptsci.com/pptxviewjs/demos/full.html) | Office Online–style: thumbnails, zoom, fullscreen, keyboard shortcuts |
| [📚 Embedded Layout](https://gptsci.com/pptxviewjs/demos/embedded.html) | Split view with thumbnail sidebar for docs portals and LMS platforms |

---

## 🚀 Features

- ✅ **Zero server dependencies** — all processing runs client-side
- ✅ **Canvas rendering** — pixel-accurate slide display
- ✅ **Charts** — bar, line, pie, area, doughnut via Chart.js (optional peer dep)
- ✅ **Tables** — merged cells, borders, shading, complex headers
- ✅ **Media & SVG** — embedded images and vector graphics
- ✅ **Framework ready** — React, Vue, Svelte, Vite, Electron, Streamlit
- ✅ **TypeScript** — full type definitions included
- ✅ **Multiple formats** — ESM, CJS, and minified UMD builds

## 📦 Installation

Choose your preferred method to install **PptxViewJS**:

### Quick Install (Node-based)

```bash
npm install pptxviewjs
```

```bash
yarn add pptxviewjs
```

### CDN (Browser Usage)

Use the UMD build via [jsDelivr](https://www.jsdelivr.com/package/npm/pptxviewjs). Include JSZip (required) before the library. Include Chart.js (optional) if you need chart rendering:

```html
<!-- Required: JSZip -->
<script src="https://cdn.jsdelivr.net/npm/jszip@3.10.1/dist/jszip.min.js"></script>

<!-- Optional: Chart.js (only if your presentations contain charts) -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>

<!-- PptxViewJS UMD build exposes global `PptxViewJS` -->
<script src="https://cdn.jsdelivr.net/npm/pptxviewjs/dist/PptxViewJS.min.js"></script>
```

> Note: JSZip is required for PPTX (ZIP) parsing. Chart.js is optional and only needed when rendering charts.

### Peer Dependencies (Node/bundlers)

Install JSZip (required). Install Chart.js if your presentations include charts:

```bash
npm install jszip
# Optional (for charts)
npm install chart.js
```

## 🚀 Universal Compatibility

PptxViewJS works seamlessly in **modern web and Node environments**, thanks to dual ESM and CJS builds and zero runtime dependencies. Whether you're building a web app, an Electron viewer, or a presentation platform, the library adapts automatically to your stack.

### Supported Platforms

- **React / Angular / Vue / Vite / Webpack** – just import and go, no config required
- **Electron** – build native presentation viewers with full filesystem access
- **Browser (Vanilla JS)** – embed in web apps with direct file handling
- **Node.js** – experimental; requires a Canvas polyfill (e.g., `canvas`) for rendering
- **Serverless / Edge Functions** – use in AWS Lambda, Vercel, Cloudflare Workers, etc.

### Builds Provided

- **CommonJS**: [`dist/PptxViewJS.cjs.js`](./dist/PptxViewJS.cjs.js)
- **ES Module**: [`dist/PptxViewJS.es.js`](./dist/PptxViewJS.es.js)
- **Minified UMD**: [`dist/PptxViewJS.min.js`](./dist/PptxViewJS.min.js)

## 📖 Documentation

### Quick Start Guide

PptxViewJS presentations are viewed via JavaScript by following 3 basic steps:

#### React/TypeScript

```typescript
import { PPTXViewer } from "pptxviewjs";

// 1. Create a new Viewer
let viewer = new PPTXViewer({
  canvas: document.getElementById('myCanvas')
});

// 2. Load a Presentation
await viewer.loadFile(presentationFile);

// 3. Render the first slide
await viewer.render();
```

#### Script/Web Browser

```html
<canvas id="myCanvas"></canvas>
<input id="pptx-input" type="file" accept=".pptx" />
<button id="prev">Prev</button>
<button id="next">Next</button>
<div id="status"></div>

<script src="PptxViewJS.min.js"></script>
<script>
  const { mountSimpleViewer } = window.PptxViewJS;
  mountSimpleViewer({
    canvas: document.getElementById('myCanvas'),
    fileInput: document.getElementById('pptx-input'),
    prevBtn: document.getElementById('prev'),
    nextBtn: document.getElementById('next'),
    statusEl: document.getElementById('status')
  });
</script>
```

Need finer control? You can still instantiate `new PptxViewJS.PPTXViewer()` manually and use the same APIs shown above.

That's really all there is to it!

## 🎮 Navigation & Interaction

Navigate through presentations with simple, chainable methods:

```javascript
// Navigate through slides
await viewer.nextSlide();        // Go to next slide
await viewer.previousSlide();    // Go to previous slide
await viewer.goToSlide(5);       // Jump to slide 5

// Get information
const currentSlide = viewer.getCurrentSlideIndex();
const totalSlides = viewer.getSlideCount();
```

## 📊 Event System

Listen to presentation events for custom interactions:

```javascript
// Listen to events
viewer.on('loadStart', () => console.log('Loading started...'));
viewer.on('loadComplete', (data) => console.log(`Loaded ${data.slideCount} slides`));
viewer.on('renderComplete', (slideIndex) => console.log(`Rendered slide ${slideIndex}`));
viewer.on('slideChanged', (slideIndex) => console.log(`Now viewing slide ${slideIndex}`));
```


## 🙏 Contributors

Thank you to everyone for the contributions and suggestions! ❤️

Special Thanks:

- [Alex Wong](https://ppt.gptsci.com) - Original author and maintainer
- [gptsci.com](https://gptsci.com) - Project sponsorship and development

## 🌟 Support the Open Source Community

If you find this library useful, consider contributing to open-source projects, or sharing your knowledge on the open social web. Together, we can build free tools and resources that empower everyone.

## 📜 License

Copyright &copy; 2025 [Alex Wong](https://gptsci.com)

[MIT](https://www.npmjs.com/package/pptxviewjs?activeTab=code)
