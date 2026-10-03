# Project Plan: Flask Resume Builder Web Application

## 1. Project Overview
A web-based application designed for students to create, manage, and download their professional resumes. The application allows users to maintain multiple job-specific roles (e.g., Software Engineer, Data Analyst) under a single profile. Resumes will be downloadable in PDF format, starting with a clean, simple design. A monetization strategy (paywall/premium access for downloads) will be integrated in a later phase.

## 2. Technical Stack
*   **Backend Framework:** Python / Flask
*   **Template Engine:** Jinja2 (Default Flask templating)
*   **Database:** SQLite (Development) / PostgreSQL (Production)
*   **ORM:** Flask-SQLAlchemy
*   **Authentication:** Flask-Login, Flask-Bcrypt
*   **Form Handling & Validation:** Flask-WTF
*   **PDF Generation:** WeasyPrint (recommended for superior HTML/CSS-to-PDF rendering)
*   **Payments (Future):** Stripe API

## 3. Database Architecture (Entity Relationship)
To support the "multiple roles" requirement, the database uses a relational structure:

*   **User:** Handles authentication and premium status.
    *   Fields: `id`, `email`, `password_hash`, `is_premium` (Boolean)
*   **Personal_Info:** Static details associated with the user.
    *   Fields: `id`, `user_id` (FK), `first_name`, `last_name`, `phone`, `address`, `linkedin`, `portfolio`
*   **Resume_Role:** The central entity for a specific job profile.
    *   Fields: `id`, `user_id` (FK), `role_name` (e.g., "Frontend Developer"), `summary`
*   **Experience:** Work history linked to a specific role.
    *   Fields: `id`, `role_id` (FK), `company`, `job_title`, `start_date`, `end_date`, `description`
*   **Education:** Academic history linked to a specific role.
    *   Fields: `id`, `role_id` (FK), `institution`, `degree`, `start_date`, `end_date`
*   **Skill:** Individual skills linked to a specific role.
    *   Fields: `id`, `role_id` (FK), `skill_name`

## 4. Application Structure (Flask Blueprints)
The application will utilize Flask Blueprints for modularity and scalability.

```text
resume_app/
├── app/
│   ├── __init__.py          # App factory and initialization
│   ├── models.py            # SQLAlchemy database schemas
│   ├── forms.py             # Flask-WTF form classes
│   ├── auth/                # Blueprint: Authentication
│   ├── dashboard/           # Blueprint: Data management (Roles, Experience)
│   ├── resume/              # Blueprint: PDF rendering and downloading
│   ├── templates/           # Jinja2 HTML templates (auth, dashboard, resumes)
│   └── static/              # CSS, JavaScript, and images
├── requirements.txt         # Project dependencies
├── config.py                # Environment and configuration variables
└── run.py                   # Application entry point
```

## 5. Phased Implementation Plan

### Phase 1: Environment Setup & Authentication
*   Initialize the Python virtual environment and install base dependencies.
*   Set up the Flask Application Factory pattern.
*   Configure the database URI and secret keys.
*   Develop the `User` model.
*   Implement registration, login, and logout workflows using `Flask-Login`.

### Phase 2: Core Data Management (The Dashboard)
*   Develop remaining database models (`PersonalInfo`, `ResumeRole`, `Experience`, etc.).
*   Create secure web forms using `Flask-WTF`.
*   Build the user dashboard interfaces:
    *   Form to update `Personal_Info`.
    *   Interface to Create/Edit/Delete a `Resume_Role`.
    *   Sub-interfaces within a role to manage `Experience`, `Education`, and `Skill` entries.

### Phase 3: The PDF Generation Engine
*   Design `simple_template.html` using Jinja2 to display the resume data clearly.
*   Write a dedicated `resume_style.css` tailored specifically for print (`@page` rules, A4 dimensions, print-friendly fonts).
*   Create the download route (`/download/pdf/<role_id>`).
*   Implement the PDF conversion logic: Render the Jinja template into an HTML string, then pass it to `WeasyPrint` to generate and serve the PDF file.

### Phase 4: Monetization (Paywall Integration)
*   Integrate Stripe API checkout.
*   Modify the download route logic:
    *   Check `if current_user.is_premium`.
    *   If True, generate and serve the PDF.
    *   If False, redirect the user to a checkout/payment page.
*   Set up a Stripe Webhook to listen for successful payments and update the user's `is_premium` status in the database.

## 6. Future Expansion Ideas
*   **Multiple Templates:** Introduce a template selection UI and pass the selected template name to the render engine.
*   **Freemium Model:** Grant users 1 free PDF generation before hitting the paywall by adding a `downloads_remaining` integer to the User model.