# 🌌 ExoHabitabilityLab

> **Exploring worlds where life could emerge** – habitability scoring for exoplanets using NASA & ESA open data

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

ExoHabitabilityLab is an open-source scientific application that analyzes real exoplanet data from NASA and ESA to estimate the potential habitability of planets beyond our Solar System.

The project combines astrophysics, open data, and software engineering to create an educational and exploratory platform for space enthusiasts, researchers, and developers.

---

## 🌐 Live Demo

| | Link |
|---|---|
| 🪐 **Web app (UI)** | **https://exohabitability-ui.vercel.app** |
| ⚙️ **API** | https://exohabitabilitylab.vercel.app |
| 📖 **API docs (Swagger)** | https://exohabitabilitylab.vercel.app/docs |

The project is split into two repositories, both deployed on **Vercel** (API on serverless Python + **Neon Postgres**, UI as a static SPA):

- **Backend API** — this repo.
- **Frontend UI** — a space-themed **Angular 19** app: [ExoHabitabilityLab-UI](https://github.com/facundozambuto/ExoHabitabilityLab-UI). Animated starfield, ambient soundscape, habitability leaderboard, search, planet detail, AI image generation, side-by-side comparison and an **Astrophysics Lab**.

---

## 🚀 Project Overview

The goal of ExoHabitabilityLab is to:

- Fetch and process real exoplanet datasets from NASA and ESA
- Compute a scientifically-informed **habitability score** using 13 factors
- Provide detailed scientific explanations for each assessment
- Generate AI-powered artistic visualizations of exoplanets
- Offer a modern API to explore other worlds

> ⚠️ **Important**: This is not a life-detection tool. It is a platform to explore which planets might be better candidates for further study based on our current understanding of habitability.

---

## 🧪 Features

### Core Features
- 🔬 **Scientific Scoring Engine** - Plugin-based architecture with 13 habitability factors
- 🌟 **Multi-source Data Integration** - NASA Exoplanet Archive + ESA datasets
- 🎨 **AI Image Generation** - Create artistic visualizations of exoplanets
- ⚡ **High Performance** - Async API with intelligent caching
- 📊 **Detailed Explanations** - Scientific reasoning for every score
- ⚛️ **Astrophysics Lab (Astropy)** - Research-grade derived quantities per planet (see below)
- 🖥️ **Space-themed Web UI** - Angular 19 companion app to explore everything visually

### ⚛️ Astrophysics Lab (Astropy)

The `GET /api/v1/exoplanets/{id}/astrophysics` endpoint uses **[Astropy](https://www.astropy.org/)** to derive
research-grade quantities from the catalogue parameters:

| Quantity | Method / reference |
|----------|--------------------|
| **Habitable-zone boundaries** | Conservative & optimistic edges — Kopparapu et al. (2014) |
| **Instellation & equilibrium temperature** | Incident flux (S⊕) and T_eq for several Bond albedos |
| **Earth Similarity Index (ESI)** | Schulze-Makuch et al. (2011) |
| **Surface gravity / escape velocity / density** | Astropy constants |
| **Galactic coordinates (ℓ, b)** | ICRS → Galactic via `astropy.coordinates.SkyCoord` |
| **Transit depth & radial-velocity semi-amplitude** | Detectability of the planet |
| **Host-star blackbody peak** | Wien's law + approximate colour |

> Astropy is imported lazily so it only loads for this route, keeping the rest of the serverless API light.

### Scoring Factors
| Category | Factor | Description |
|----------|--------|-------------|
| **Stellar** | Stellar Type | Host star spectral class (F-M optimal) |
| | Stellar Luminosity | Light output and radiation |
| | Stellar Age | Time for life to evolve (2-8 Gyr optimal) |
| | Habitable Zone Position | Distance from conservative/optimistic HZ |
| **Planetary** | Planet Radius | Size indicator of composition |
| | Planet Mass | Atmosphere retention capability |
| | Planet Density | Composition inference (rocky vs gas) |
| | Equilibrium Temperature | Surface temperature proxy |
| | Surface Gravity | Atmosphere retention & biology |
| **Orbital** | Orbital Eccentricity | Climate stability |
| | Tidal Locking | Day/night hemisphere effects |
| **Derived** | Atmosphere Retention | Escape velocity vs stellar activity |
| | Magnetic Field | Protection from stellar wind |

---

## 🛠 Tech Stack

- **Runtime**: Python 3.11+ (3.12 on Vercel)
- **Framework**: FastAPI with async support
- **Validation**: Pydantic v2
- **Database**: SQLAlchemy async — SQLite locally, **Neon Postgres** in production
- **Astronomy**: Astropy (advanced astrophysics endpoint)
- **Testing**: pytest + pytest-asyncio
- **Frontend**: Angular 19 SPA ([separate repo](https://github.com/facundozambuto/ExoHabitabilityLab-UI))
- **Hosting**: Vercel (serverless Python + static SPA)

---

## 📁 Project Structure

```
ExoHabitabilityLab/
├── app/
│   ├── main.py                     # FastAPI application entry point
│   ├── api/
│   │   ├── routes/
│   │   │   ├── health.py           # Health check endpoint
│   │   │   ├── exoplanets.py       # Exoplanet CRUD & scoring
│   │   │   └── images.py           # Image generation endpoint
│   │   └── deps.py                 # Dependency injection
│   ├── core/
│   │   ├── config.py               # Application settings
│   │   └── logging.py              # Logging configuration
│   ├── domain/                     # Domain layer (DDD)
│   │   ├── entities/
│   │   │   ├── exoplanet.py        # ExoplanetEntity with physics
│   │   │   ├── star.py             # StarEntity with HZ calculations
│   │   │   └── habitability.py     # HabitabilityAssessment
│   │   └── scoring/
│   │       ├── engine.py           # ScoringEngine orchestrator
│   │       ├── config.py           # YAML-based configuration
│   │       ├── base.py             # Factor plugin interface
│   │       └── factors/            # 13 scoring factor plugins
│   │           ├── stellar.py      # Stellar factors (4)
│   │           ├── planetary.py    # Planetary factors (5)
│   │           ├── orbital.py      # Orbital factors (2)
│   │           └── derived.py      # Derived factors (2)
│   ├── infrastructure/
│   │   └── caching.py              # Cache backend abstraction
│   ├── models/                     # SQLAlchemy models
│   ├── schemas/                    # Pydantic schemas
│   └── services/
│       ├── nasa.py                 # NASA API integration
│       ├── esa.py                  # ESA API integration
│       └── image_generation.py     # AI image service
├── tests/
│   ├── test_scoring_engine.py      # Scoring engine tests
│   └── test_image_generation.py    # Image generation tests
└── scoring_weights.yaml            # Factor weight configuration
```


---

## 🔧 Installation

```bash
git clone https://github.com/facundozambuto/ExoHabitabilityLab.git
cd ExoHabitabilityLab
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## ⚙️ Configuration

Copy the example environment file and customize as needed:

```bash
cp .env.example .env
```

### Scoring Configuration

Factor weights can be customized via `scoring_weights.yaml`:

```yaml
# scoring_weights.yaml
weights:
  stellar_type: 1.0
  stellar_luminosity: 0.7
  stellar_age: 0.6
  habitable_zone_position: 1.5  # Extra weight for HZ position
  planet_radius: 1.2
  planet_mass: 1.0
  planet_density: 0.8
  equilibrium_temperature: 1.3
  surface_gravity: 0.9
  orbital_eccentricity: 0.8
  tidal_locking: 0.6
  atmosphere_retention: 1.1
  magnetic_field: 0.7

normalization_method: weighted_average  # or geometric_mean, minimum
```

## 🚀 Running the API

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_scoring_engine.py -v
```

## 📊 Syncing Data

Before using the API, sync exoplanet data from external sources:

```bash
# Using curl
curl -X POST http://localhost:8000/api/v1/exoplanets/sync/nasa?limit=100
curl -X POST http://localhost:8000/api/v1/exoplanets/sync/esa
```

---

## 🌐 API Endpoints

| Endpoint                          | Method | Description                    |
| --------------------------------- | ------ | ------------------------------ |
| `/api/v1/health`                  | GET    | API health status              |
| `/api/v1/exoplanets`              | GET    | List exoplanets (paginated)    |
| `/api/v1/exoplanets/{id}`         | GET    | Get exoplanet details          |
| `/api/v1/exoplanets/{id}/score`   | GET    | Get habitability score         |
| `/api/v1/exoplanets/{id}/astrophysics` | GET | Astropy-derived astrophysics (HZ, ESI, galactic coords…) |
| `/api/v1/exoplanets/{id}/generate-art` | POST | Generate AI visualization |
| `/api/v1/exoplanets/ranking/top`  | GET    | Top habitable planets, ranked  |
| `/api/v1/exoplanets/scoring/methodology` | GET | Scoring methodology info |
| `/api/v1/exoplanets/sync/nasa`    | POST   | Sync from NASA archive         |
| `/api/v1/exoplanets/sync/esa`     | POST   | Sync from ESA (mock)           |

---

## 📊 Example Responses

### Habitability Score Response

```json
{
  "exoplanet_id": 1,
  "exoplanet_name": "Kepler-442 b",
  "total_score": 0.8234,
  "score_category": "Very High",
  "factors": [
    {
      "factor_id": "stellar_type",
      "factor_name": "Stellar Type",
      "score": 0.85,
      "weight": 1.0,
      "input_value": "K5V",
      "optimal_range": "G, K spectral classes",
      "explanation": "K-type star (K5V): Slightly cooler than Sun. Excellent habitability potential with very stable luminosity and extended lifetime.",
      "confidence": "high"
    },
    {
      "factor_id": "habitable_zone_position",
      "factor_name": "Habitable Zone Position",
      "score": 0.95,
      "weight": 1.5,
      "input_value": "0.409 AU",
      "optimal_range": "Within conservative HZ",
      "explanation": "Planet orbits within the conservative habitable zone where liquid water could exist on the surface.",
      "confidence": "high"
    }
  ],
  "data_completeness": 0.92,
  "assessment_version": "2.0.0",
  "scientific_disclaimer": "This is a probabilistic indicator, not a detection of life..."
}
```

### Image Generation Response

```json
{
  "exoplanet_name": "Kepler-442 b",
  "style": "realistic",
  "prompt": "Photorealistic render of an exoplanet, massive rocky super-Earth with dramatic landscapes, temperate atmosphere with water vapor clouds, illuminated by orange amber-tinted starlight...",
  "scientific_notes": [
    "Super-Earth: Larger rocky world with stronger gravity",
    "T_eq 233K: Cool but potentially habitable"
  ],
  "image_url": "https://..."
}
```

---

## 🔬 Scoring Methodology

### How Habitability Scores Are Calculated

The scoring engine evaluates 13 factors across 4 categories:

1. **Stellar Factors** (4 factors)
   - Assess the host star's suitability for life
   - G and K-type stars score highest (stable, long-lived)
   - Habitable zone boundaries calculated using Kopparapu et al. (2013, 2014)

2. **Planetary Factors** (5 factors)
   - Evaluate physical properties
   - Earth-sized to super-Earth sizes optimal
   - Rocky composition (density >3 g/cm³) preferred

3. **Orbital Factors** (2 factors)
   - Climate stability assessment
   - Low eccentricity = stable temperatures
   - Tidal locking effects considered

4. **Derived Factors** (2 factors)
   - Inferred from multiple properties
   - Atmosphere retention from escape velocity
   - Magnetic field from mass/age/composition

### Confidence Levels

Each factor reports a confidence level:
- **High**: Directly measured parameter
- **Medium**: Calculated from measurements
- **Low**: Estimated or inferred
- **Very Low**: Missing data, default used

### Score Normalization

Final scores are calculated using configurable methods:
- **Weighted Average** (default): Σ(score × weight) / Σ(weight)
- **Geometric Mean**: (∏ score^weight)^(1/Σweight)
- **Minimum**: Conservative approach using lowest factor

---

## 🌍 Scientific Disclaimer

This project:
Does NOT detect life
Does NOT claim habitability certainty
Uses heuristic indicators based on current astrophysical knowledge
Results are educational and exploratory.

🗺 Roadmap
- [x] Frontend dashboard (Angular 19 SPA)
- [x] Artistic planet generation (AI images)
- [x] Advanced astrophysics (Astropy: HZ, ESI, galactic coords…)
- [x] Habitability ranking / leaderboard
- [ ] Machine learning scoring model
- [ ] Visualization of planetary systems
- [ ] Support for exomoons

🤝 Contributing
Contributions are welcome!
Fork the repo
Create a branch
Open a pull request

📜 License
MIT License

👨‍🚀 Author
Facundo – Software Engineer & Space Enthusiast
GitHub: https://github.com/facundozambuto
Blog/Vlog: COMING SOON 🚀
