# AI News Hub Frontend

A clean, modern web interface for the AI News application that displays news articles and provides recommendations.

## Features

- **Clean UI**: Modern design with glassmorphism effects and smooth animations
- **News Display**: Shows articles with title, summary, date, source, and up to 3 tags
- **Related Topics**: Each article has a "Related Topics" button that shows recommendations
- **Auto-fetch**: Automatically loads news on app startup
- **Responsive**: Works on desktop and mobile devices
- **Real-time Updates**: Auto-refreshes every 30 minutes

## Setup

**Single Command Setup** - The frontend is now served directly by the FastAPI backend:

1. **Start the Application**:
   ```bash
   cd backend
   python main.py
   ```

2. **Open in Browser**:
   Navigate to `http://localhost:8000`

That's it! The backend serves both the API endpoints and the frontend interface from the same server.

## Usage

### Main Interface
- The app automatically fetches news when it loads
- Articles are displayed in a responsive grid layout
- Each article shows:
  - Title (clickable link to original article)
  - Source and publication date
  - AI-generated summary
  - Up to 3 tags (if available)
  - "Related Topics" button
  - "Read More" link

### Related Topics
- Click the "Related Topics" button on any article
- A modal will open showing similar articles
- Click outside the modal or press Escape to close

### Error Handling
- If the backend is not running, you'll see an error message
- Click "Retry" to attempt fetching news again
- The app will show appropriate loading states

## API Endpoints Used

The frontend uses these two API endpoints:

1. **GET /fetch-news**
   - Fetches the latest processed news articles
   - Called automatically on app startup

2. **GET /recommend-news?article_id={id}&max_results={num}**
   - Gets recommendations for a specific article
   - Called when "Related Topics" button is clicked

## File Structure

```
frontend/
├── index.html      # Main HTML structure
├── styles.css      # CSS styling and responsive design
├── script.js       # JavaScript functionality and API calls
└── README.md       # This file
```

## Browser Compatibility

- Modern browsers (Chrome, Firefox, Safari, Edge)
- Requires JavaScript enabled
- Uses modern CSS features (CSS Grid, Flexbox, backdrop-filter)

## Customization

### Changing API URL
The frontend uses relative URLs by default since it's served from the same server as the API. If you need to use a different API server, edit the `API_BASE_URL` constant in `script.js`:
```javascript
const API_BASE_URL = 'http://your-api-url:port';
```

### Styling
Modify `styles.css` to customize:
- Colors and gradients
- Typography
- Layout and spacing
- Animations and transitions

### Functionality
Edit `script.js` to:
- Change auto-refresh interval
- Modify number of recommendations shown
- Add new features or interactions
