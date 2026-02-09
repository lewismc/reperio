# Reperio Frontend

React-based web interface for visualizing Apache Nutch graph data using Sigma.js.

## Development

### Prerequisites

- Node.js 18+
- npm or yarn

### Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Environment Variables

Create `.env` file in the frontend directory:

```bash
VITE_API_URL=http://localhost:8000
```

## Architecture

```
src/
├── components/         # React components
│   ├── DataLoader.jsx  # Data loading interface
│   ├── GraphViewer.jsx # Sigma.js graph visualization
│   └── ControlPanel.jsx # Graph controls and filters
├── api/               # API client
│   └── client.js      # Axios-based API wrapper
├── store/             # State management
│   └── graphStore.js  # Zustand store for graph state
├── App.jsx            # Main application component
└── main.jsx           # Entry point
```

## Features

- **Interactive Graph Visualization**: Powered by Sigma.js with WebGL rendering
- **Data Loading**: Support for local and HDFS data sources
- **Real-time Search**: Find nodes by URL pattern
- **Graph Analysis**: PageRank, centrality, components
- **Export**: Download graph data in various formats
- **Responsive UI**: Works on desktop and tablet devices

## Components

### DataLoader

Form for loading Nutch data from local filesystem or HDFS.

**Props:**
- `onClose`: Callback when loader is closed

### GraphViewer

Main graph visualization component using Sigma.js.

**Features:**
- Pan and zoom
- Click nodes for details
- Automatic layout
- Status-based coloring

### ControlPanel

Sidebar with controls for graph manipulation.

**Features:**
- Search nodes
- Run analysis (PageRank, centrality, components)
- Export graph
- View statistics

## State Management

Uses Zustand for state management with the following store:

```javascript
{
  graphData: null,      // Current graph data
  metadata: null,       // Graph metadata (node/edge counts)
  isLoading: false,     // Loading state
  error: null,          // Error message
  filters: {...}        // Active filters
}
```

## API Integration

All API calls go through `src/api/client.js`:

```javascript
import { api } from './api/client'

// Load graph
await api.loadGraph(path, dbType, storage)

// Get graph data
const data = await api.getGraphData(maxNodes, format)

// Run analysis
const results = await api.analyzeGraph('pagerank')
```

## Styling

- CSS Modules for component styles
- Dark theme by default
- Responsive design

## Performance

- Lazy loading of large graphs
- Progressive rendering with Sigma.js
- Optimized for 100k+ nodes using WebGL

## Testing

```bash
# Run tests (when implemented)
npm test
```

## Build

```bash
# Production build
npm run build

# Output in dist/
# Deploy dist/ folder to web server
```

## Deployment

### Static Hosting

Deploy `dist/` folder to:
- Nginx
- Apache
- Netlify
- Vercel
- AWS S3 + CloudFront

### Nginx Configuration

```nginx
server {
    listen 80;
    root /var/www/reperio;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
    }
}
```

## Contributing

See main project CONTRIBUTING.md for guidelines.

## License

Apache License 2.0 - See LICENSE file in project root.
