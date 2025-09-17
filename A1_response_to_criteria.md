Assignment 1 - REST API Project - Response to Criteria
================================================

Overview
------------------------------------------------

- **Name:** Anthonius Evan
- **Student number:** n12342734
- **Application name:** AI Image Detector
- **Two line description:** This app detects if an image is real or AI-generated. Users can then see the website's prediction as well as the confidence level for the prediction.


Core criteria
------------------------------------------------

### Containerise the app

- **ECR Repository name:** evan/ai-image-detector
- **Video timestamp:** 0:17
- **Relevant files:**
    - /Dockerfile
    - compose.yaml

### Deploy the container

- **EC2 instance ID:** i-05455b8c1b660f607
- **Video timestamp:** 0:45

### User login

- **One line description:** Users data stored in MariaDB. Using JWTs for sessions. Stored as a cookie for web client
- **Video timestamp:** 1:30
- **Relevant files:**
    - /app/app.py
    - /db/db.py

### REST API

- **One line description:** API to login, to detect AI or real, to fetch random AI/real image, to get uploaded images, etc
- **Video timestamp:** 01:08 - 01:43
- **Relevant files:**
    - /app/app.py
    - /api/models.py
    - /api/controllers.py

### Data types

- **One line description:** Image files, trained PyTorch model, and SQL database data
- **Video timestamp:** 01:45 - 02:05

#### First kind

- **One line description:** Image and trained model files
- **Type:** Unstructured
- **Rationale:** The images uploaded by users and the trained ResNet50 model file are binary, large, and do not have fixed schema.
- **Video timestamp:** 01:45
- **Relevant files:**
    - in AWS S3 -> ai-detector-image-uploads
    - ai-detector-image-uploads/images
    - ai-detector-image-uploads/model

#### Second kind

- **One line description:** User and upload metadata stored in MariaDB
- **Type:** Structured
- **Rationale:** User IDs, usernames, high scores, and upload records are stored in tables with defined columns and types
- **Video timestamp:** 02:01
- **Relevant files:**
  - /db/db.py

### CPU intensive task

 **One line description:** Batch image inference using ResNet50 on CPU for uploaded images
- **Video timestamp:** 02:06
- **Relevant files:**
    - /app/util.py
    - /app/model.py

### CPU load testing

 **One line description:** Simulated multiple concurrent API requests to /detect-image endpoint from a separate machine
- **Video timestamp:** 02:30
- **Relevant files:**
    - stress_test.py

Additional criteria
------------------------------------------------

### Extensive REST API features

- **One line description:** Pagination, filtering, and sorting implemented for /admin/uploads endpoint
- **Video timestamp:** 03:24
- **Relevant files:**
    - /app/app.py -> /admin/uploads endpoint
    - /public/admin.html

### External API(s)

- **One line description:** Optional AI/real image game uses external API for real image retrieval
- **Video timestamp:** 03:57
- **Relevant files:**
    - /app/app.py -> /game/... endpoint
    - public/game.html

### Additional types of data

- **One line description:** Not attempted
- **Video timestamp:**
- **Relevant files:**
    - 

### Custom processing

- **One line description:** Not attempted
- **Video timestamp:**
- **Relevant files:**
    - 

### Infrastructure as code

- **One line description:** Docker Compose used to execute MariaDB and the main app container
- **Video timestamp:** 03:03
- **Relevant files:**
    - compose.yaml

### Web Client

- **One line description:** Provides a user interface for web client
- **Video timestamp:** 03:15
- **Relevant files:**
    - /app/app.py
    - /public 

### Upon request

- **One line description:** Not attempted
- **Video timestamp:**
- **Relevant files:**
    - 