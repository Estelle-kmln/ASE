# BattleCards Microservices — Refactored Architecture with DB Manager

## 📌 Overview

This repository contains the microservices implementation of **BattleCards** for the Advanced Software Engineering course.  
Originally, all microservices shared a single PostgreSQL database directly — this introduced a **Shared Persistence** smell, which reduces service autonomy and violates microservice design principles. To address this, we performed a systematic refactoring using **MicroFreshener**, and migrated database access to a shared **DB Manager module**.  

The result is a cleaner, modular architecture where each service interacts with the database through a centralized abstraction, improving maintainability, consistency, and reducing duplication.

---

## 🚀 What Changed / Why Refactoring was Needed

- Detected **Shared Persistence** smell: auth-service, card-service, game-service, and leaderboard-service all accessed the same database directly.  
- Sharing a single DB across services breaks the **Decentralization Principle** — makes services tightly coupled, hard to maintain, scale, or evolve independently.  
- To solve this, we evaluated refactoring options (split databases, merge services, introduce Data Manager).  

**We chose the Data Manager approach** because it strikes a good balance between practicality and adherence to microservice principles for our project size and timeline.

---

## 🛠 Refactoring Implementation — How It Works

- Introduced a shared module: `common/db_manager.py`  
  - Manages a connection pool with `psycopg2.pool.SimpleConnectionPool`  
  - Provides `unit_of_work()` context manager for SQL transactions (automatic commit/rollback)  
  - Centralizes error handling, retry logic, and database health checks  

- Removed direct database access from all microservices:
  - No more raw `psycopg2.connect(...)` in service code  
  - Instead, all services use `with unit_of_work() as cur:` or `get_connection()` / `release_connection()` for more complex cases  

- Updated each service’s `/health` endpoint to use `db_manager.db_health()` — now health checks include database connectivity  

- The overall architecture is now:

service A
service B \
service C --> DB Manager --> PostgreSQL
service D /


instead of each service connecting directly to PostgreSQL.  

---

## ✅ Benefits

- Single, well-defined place for all persistence logic  
- Easier to maintain, update schema/migrations, or swap DB technology later  
- Less code duplication across services  
- Reduced risk of connection leaks or inconsistent DB usage  
- Centralized error handling, transaction control, health monitoring  

---

## ⚠️ Trade-offs & Considerations

- All services now depend on the DB Manager — becomes a **single point of failure** if not managed carefully; health checks and proper error handling are critical  
- DB Manager may grow complex over time — risk of becoming a “god object” if too much logic is centralized  
- Scaling individual services independently becomes more constrained (they share DB access paths)  

---

## 📦 How to Run the Project

1. Ensure Docker + Docker Compose are installed  
2. From repository root run:

   ```bash
   docker compose down -v      # clear existing volumes  
   docker compose up --build    # build and start all services + DB  
3. Wait until all services (auth, card, game, leaderboard, API gateway) are running and healthy
4. Use service endpoints as before — database interactions are now transparently handled by db_manager.py

---

## 📚 Tools & Architecture Analysis

Architecture smell detection and refactoring guided by MicroFreshener
 — an open-source tool for detecting microservice smells

The “Shared Persistence → DB Manager” refactoring was recommended by MicroFreshener and implemented as described