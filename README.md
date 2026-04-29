# CuotaPro: A Student Manager App 📚

A lightweight desktop application for managing students, payments, and monthly fees in small educational institutes.

Designed for **single-user environments** and **low-end hardware**, this project balances **performance**, **simplicity**, and **clean architecture principles**.

---

## 🚀 Overview

This application allows an institute director to:

* Manage students and their information
* Track monthly fees and payments
* Monitor debt and balances
* Reverse transactions safely
* Generate simple financial insights

The system is optimized for:

* ~250 students
* Local execution (no server)
* SQLite database
* Low memory and CPU usage

---

## 🧠 Architecture

The project follows a **pragmatic DDD-lite + Clean Architecture + CQRS-lite** approach.

### Key Principles

* **Domain-driven design (lite)**
  Core business rules live in the domain layer using entities and value objects.

* **Clean Architecture**
  Clear separation between:

  * Domain
  * Application services
  * Infrastructure (SQLite)

* **CQRS-lite**

  * Command side: uses domain aggregates (`Student`, `StudentAccount`)
  * Query side: optimized read operations using repositories and DTOs

---

## 🧱 Project Structure

```
domain/
├── student/
├── accounting/
├── student_account/

application/
├── application_service.py   # Command side
├── cqrs.py                  # Query side
├── dto.py                   # Data Transfer Objects
├── mappers.py

infrastructure/
├── database/
```

---

## 🧩 Domain Model

### Core Entities

* **Student**

  * Personal and academic data
  * Monthly fee
  * Active/inactive state

* **Movement**

  * Financial transaction (FEE, PAYMENT, REVERSED)

* **StudentAccount (Aggregate Root)**

  * Handles:

    * Balance calculation
    * Payments
    * Fees
    * Reversals

---

### Value Objects

* `StudentName`
* `PhoneNumber`
* `MonthlyFee`
* `Money`
* `Period`

These enforce validation and keep the domain consistent.

---

## ⚙️ Tech Stack

* **Python**
* **SQLite**
* **ttkbootstrap** (UI)
* **Pydantic** (DTO validation)

---

## 🔄 Core Workflows

### ➕ Add Student

* Validated via DTO + domain objects
* Persisted in SQLite

### 💰 Add Payment

* Ensures student is active
* Ensures debt exists
* Registers movement

### 📅 Apply Monthly Fees

* Batch operation
* Avoids duplicates per period

### 🔁 Reverse Movement

* Creates reversal entry (immutable system)
* Preserves history

---

## 📊 Query System (CQRS-lite)

Read operations are separated and optimized:

* Student overviews
* Balances
* Debt tracking
* KPI metrics
* Income trends

⚠️ Note: Some queries reconstruct domain objects for consistency, but heavy operations are being optimized progressively.

---

## 🧪 Design Tradeoffs

This project intentionally makes pragmatic decisions:

### ✔️ Chosen

* Simple SQLite over external DB
* In-memory aggregation for clarity
* Minimal abstractions

### ❗ Tradeoffs

* Some read operations rebuild aggregates (can be optimized)
* Rehydration trusts database integrity
* No multi-user concurrency support

---

## 🔐 Data Integrity

* Domain enforces business rules
* Repository layer uses parameterized queries (safe from SQL injection)
* Movements are **immutable** (no updates/deletes)

---

## ⚡ Performance Considerations

Optimized for low-end devices:

* Batch operations (e.g., fee application)
* Minimal dependencies
* SQLite transactions
* Avoids unnecessary complexity

Known improvement areas:

* Reduce N+1 queries in read layer
* Use SQL aggregation for reporting
* Add indexes on movement queries

---

## 📈 Future Improvements

* [ ] Add database indexes and constraints
* [ ] Optimize CQRS queries (remove N+1 patterns)
* [ ] Introduce lightweight read models
* [ ] Add domain events
* [ ] Improve validation on rehydration
* [ ] Optional caching for reports

---

## 🧑‍💻 Development Philosophy

This project aims to:

* Stay **simple but correct**
* Use **DDD where it adds value**
* Avoid over-engineering
* Prioritize **real-world usability**

---

## 📌 Target Use Case

Small institutes that need:

* A reliable offline system
* Simple financial tracking
* No infrastructure overhead

---

## 📝 License

Private / Custom (adjust as needed)

---

## 💬 Final Note

This is a **pragmatic system**, not an academic exercise.

It intentionally balances:

* correctness
* performance
* maintainability

while remaining usable on modest hardware.

---

