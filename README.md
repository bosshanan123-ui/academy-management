# 🎓 Academy Management System

A complete role-based Academy Management System built with **Flask + Supabase (PostgreSQL)**, deployable to **Vercel**.

## ✨ Features

- **Single login** with Roll Number + Password (`SA-2025-0001`, `T-2025-0001`, etc.)
- **Role auto-detection** from roll-number prefix
- **5 roles**: Super Admin, Principal, Teacher, Student, Parent
- **Auto roll-number generation** per year per role
- **Teacher assignments** (Teacher → Class → Section → Subject)
- **Timetable** builder + weekly grid view
- **Attendance** taking (only for assigned classes)
- **Marks entry** per exam type
- **Fee vouchers** + paid/unpaid tracking
- **Notices** with role targeting
- **Chart.js dashboards** (bar, line, doughnut)
- **Responsive** mobile-friendly UI
- **Single CSS file** (`static/css/style.css`)

## 📁 Project Structure

See `tree` above.

## 🚀 Setup

### 1. Clone the repo

```bash
git clone <your-repo-url>
cd academy-management
```

### 2. Create a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create a Supabase project

1. Go to https://supabase.com → New Project.
2. Open **SQL Editor**, paste the entire SQL script from this README (section **SQL Schema**), and click **Run**.
3. Go to **Project Settings → API** and copy:
   - `Project URL` → `SUPABASE_URL`
   - `anon public` key → `SUPABASE_KEY`

### 5. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOi...
FLASK_SECRET_KEY=some-random-secret
```

### 6. Seed the database

```bash
python seed.py
```

This creates the default Super Admin, Principal, sample classes, sections, subjects, teachers, students, parent, assignments, and timetable.

### 7. Run locally

```bash
python app.py
```

Open http://localhost:5000

### 🔐 Default Credentials

| Role        | Roll Number  | Password       |
|-------------|--------------|----------------|
| Super Admin | SA-2025-0001 | admin123       |
| Principal   | P-2025-0001  | principal123   |
| Teacher     | T-2025-0001  | teacher123     |
| Teacher     | T-2025-0002  | teacher123     |
| Student     | S-2025-0001  | student123     |
| Parent      | PT-2025-0001 | parent123      |

> **Change all passwords in production.**

## 🗄️ SQL Schema

Paste this into Supabase → SQL Editor:

```sql
-- (full SQL from section 2 of this build)
```

## ☁️ Deployment to Vercel

1. Push the project to GitHub:

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```

2. Go to https://vercel.com → **Import Project** → select your GitHub repo.

3. In **Environment Variables**, add:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `FLASK_SECRET_KEY`

4. Click **Deploy**. Vercel will use `vercel.json` to build.

5. Your app will be live at `https://your-project.vercel.app`.

## 🧪 Testing Each Role

1. Login as Super Admin → create classes, sections, subjects, teachers, students, parents.
2. Assign teachers in **Assignments**.
3. Build the timetable.
4. Login as Teacher → take attendance, enter marks.
5. Login as Student → view timetable, attendance, results, fees.
6. Login as Parent → view child's data.

## 📸 Screenshots

_(Add screenshots of each dashboard here.)_

## 🛠️ Tech Stack

- **Backend:** Flask, Supabase (PostgreSQL)
- **Frontend:** HTML, CSS (single file), Vanilla JS, Chart.js
- **Deployment:** Vercel
- **Auth:** Werkzeug password hashing + Flask sessions

## 📄 License

MIT