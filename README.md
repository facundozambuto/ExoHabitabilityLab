# ExoHabitabilityLab
Exploring worlds where life could emerge – habitability scoring for exoplanets using NASA &amp; ESA open data 


# 🌌 ExoHabitabilityLab  
**Exploring worlds where life could emerge**

ExoHabitabilityLab is an open-source scientific application that analyzes real exoplanet data from NASA and ESA to estimate the potential habitability of planets beyond our Solar System.

The project combines astrophysics, open data and software engineering to create an educational and exploratory platform for space enthusiasts, researchers and developers.

---

## 🚀 Project Overview

The goal of ExoHabitabilityLab is to:

- Fetch and process real exoplanet datasets  
- Compute a heuristic **habitability score**
- Provide scientific explanations for each result  
- Offer a modern API and web interface to explore other worlds  

This is not a life-detection tool, but a platform to explore **which planets might be better candidates for further study**.

---

## 🧪 Features (MVP)

- REST API built with **FastAPI**
- Integration with:
  - NASA Exoplanet Archive
  - ESA open datasets
- Scientific scoring model based on:
  - Stellar type  
  - Planet radius  
  - Equilibrium temperature  
- JSON responses with:
  - Final score  
  - Factor breakdown  
  - Explanatory reasoning  

---

## 🛠 Tech Stack

- Python 3.11+
- FastAPI  
- Pydantic  
- Astropy  
- SQLAlchemy (async)
- SQLite (MVP database)
- Uvicorn  

---

## 📁 Project Structure

app/
├── main.py
├── api/
│ ├── routes/
│ └── deps.py
├── core/
├── models/
├── schemas/
├── services/
│ ├── nasa.py
│ ├── esa.py
│ └── scoring/
└── utils/


---

## 🔧 Installation

```bash
git clone https://github.com/facundozambuto/ExoHabitabilityLab.git
cd ExoHabitabilityLab
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload


🌐 API Endpoints
| Endpoint                 | Description        |
| ------------------------ | ------------------ |
| `/health`                | API status         |
| `/exoplanets`            | List exoplanets    |
| `/exoplanets/{id}`       | Detailed info      |
| `/exoplanets/{id}/score` | Habitability score |

📊 Example Response
{
  "planet": "Kepler-442b",
  "habitability_score": 0.78,
  "breakdown": {
    "stellar_type": 0.8,
    "temperature": 0.75,
    "radius": 0.8
  },
  "explanation": "Planet is within conservative habitable zone..."
}

🌍 Scientific Disclaimer
This project:
Does NOT detect life
Does NOT claim habitability certainty
Uses heuristic indicators based on current astrophysical knowledge
Results are educational and exploratory.

🗺 Roadmap
 Frontend dashboard
 Machine learning scoring model
 Visualization of planetary systems
 Artistic planet generation
 Support for exomoons

🤝 Contributing
Contributions are welcome!
Fork the repo
Create a branch
Open a pull request

📜 License
MIT License

👨‍🚀 Author
Facundo – Software Engineer & Space Enthusiast
GitHub: https://github.com/YOUR_USERNAME
Blog/Vlog: COMING SOON 🚀
