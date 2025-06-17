# TravelMAX - AI-Powered Trip Planner

An intelligent trip planning application that creates personalized itineraries based on your interests and duration of stay.

## Features

- Multi-day trip planning (1-10 days)
- Personalized itineraries based on interests
- Detailed activity scheduling
- Restaurant and attraction recommendations
- Downloadable itineraries
- Interactive UI

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd TravelMAX
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory and add your Groq API key:
```
GROQ_API_KEY=your_api_key_here
```

4. Run the application locally:
```bash
streamlit run app.py
```

## Deployment

The application is configured to be deployed on Streamlit Cloud or similar platforms.

### Streamlit Cloud Deployment

1. Push your code to a GitHub repository
2. Go to [Streamlit Cloud](https://streamlit.io/cloud)
3. Create a new app
4. Select your repository and set the main file path to `app.py`
5. Add your environment variables (GROQ_API_KEY) in the Streamlit Cloud dashboard
6. Deploy!

### Environment Variables

Make sure to set the following environment variables in your deployment platform:
- `GROQ_API_KEY`: Your Groq API key

## Project Structure

```
TravelMAX/
├── app.py              # Main Streamlit application
├── main.py            # Core trip planning logic
├── requirements.txt   # Project dependencies
├── Procfile          # Deployment configuration
├── .env              # Environment variables (not tracked in git)
└── .gitignore        # Git ignore rules
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 