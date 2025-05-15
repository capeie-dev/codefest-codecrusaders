
# Hotel Reservation API

This project provides a **RESTful API** for hotel reservations. It enables users to create hotels, make reservations, search for availability, and manage existing data. The project is implemented using **Spring Boot**, with a focus on clean architecture and proper validations.

---

## Features
- **Hotel Management**:
  - Create, update, and delete hotels.
  - Search for hotels by availability or retrieve all existing hotels.
  - Each hotel has attributes such as name, type (e.g., DELUXE, LUXURY, SUITE), availability dates, and status.

- **Reservation Management**:
  - Make reservations for a specific hotel, including check-in and check-out dates, number of guests, and status.
  - View or delete existing reservations.
  - Ensures logical validations, such as no overlapping reservations for the same hotel.

- **Validations**:
  - Prevent overlapping reservations for the same hotel.
  - Ensure valid date ranges and proper input formats (e.g., `YYYY-MM-DD`).
  - Disallow deletion of hotels with active reservations.

---

## Explore REST APIs

### Hotel APIs

![image](https://github.com/user-attachments/assets/cb224507-8968-441a-a1d5-600c1271c401)



| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| POST   | `/api/v1/hotel` | Create a new hotel. |
| PATCH  | `/api/v1/hotel` | Update an existing hotel. |
| GET    | `/api/v1/hotels` | Retrieve all hotels. |
| GET    | `/api/v1/hotels/availabilitySearch?dateFrom={from}&dateTo={to}` | Get available hotels for a date range. |
| GET    | `/api/v1/hotel/{id}` | Retrieve a specific hotel by ID. |
| DELETE | `/api/v1/hotel/{id}` | Delete a hotel by ID. |

#### Example Request: Create a New Hotel
**Request Body:**
```json
{
  "name": "Luxury Inn",
  "type": "LUXURY",
  "description": "A luxurious hotel in the city center.",
  "availableFrom": "2025-01-01",
  "availableTo": "2025-12-31",
  "status": true
}
```
**Response:**
```json
{
  "id": 1,
  "name": "Luxury Inn",
  "type": "LUXURY",
  "description": "A luxurious hotel in the city center.",
  "availableFrom": "2025-01-01",
  "availableTo": "2025-12-31",
  "status": true
}
```

---

### Reservation APIs

![image](https://github.com/user-attachments/assets/d51a7e5d-481c-46ed-8bda-a31314e212ff)



| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| POST   | `/api/v1/reservation` | Create a reservation for a hotel. |
| GET    | `/api/v1/reservations` | Retrieve all reservations. |
| GET    | `/api/v1/reservation/{id}` | Retrieve a reservation by ID. |
| DELETE | `/api/v1/reservation/{id}` | Delete a reservation by ID. |

#### Example Request: Create a Reservation
**Request Body:**
```json
{
  "hotelId": 1,
  "checkIn": "2025-03-15",
  "checkOut": "2025-03-20",
  "guests": 2,
  "status": true
}
```
**Response:**
```json
{
  "id": 101,
  "hotelId": 1,
  "checkIn": "2025-03-15",
  "checkOut": "2025-03-20",
  "guests": 2,
  "status": true
}
```



---

## Database Structure
The API uses a **MySQL database** with the following tables:

### `hotel`
| Column          | Type       | Description                         |
| --------------- | ---------- | ----------------------------------- |
| `id`            | Integer    | Primary key.                        |
| `name`          | String     | Hotel name.                         |
| `type`          | Enum       | `DELUXE`, `LUXURY`, or `SUITE`.     |
| `description`   | String     | Description of the hotel.           |
| `availableFrom` | Date       | Start date of availability.         |
| `availableTo`   | Date       | End date of availability.           |
| `status`        | Boolean    | Availability status.                |

### `reservation`
| Column       | Type    | Description                          |
| ------------ | ------- | ------------------------------------ |
| `id`         | Integer | Primary key.                         |
| `hotelId`    | Integer | Foreign key referencing `hotel`.     |
| `checkIn`    | Date    | Check-in date.                       |
| `checkOut`   | Date    | Check-out date.                      |
| `guests`     | Integer | Number of guests.                    |
| `status`     | Boolean | Reservation status.                  |

### Example SQL Script to Set Up the Schema
```sql
CREATE TABLE hotel (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type ENUM('DELUXE', 'LUXURY', 'SUITE') NOT NULL,
    description TEXT,
    availableFrom DATE NOT NULL,
    availableTo DATE NOT NULL,
    status BOOLEAN NOT NULL
);

CREATE TABLE reservation (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hotelId INT NOT NULL,
    checkIn DATE NOT NULL,
    checkOut DATE NOT NULL,
    guests INT NOT NULL,
    status BOOLEAN NOT NULL,
    FOREIGN KEY (hotelId) REFERENCES hotel(id)
);

INSERT INTO hotel (name, type, description, availableFrom, availableTo, status) VALUES
('Luxury Inn', 'LUXURY', 'A luxurious hotel in the city center.', '2025-01-01', '2025-12-31', true),
('City Center Suites', 'DELUXE', 'Conveniently located in the heart of the city.', '2025-01-01', '2025-12-31', true);
```

---

## Tech Stack
- **Backend**: Java 21, Spring Boot 3, Hibernate, JPA
- **Database**: MySQL (runtime), H2 (testing)
- **API Documentation**: Swagger UI
- **Testing**: JUnit 5, Mockito
- **Utilities**: Lombok, Maven

---

## Project Structure
```
marioszocs-spring-boot-hotel-reservation-api/
├── README.md
├── mvnw
├── mvnw.cmd
├── pom.xml
├── src/
│   ├── main/
│   │   ├── java/
│   │   │   └── dev/marioszocs/hotelreservationapi/
│   │   │       ├── HotelReservationApiApplication.java
│   │   │       ├── ServletInitializer.java
│   │   │       ├── bootstrap/
│   │   │       │   └── HotelsAndReservationsLoader.java
│   │   │       ├── config/
│   │   │       │   └── OpenApiConfig.java
│   │   │       ├── constants/
│   │   │       │   ├── AppConstants.java
│   │   │       │   └── ErrorMessages.java
│   │   │       ├── controller/
│   │   │       │   ├── HotelController.java
│   │   │       │   └── ReservationController.java
│   │   │       ├── entity/
│   │   │       │   ├── Hotel.java
│   │   │       │   ├── Reservation.java
│   │   │       │   └── ValidTypesOfHotelsEnum.java
│   │   │       ├── repository/
│   │   │       │   ├── HotelRepository.java
│   │   │       │   └── ReservationRepository.java
│   │   │       ├── service/
│   │   │       │   ├── HotelService.java
│   │   │       │   └── ReservationService.java
│   │   │       ├── serviceImp/
│   │   │       │   ├── HotelServiceImp.java
│   │   │       │   └── ReservationServiceImp.java
│   │   │       ├── utils/
│   │   │       │   └── AppUtils.java
│   │   │       └── validator/
│   │   │           ├── HotelValidator.java
│   │   │           └── ReservationValidator.java
│   │   └── resources/
│   │       ├── application-h2.properties
│   │       ├── application-mysql.properties
│   │       └── application.properties
├── .mvn/
│   └── wrapper/
│       └── maven-wrapper.properties
```

---

## Testing
- Includes **unit tests** (with Mockito) and **integration tests** (using H2 in-memory database).
- Coverage:
  - **93%** of classes.
  - **94%** of methods.
  - **85%** of lines.
- Test scenarios:
  - API endpoint responses.
  - Validation of inputs and error handling.
  - Business logic for reservations and hotel availability.

---

## Installation

### Prerequisites
- Java 21
- Maven
- MySQL (if not using the H2 database)

### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/hotel-reservation-api.git
   cd hotel-reservation-api
   ```
2. Configure the database in `src/main/resources/application.properties`:
   ```properties
   spring.datasource.url=jdbc:mysql://localhost:3306/hotel_reservation_db
   spring.datasource.username=your-username
   spring.datasource.password=your-password
   ```
3. Build the project:
   ```bash
   mvn clean install
   ```
4. Run the application:
   ```bash
   mvn spring-boot:run
   ```

---

## Contribution
Contributions are welcome! Feel free to fork the repository and submit a pull request.




























