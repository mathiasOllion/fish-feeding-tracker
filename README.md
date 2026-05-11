# Fish Feeding Tracker

A responsive web application to track daily fish feeding activities in aquariums or fish ponds. Manage multiple fish locations, track pellet consumption per fish, and visualize feeding patterns with interactive dashboards.

## Features

- **User Authentication**: Secure registration and login system
- **Location Management**: Create and manage multiple aquarium/pond locations with descriptions and images
- **Fish Profiles**: Add individual fish with names, descriptions, and photos
- **Daily Tracking**: Log pellet counts for each fish with date navigation
- **Dashboard Analytics**: Visualize feeding patterns with interactive charts
- **Account Management**: Update username and password
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- **Persistent Storage**: SQLite database with Docker volume support

## Tech Stack

- **Backend**: Flask 3.0 (Python)
- **Frontend**: HTML5, CSS3, JavaScript (vanilla)
- **Database**: SQLite
- **Containerization**: Docker & Docker Compose
- **Charts**: Chart.js
- **Security**: Werkzeug (password hashing)

## Prerequisites

- Docker & Docker Compose
- Or Python 3.12+ with pip

## Quick Start with Docker

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/fish-feeding-tracker.git
cd fish-feeding-tracker
```

### 2. Build and Deploy

```bash
docker compose up --build -d
```

The application will be available at `http://localhost:5000`

### 3. Access the Application

- Navigate to `http://localhost:5000`
- Register a new account
- Set up your first location and add fish
- Start tracking daily feeding

## Local Development

### 1. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Initialize Database

```bash
python -c "from app import app, init_db; app.app_context().push(); init_db()"
```

### 3. Run Development Server

```bash
python app.py
```

Server will run on `http://localhost:5000`

## Project Structure

```
fish-feeding-tracker/
├── app.py                    # Main Flask application
├── schema.sql                # Database schema
├── requirements.txt          # Python dependencies
├── Dockerfile                # Docker container configuration
├── docker-compose.yml        # Docker Compose orchestration
├── static/
│   ├── css/style.css         # Responsive styling
│   ├── js/app.js             # Frontend interactivity
│   ├── default-fish.svg      # Default fish image
│   └── default-location.svg  # Default location image
├── templates/
│   ├── base.html             # Base template with navigation
│   ├── login.html            # Login page
│   ├── register.html         # Registration page
│   ├── setup.html            # Initial location/fish setup
│   ├── tracker.html          # Daily feeding tracker
│   ├── dashboard.html        # Analytics dashboard
│   ├── account.html          # Account settings
│   └── locations.html        # Location & fish management
└── data/                     # Persistent storage (Docker volume)
    ├── tracker.db            # SQLite database
    └── uploads/              # Fish and location images
```

## Usage

### 1. Register & Login

Create a new account with a username and password, then log in to access the tracker.

### 2. Set Up Location

On first login, you'll be prompted to:
- Enter a location name (e.g., "Main Tank")
- Optionally add a description and image
- Specify the number of fish
- Name each fish and optionally upload photos

### 3. Track Daily Feeding

- Navigate to the **Tracker** page
- Use the date navigator to select a specific date
- Click `+` and `-` buttons to adjust pellet count for each fish
- Or click on the fish image to increment the count
- Click **Save** to store the feeding log

### 4. Manage Locations & Fish

- Go to **Location** page to update location details and fish information
- Click **Add fish** to add new fish to an existing location
- Upload new images for locations or individual fish

### 5. View Analytics

- Visit the **Dashboard** page to see:
  - Historical feeding trends
  - Per-fish consumption charts
  - Daily/weekly comparisons

### 6. Manage Account

- Update username and password in the **Account** page

## Database Schema

### Users
- `id`: Unique identifier
- `username`: Unique username
- `password_hash`: Hashed password

### Locations
- `id`: Unique identifier
- `user_id`: Reference to user
- `name`: Location name (e.g., "Tank A")
- `fish_count`: Number of fish
- `description`: Optional location description
- `image_filename`: Optional location image

### Fish
- `id`: Unique identifier
- `location_id`: Reference to location
- `name`: Fish name
- `description`: Optional fish description
- `image_filename`: Optional fish image

### Food Logs
- `id`: Unique identifier
- `fish_id`: Reference to fish
- `date`: Date of feeding (ISO format)
- `pellets`: Number of pellets fed
- Unique constraint on (fish_id, date)

## Docker Volumes

The application uses a named volume `tracker-data` to persist:
- SQLite database (`tracker.db`)
- Uploaded images (`uploads/`)

### View Persisted Data

```bash
# Check volume details
docker volume inspect fft_tracker-data

# Access the data directory (inside container)
docker exec fft-app-1 ls /app/data
```

### Remove Volume (Reset Data)

```bash
docker compose down -v
```

## Environment Variables

Set in `docker-compose.yml` or as environment variables:

- `SECRET_KEY`: Flask session secret (default: "change-me-to-a-secret") — **Change in production**
- `FLASK_APP`: Entry point (default: "app.py")
- `FLASK_ENV`: Environment mode (default: "production")

## Production Deployment

### Security Recommendations

1. **Set a Strong SECRET_KEY**

```bash
export SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
```

2. **Use a Production WSGI Server**

Replace Flask's development server with Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

3. **Enable HTTPS**

Use a reverse proxy (nginx, Traefik) with SSL certificates.

4. **Database Backups**

Regularly backup the `tracker.db` file from the Docker volume.

## Troubleshooting

### App won't start
Check logs with:
```bash
docker compose logs app
```

### Database errors
Ensure the volume is mounted correctly:
```bash
docker compose ps
docker volume ls
```

### Images not loading
Verify the `uploads/` directory exists:
```bash
docker exec fft-app-1 ls -la /app/data/uploads
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

## License

MIT License — see [LICENSE](LICENSE) file for details.

## Support

For issues or questions, please open an issue on GitHub or contact the maintainers.

---

**Built with ❤️ for aquarium enthusiasts**

The database file `tracker.db` will be created automatically when the app first runs.
