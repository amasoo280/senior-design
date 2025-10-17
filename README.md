# Asset Query Dashboard

A modern React-based dashboard for querying asset and equipment data using natural language. Built with TypeScript, Tailwind CSS, and Vite.

## Features

- **Natural Language Queries**: Ask questions about equipment, locations, status, and deployment duration
- **Real-time Results**: Interactive query results with equipment cards and status indicators
- **Query History**: Keep track of recent queries for easy reference
- **Sample Queries**: Pre-built example queries to get started quickly
- **Responsive Design**: Modern UI that works on desktop and mobile devices
- **Mock Data**: Includes sample data for frontend testing and development

## Tech Stack

- **React 18** with TypeScript
- **Tailwind CSS** for styling
- **Lucide React** for icons
- **Vite** for build tooling and development server
- **ESLint** for code linting

## Getting Started

### Prerequisites

- Node.js (version 16 or higher)
- npm or yarn

### Installation

1. Clone or download this project
2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

4. Open your browser and navigate to `http://localhost:5173`

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Project Structure

```
src/
├── components/
│   └── Dashboard.tsx    # Main dashboard component
├── App.tsx              # Root app component
├── main.tsx            # Application entry point
└── index.css           # Global styles with Tailwind imports
```

## Features Overview

### Query Interface
- Text area for natural language queries
- Enter key to submit queries
- Loading states with spinner animation
- Disabled state when query is empty

### Results Display
- Equipment cards with detailed information
- Status indicators (Active, Maintenance, etc.)
- Location and deployment duration data
- Query summary and timestamp

### Sidebar Components
- **Quick Stats**: Overview of equipment counts and status
- **Sample Queries**: Clickable example queries
- **Recent Queries**: History of previous searches

## Customization

### Adding New Equipment Data
Edit the mock data in `src/components/Dashboard.tsx` around line 35-45:

```typescript
const mockData = {
  query: query,
  timestamp: new Date().toISOString(),
  data: [
    // Add your equipment objects here
  ],
  summary: `Found X pieces of equipment matching your query.`
};
```

### Styling
The project uses Tailwind CSS. You can customize the design by:
- Modifying Tailwind classes in components
- Updating the color scheme in `tailwind.config.js`
- Adding custom CSS in `src/index.css`

### Backend Integration
To connect to a real backend:

1. Replace the mock data section in `executeQuery()` function
2. Uncomment and modify the fetch API call
3. Update the data structure to match your backend response

## Development Notes

- The dashboard currently uses mock data for demonstration
- All queries return the same sample equipment data
- The loading animation simulates a 1.5-second API call
- Query history is stored in component state (not persisted)

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## License

This project is for demonstration purposes.
