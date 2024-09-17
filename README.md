# Library Management System

## Overview

The Library Management System is a Django Rest Framework (DRF) project designed to manage book borrowing, reservations, and reviews. It supports authentication via JWT and includes features for both authors and borrowers. It also uses Celery to handle periodic tasks in the background. The project also uses Docker for containerization.

## Features

- **Authentication**: JWT authentication for secure access.
- **User Roles**:
  - **Authors**: Create and manage their books, view reviews for their books.
  - **Borrowers**: Borrow books, reserve books, view their borrowing history, and leave reviews.
- **Book Management**: Search and filter books, view book details.
- **Borrowing Transactions**: Automatically manage borrowing periods and due dates.
- **Reservations**: Reserve books that are currently borrowed.
- **Admin Dashboard**: Monitor book borrowings, reservations, and generate reports.
- **Notifications**: Alerts for due dates and available reserved books.

## Installation

### Prerequisites

- Docker
- Docker Compose

### Clone the Repository

  
    git clone https://github.com/Elemental-EL/lms.git
    cd lms

    
## Setup and Run with Docker

### 1. Build the Docker Images


    docker-compose build

### 2. Run Migrations


    docker-compose exec web python manage.py migrate

### 3. Create a Superuser (optional)


    docker-compose exec web python manage.py createsuperuser

### 4. Start the Development Server


    docker-compose up

The application will be accessible at http://localhost:8000.

## Testing
### To run the tests, use the following command:


    docker-compose run web pytest

## License

   © 2024 Elyar KordKatool. All rights reserved.

## Contact

   For any questions or feedback, please reach out to elyar.k2004@protonmail.com .


**Thank you for using the Library Management System!**
