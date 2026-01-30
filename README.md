# GitHub Webhook Receiver

A Flask-based webhook receiver that captures GitHub events (PUSH, PULL REQUEST, MERGE) and displays them in a real-time dashboard.

## 🌟 Features

- **Real-time Event Monitoring**: Displays GitHub webhook events as they happen
- **15-Second Polling**: Automatically refreshes data every 15 seconds
- **MongoDB Storage**: Persistent storage with duplicate prevention
- **Premium UI**: Modern, dark-themed dashboard with smooth animations
- **Event Types Supported**:
  - 📤 PUSH events
  - 🔀 PULL REQUEST events
  - 🔗 MERGE events (bonus!)

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- MongoDB Atlas account (free tier works)
- GitHub account

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/Abrar090909/webhook-repo.git
   cd webhook-repo
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Mac/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   
   Create a `.env` file in the root directory:
   ```env
   MONGODB_URI=your_mongodb_connection_string
   SECRET_KEY=your_secret_key
   FLASK_ENV=development
   PORT=5000
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Open in browser**
   
   Navigate to `http://localhost:5000`

## 🌐 Deployment to Render

1. **Push code to GitHub**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Create new Web Service on Render**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure:
     - **Name**: webhook-receiver
     - **Environment**: Python 3
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn app:app`

3. **Add Environment Variables**
   
   In Render dashboard, add:
   - `MONGODB_URI` = Your MongoDB connection string
   - `SECRET_KEY` = Any secure random string
   - `FLASK_ENV` = production

4. **Deploy**
   
   Render will automatically build and deploy your application.
   
   Your webhook URL will be: `https://your-app-name.onrender.com/webhook`

## 📡 API Endpoints

### `POST /webhook`
Receives webhook events from GitHub Actions.

**Request Body:**
```json
{
  "event_type": "push",
  "author": "username",
  "branch": "main",
  "timestamp": "2026-01-30T10:00:00Z",
  "request_id": "unique-id"
}
```

### `GET /api/events`
Returns all events from MongoDB.

**Query Parameters:**
- `since` (optional): ISO 8601 timestamp
- `limit` (optional): Max events to return (default: 50)

**Response:**
```json
{
  "status": "success",
  "count": 10,
  "events": [...],
  "server_time": "2026-01-30T10:00:00Z"
}
```

### `GET /health`
Health check endpoint for monitoring.

## 🗂️ Project Structure

```
webhook-repo/
├── app.py              # Main Flask application
├── config.py           # Configuration management
├── database.py         # MongoDB operations
├── requirements.txt    # Python dependencies
├── Procfile           # Deployment configuration
├── render.yaml        # Render.com config
├── .env               # Environment variables (local)
├── .env.example       # Environment template
├── .gitignore         # Git ignore rules
├── static/
│   ├── css/
│   │   └── style.css  # Premium dark theme
│   └── js/
│       └── app.js     # Frontend logic
└── templates/
    └── index.html     # Dashboard UI
```

## 🔧 Configuration

### MongoDB Schema

```javascript
{
  "_id": ObjectId,
  "event_type": "push" | "pull_request" | "merge",
  "author": String,
  "action": String,
  "from_branch": String,
  "to_branch": String,
  "branch": String,
  "timestamp": ISODate,
  "request_id": String (unique),
  "created_at": ISODate
}
```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `MONGODB_URI` | MongoDB Atlas connection string | Yes |
| `SECRET_KEY` | Flask secret key | Yes |
| `FLASK_ENV` | Environment (development/production) | No |
| `PORT` | Server port | No (default: 5000) |

## 🧪 Testing

### Test Webhook Locally

```bash
curl -X POST http://localhost:5000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "push",
    "author": "testuser",
    "branch": "main",
    "timestamp": "2026-01-30T10:00:00Z",
    "request_id": "test-123"
  }'
```

### Test API Endpoint

```bash
curl http://localhost:5000/api/events
```

## 📚 Related Repositories

- **[action-repo](https://github.com/Abrar090909/action-repo)**: GitHub Actions workflows that trigger webhooks

## 🛠️ Built With

- **Flask** - Python web framework
- **MongoDB Atlas** - Cloud database
- **PyMongo** - MongoDB driver for Python
- **Gunicorn** - WSGI HTTP server
- **Vanilla JavaScript** - Frontend interactivity
- **CSS3** - Premium dark theme styling

## 📝 License

This project is built for the TechStaX Developer Assessment.

## 👤 Author

**Abrar**
- GitHub: [@Abrar090909](https://github.com/Abrar090909)

---

**Note**: Make sure to keep your `.env` file secure and never commit it to version control!
