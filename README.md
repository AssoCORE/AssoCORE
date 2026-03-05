# AssoCORE — Association Management Platform

###### An <img src="https://newsroom.ionis-group.com/wp-content/uploads/2023/09/epitech-2023-logo-m.png" height=18/> Innovative project

[Project](#project) • [Vision](#vision) • [Features](#features) • [Architecture](#architecture) • [Usage](#usage) • [Team](#team)

---

<a name="project"></a>
## Project

### Overview

AssoCORE is an **all-in-one association management platform** designed to address the real-world challenges faced by non-profit organizations and associations.

Through field research and discussions with association managers, volunteers, and employees, we identified a recurring issue:
the excessive fragmentation of tools (spreadsheets, shared drives, emails, external calendars), leading to inefficiency, administrative overload, and poor user experience.

AssoCORE proposes a **unified, user-centered solution**, where usability and clarity are treated as first-class concerns rather than secondary features.

---

<a name="vision"></a>
## Vision

AssoCORE aims to become a **digital backbone for associations**, simplifying daily operations while respecting organizational constraints.

Our vision is built around the following principles:
- Reduce administrative complexity
- Centralize essential association tools
- Improve internal and external communication
- Ensure data security and sovereignty
- Provide a modern, intuitive, and accessible user experience

Every feature is designed to be reachable within **2 to 3 clicks**, using a modular and customizable interface adapted to each association’s needs.

---

<a name="features"></a>
## Features

### Core features

- Member management
- Document management (statutes, report, internal files)
- Event management
- Shared calendars and agenda synchronization
- Budget tracking
- Role and permission system
- Email communication and newsletters
- Public association web page

### Advanced features

- Smart room reservation requests
- Internal messaging system
- Monitoring and management dashboards
- User interface personalization
- Multi-language support

### Optional features

- Organizational Kanban boards
- Internal surveys
- Attendance tracking
- Video conferencing

---

<a name="architecture"></a>
## Architecture

> Work in progress

### Global design

AssoCORE is built around a **modular architecture**, allowing:
- feature activation based on association needs
- progressive scalability
- easier maintenance and evolution

### Constraints & guidelines

- **GDPR** compliance
- **Accessibility** standards compliance (RGAA)
- Data sovereignty and protection
- Long-term maintainability

---

<a name="usage"></a>
## Getting Started & Deployment

### 📚 Documentation

Our comprehensive documentation is available in the `docs/` folder and covers everything from Docker basics to Kubernetes deployment:

- **[Docker Basics](./docs/src/content/docs/guides/how-to/docker-basics.mdx)** - Complete beginner's guide to Docker
- **[Docker Deployment with GHCR](./docs/src/content/docs/guides/how-to/docker-deployment.mdx)** - CI/CD and container registry
- **[Kubernetes Deployment](./docs/src/content/docs/guides/how-to/kubernetes-deployment.mdx)** - Deploy on Kubernetes (beginner-friendly)
- **[DevOps Infrastructure](./docs/src/content/docs/architecture/devops-infrastructure.mdx)** - Architecture overview

### 🚀 Quick Start (Docker)

```bash
# 1. Clone the repository
git clone https://github.com/AssoCORE/AssoCORE.git
cd AssoCORE

# 2. Set up environment
cp .env.example .env
# Edit .env with your configuration

# 3. Start services with Docker Compose
docker compose up -d

# 4. Initialize database
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser

# 5. Access the application
# Backend API: http://localhost:8000
# Frontend: http://localhost:3000
```

### ☸️ Quick Start (Kubernetes)

```bash
# 1. Install k3d cluster (easiest for local development)
./k8s/install-k3d.sh

# 2. Deploy core services (Traefik, Watchtower)
./k8s/deploy-core-services.sh YOUR_GITHUB_USERNAME YOUR_GITHUB_TOKEN

# 3. Access Traefik dashboard
kubectl port-forward -n assocore svc/traefik-dashboard 9000:9000
# Open: http://localhost:9000/dashboard/
```

**📖 Full guides with troubleshooting and explanations available in [docs/](./docs/src/content/docs/)!**

---

<a name="usage"></a>
## Usage

> Work in progress

---

<a name="team"></a>
## Team

| <img src="https://avatars.githubusercontent.com/u/146708420?v=4" width=92> | <img src="https://avatars.githubusercontent.com/u/146721664?v=4" width=92> | <img src="https://avatars.githubusercontent.com/u/146714535?v=4" width=92> | <img src="https://avatars.githubusercontent.com/u/114913834?v=4" width=92> | <img src="https://avatars.githubusercontent.com/u/97297209?v=4" width=92> | <img src="https://avatars.githubusercontent.com/u/122123024?v=4" width=92> |
|---|---|---|---|---|---|
| [**Lilian BAZANTAY**](https://github.com/Lilianbazantay)<br/>lilian.bazantay@epitech.eu | [**Valentin ROQUEJOFRE**](https://github.com/Valentin22r)<br/>valentin.roquejofre@epitech.eu | [**Antoine QUILLET**](https://github.com/Touf272)<br/>antoine.quillet@epitech.eu | [**Thibaud LE CREURER**](https://github.com/leTLC)<br/>thibaud.le-creurer@epitech.eu | [**Julien BREGENT**](https://github.com/Fenriir42)<br/>julien.bregent@epitech.eu | [**Louis PERSIN**](https://github.com/ElectronicIV)<br/>louis.percin@epitech.eu |

This project is developed as part of the **Epitech Innovative Project (EIP)**.
