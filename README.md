# Job Portal API

A Flask REST API for a Job Portal. Users can register, companies can post jobs, and applicants can apply.

## 🚀 Live Demo
https://Archibongabasifreke.pythonanywhere.com/

## ✨ Features
- **Authentication**: User Register & Login
- **Companies**: Add and View Companies  
- **Jobs**: Post jobs, Get all jobs, Filter by location
- **Applications**: Apply to jobs, View applications

## 📌 API Endpoints

#### Users
`POST /register` - Register new user  
`POST /login` - Login user

#### Companies  
`POST /company` - Add company  
`GET /companies` - Get all companies

#### Jobs
`POST /add_job` - Add job  
`GET /jobs` - Get all jobs  
`GET /jobs?location=Lagos` - Filter jobs  
`DELETE /jobs/<id>` - Delete job

#### Applications
`POST /apply` - Apply to job  
`GET /my_applications?user_id=1` - Get my applications  
`GET /job/<id>/applications` - See applicants for a job

## 🛠️ Setup & Run
```bash
pip install flask
python app.py