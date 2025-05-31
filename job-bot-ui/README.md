# 🤖 Auto-Applying LinkedIn Bot

An automation bot built using **Python**, **Flask**, and **Selenium** to automatically apply for "Easy Apply" jobs on LinkedIn. It includes a backend service and an optional frontend interface to manage and control the bot.

---

## 📌 Features

- Auto-login to LinkedIn
- Automatically applies to "Easy Apply" jobs
- Handles external job links and sends them via email
- Skips already applied jobs
- Fills forms with default values or AI logic
- Frontend UI built with React (optional)

---

## 🧰 Tech Stack

- Python 3.8+
- Flask
- Selenium
- Flask-CORS
- React (Frontend)
- Node.js & npm
- Chrome & ChromeDriver

---

---

## ⚙️ Step-by-Step Process to Run the Project

### ✅ Prerequisite

- Make sure you're using a terminal directed to the project folder (e.g., `D:\bot-vscode\`)

---

### 🔧 Backend Setup

1. Navigate to the `backend` folder:

```bash
cd backend

pip install flask
pip install selenium
pip install flask-cors

# Run the backend Server
# make sure your in the backend folder and run this
python app.py


# Frontend Setup
cd job-bot-ui
npm install
npm start

