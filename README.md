# Akash Clinic: Hospital Billing and Patient Management

A simple web app for a small clinic to register patients, search records, generate bills and print receipts. Built with Flask and SQLite.

## Features

- Admin login with session protection on all pages
- Add patients with validation (name, age, 10-digit contact, gender, date of birth, disease)
- Dashboard listing all patients, newest first
- Search by name, contact number or disease
- Delete a patient along with their bills
- Automatic bill: consultation fee plus a disease-based charge
- Payment by Cash or UPI
- Printable receipt

## Pricing

Consultation fee is Rs. 300 for every visit. The disease charge is added on top:

- Fever: Rs. 200
- Cold and Cough: Rs. 200
- Malaria: Rs. 500
- Dengue: Rs. 500
- Typhoid: Rs. 500
- Other: Rs. 300

Prices are set in `DISEASE_PRICES` and `CONSULTATION_FEE` at the top of `bill.py`.

## Tech Stack

- Python 3
- Flask
- SQLite (built in with Python)
- HTML, Jinja2 templates and CSS

## Project Structure

```
akash hospitals/
├── bill.py               Flask app: routes, validation, database setup
├── clinic.db             SQLite database
├── static/
│   └── style.css         Styles
└── templates/
    ├── login.html        Login page
    ├── dashboard.html    Patient list and search
    ├── patient_form.html Add patient form
    ├── bill.html         Bill preview and payment selection
    └── receipt.html      Printable receipt
```

## Database

The tables are created automatically on first run.

- `patients`: id, name, age, contact, gender, dob, disease, created_at
- `bills`: id, patient_id, consultation_fee, disease_charge, total, payment_method, created_at

Each bill is linked to a patient through `patient_id`.

## Getting Started

1. Clone the repository

```
git clone https://github.com/akash33-cmd/Hospitals-billing-Software.git
cd Hospitals-billing-Software
```

2. Install Flask

```
pip install flask
```

3. Run the app

```
python bill.py
```

4. Open http://127.0.0.1:5000 in your browser

## Default Login

- Username: `admin`
- Password: `1234`

These are hardcoded in `bill.py`. Change them before using the app with real patient data.

## Configuration

The session secret key is read from the `SECRET_KEY` environment variable. If it is not set, a default value is used, so set your own for any real deployment.

```
export SECRET_KEY="your-own-random-string"
```

## How to Use

1. Log in with the admin account
2. Click **Add Patient** and fill in the details
3. Find the patient on the dashboard, using search if needed
4. Click the bill action for that patient and choose Cash or UPI
5. Print the receipt from the receipt page

## Notes

- The app runs in debug mode on localhost only. Turn debug off before deploying.
- Back up `clinic.db` regularly, since all records are stored in that single file.

## Future Improvements

- Store hashed passwords and support multiple users
- Edit patient details
- Bill history and daily revenue reports
- Export records to PDF or Excel

## Author

Akash
