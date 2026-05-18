# CommentFlux - AI Studio Project Documentation

## Project Overview

CommentFlux is a YouTube comment extraction and analysis tool built with **React + TypeScript + Vite**. This project was created in Google AI Studio and downloaded locally.

**IMPORTANT**: This is a **React project**, NOT a Vue.js project.

## Common Issue: `"Vue not recognized`" Error

### Problem
When trying to run the project locally, you may see an error: `vue: command not recognized` or similar.

### Root Cause
This happens when you try to run Vue CLI commands (like `vue serve` or `vue create`) on a React project. The project uses Vite as the build tool, not Vue CLI.

### Solution
Use the correct commands from package.json:
```bash
npm install        # Install dependencies
npm run dev        # Start development server
npm run build      # Build for production
npm run preview    # Preview production build
```

## Tech Stack

### Core Technologies
- **React** 19.2.3 - UI library
- **TypeScript** 5.8.2 - Type-safe JavaScript
- **Vite** 6.2.0 - Build tool and dev server
- **Lucide React** 0.561.0 - Icon library
- **Recharts** 3.6.0 - Data visualization library

### Development Tools
- **@vitejs/plugin-react** - Vite plugin for React
- **@types/node** - Node.js type definitions

## Project Structure

```
commentflux/
|-- components/
|   |-- ui/
|   |   `-- Badge.tsx           # Reusable badge component
|   |-- ConfigPanel.tsx         # Configuration panel for settings
|   |-- Dashboard.tsx           # Main dashboard with results
|   `-- Icons.tsx               # Icon components
|-- services/
|   `-- mockService.ts          # Mock service for fetching comments
|-- .env.local                  # Environment variables (API keys)
|-- .gitignore                  # Git ignore rules
|-- App.tsx                     # Main application component
|-- constants.ts                # Application constants
|-- index.html                  # HTML entry point
|-- index.tsx                   # React entry point
|-- metadata.json               # Project metadata
|-- package.json                # Dependencies and scripts
|-- README.md                   # Project documentation
|-- tsconfig.json               # TypeScript configuration
`-- types.ts                    # TypeScript type definitions
```

## Key Components

### App.tsx (Main Application)
- **Purpose**: Root component managing application state and flow
- **State Management**:
  - `url`: YouTube URL input
  - `enableClassification`: Toggle for sentiment analysis
  - `exportFormat`: JSON or CSV export format
  - `processingState`: Loading/error/complete states
  - `results`: Comment data and statistics
- **Key Functions**:
  - `handleProcess()`: Fetches and processes comments
  - `handleDownload()`: Exports data in selected format
  - `handleReset()`: Resets application state

### types.ts (Type Definitions)
```typescript
enum ClassificationStatus {
  Unclassified, Positive, Negative, Neutral, Spam
}

interface Comment {
  id, author, text, timestamp, likes
  classification?, confidence?
}

interface AnalysisStats {
  total, positive, negative, neutral, spam
}

type ExportFormat = `"JSON`" | `"CSV`"

interface ProcessingState {
  status: `"IDLE`" | `"LOADING`" | `"COMPLETE`" | `"ERROR`"
  error?, progress?
}
```

### Components
1. **ConfigPanel.tsx**: Configuration options panel
   - Enable/disable classification
   - Select export format

2. **Dashboard.tsx**: Results visualization
   - Display comments
   - Show statistics
   - Export functionality

3. **Icons.tsx**: Custom icon components
   - IconYoutube, IconSearch, IconTerminal

4. **ui/Badge.tsx**: Reusable badge component

### Services
- **mockService.ts**: Mock service for fetching YouTube comments
  - `fetchComments()`: Simulates API call to fetch comments
  - `downloadData()`: Handles data export

## Setup Instructions

### Prerequisites
- Node.js (latest LTS version recommended)
- npm or yarn package manager

### Installation Steps

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Configure API Key**:
   - Open `.env.local`
   - Replace `PLACEHOLDER_API_KEY` with your actual Gemini API key:
     ```
     GEMINI_API_KEY=your_actual_api_key_here
     ```

3. **Run development server**:
   ```bash
   npm run dev
   ```

4. **Access the app**:
   - Open browser to `http://localhost:5173` (or the port shown in terminal)

### Production Build
```bash
npm run build      # Creates optimized build in dist/
npm run preview    # Preview production build locally
```

## Features

1. **YouTube Comment Extraction**
   - Paste YouTube URL
   - Extract all comments from video

2. **Sentiment Classification** (Optional)
   - Classify comments as Positive, Negative, Neutral, or Spam
   - Powered by Gemini API
   - Confidence scores for classifications

3. **Data Export**
   - Export to JSON or CSV format
   - Download processed data locally

4. **Analytics Dashboard**
   - View comment statistics
   - Visualize sentiment distribution
   - Review individual comments with classifications

## Design System

### Color Palette
- **void**: Background color (dark)
- **surface**: Surface color (slightly lighter)
- **subtle**: Border/divider color
- **acid**: Accent color (bright green/yellow)
- **lavender**: Secondary accent

### Typography
- Sans-serif font family
- Monospace for code/technical elements

## Environment Variables

- `GEMINI_API_KEY`: API key for Google Gemini AI (required for classification)

## Common Development Tasks

### Adding a New Component
1. Create file in `components/` directory
2. Use TypeScript with proper typing
3. Import types from `types.ts`
4. Follow existing component patterns

### Modifying Data Processing
1. Update `services/mockService.ts`
2. Adjust types in `types.ts` if needed
3. Update component props/state accordingly

### Styling
- Uses Tailwind-like utility classes
- Custom CSS variables for colors
- Responsive design with mobile-first approach

## Troubleshooting

### `"Vue not recognized`" Error
- **Cause**: Trying to use Vue CLI commands on a React project
- **Fix**: Use `npm run dev` instead of `vue serve`

### Port Already in Use
- **Cause**: Another process using port 5173
- **Fix**: Kill the process or Vite will auto-select another port

### API Key Issues
- **Cause**: Missing or invalid Gemini API key
- **Fix**: Ensure `.env.local` has valid `GEMINI_API_KEY`

### Build Errors
- **Cause**: Outdated dependencies or TypeScript errors
- **Fix**: Run `npm install` again, check TypeScript errors

## AI Studio Integration

This project was created in Google AI Studio:
- View app: https://ai.studio/apps/drive/1iBGJgrEzVjXn9g7_8UjQB3D-Sb5Otwst
- Uses Gemini API for sentiment classification
- Can be deployed back to AI Studio or hosted independently

## Next Steps for Development

1. **Replace Mock Service**: Implement actual YouTube API integration
2. **Add Authentication**: Secure API key usage
3. **Enhance Analytics**: Add more visualization options
4. **Add Filters**: Filter comments by sentiment, date, likes
5. **Batch Processing**: Handle multiple videos at once
6. **Real-time Updates**: Live comment streaming

## Version History

- **v1.0.0-beta**: Initial release
  - Basic comment extraction
  - Sentiment classification
  - JSON/CSV export
  - Dashboard visualization

---

**Last Updated**: 2025-12-28
**Project Type**: React + TypeScript + Vite
**Framework**: NOT Vue.js (this is a common confusion)
