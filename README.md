# Cinema Ticket Booking — IT5016 Assessment 3: Research Repository

> **Course**: IT5016 – Assessment 3 (Research Repository)  
> **Purpose**: Demonstrate analysis of programming principles on a small, real project; add clear commentary inside code; document your research and reflections in this README; submit a Word/PDF that includes this content and your repo link.  
> **Repo URL**: [click](https://github.com/roshanshrestha/cinema-ticket-booking-research)

---

## Attribution (source of the project code)

This repository analyzes and documents a **borrowed** beginner project:

- **Original repo**: `pxxthik/Python-OOP-Projects`
- **Original folder**: `Cinema_Ticket_Booking`
- **Original author**: `pxxthik`
- **Retrieved on**: <add date>
- **Modifications here**: bug fixes, migration to `fpdf2` API (`text=` params), exception handling, comments, and documentation for educational purposes.

> Note: This repo is for **learning/research**. Full credit to the original author; any code snippets retained here remain under the original author’s rights/licence. I added analysis-only comments and documentation.

---

## What this repository contains

cinema-ticket-booking-research/
├─ README.md
├─ src/
│  └─ cinema-ticket-booking/
│       ├─ main.py
│       ├─ description.txt
│       ├─ banking.db
│       └─ cinema.db
└─ docs/
└─ principles-notes.md


**Project summary**  
An app where a user can book a cinema seat **if** the seat is free and **if** the card has enough balance. On success, it generates a **PDF ticket**.

**Objects (from `description.txt`)**  
- `User(name).buy(seat, card)`  
- `Seat(database, seat_id) → get_price(), is_free(), occupy()`  
- `Card(database, type, number, cvc, holder) → validate(price)`  
- `Ticket(user, price, seat_number).to_pdf(path)`  

---

## How to run (quick start)

### 1) Requirements
- Python 3.8+
- Packages:
  ```bash
  pip install fpdf2
```

(`sqlite3` is part of Python’s standard library.)

### 2) Ensure the two databases are present

Place `cinema.db` and `banking.db` next to `main.py`:

```
src/cinema-ticket-booking/main.py
src/cinema-ticket-bookking/cinema.db
src/cinema-ticket-bookking/banking.db
```

> If you **don’t** have the DB files, see **Appendix A** for SQL to create & seed minimal tables.

### 3) Run

```bash
cd src/cinema-ticket-booking
python main.py
```

Follow prompts (name, seat id, card details). On success, a `ticket_<ID>.pdf` is created in the same folder.

---

## Principles covered (my own words)

* **SRP (Single Responsibility Principle)**: a function/class should do one primary job; split unrelated tasks.
* **DRY (Don’t Repeat Yourself)**: avoid duplicating logic; extract helpers/utilities.
* **Cohesion**: keep related logic together inside a unit (function/class); higher cohesion is better.
* **Coupling**: how tightly pieces depend on each other; lower coupling is better for change.
* **Encapsulation/Abstraction**: hide details behind well-defined methods so callers don’t know internal complexity.
* **Testability**: code structure that makes it easy to write and run tests (pure functions, dependency injection, minimal I/O inside logic).
* **Error Handling**: handle failure paths predictably; don’t crash on expected errors.

---

## What I fixed (engineering notes)

* Migrated to **fpdf2** API (`cell(..., text=...)`) to resolve “no parameter named `txt`” errors.
* Ensured **DB connections are closed** after queries/updates.
* **`Card.validate`** now always returns a boolean; clearer failure paths.
* Added **try/except** for DB operations to avoid crashes if files/tables are missing.
* Unique, meaningful **PDF filename** (`ticket_<id>.pdf`).
* Extracted a small `_add_field` helper in `Ticket` for **DRY**.

---

## Short analysis by component

### 1) `User.buy(seat, card)`

* **What it does**: checks seat availability, validates/charges card, occupies seat, generates ticket.
* **Principles observed**:

  * SRP concern: does **many** things; mixing orchestration, validation, state updates, and PDF concerns.
  * Cohesion: the concept “buy” holds, but responsibilities could be split.
* **Improvements**: introduce a `PurchaseService`/`PaymentProcessor` to handle payment & ticketing; `User` becomes a simple domain entity.

### 2) `Seat` (`get_price`, `is_free`, `occupy`)

* **What it does**: reads price/availability and updates status in `cinema.db`.
* **Principles observed**:

  * Encapsulation: hides SQL & DB details.
  * Coupling: **hard-coupled** to SQLite and schema names.
* **Improvements**: move SQL into a `SeatRepository` with context managers; add caching if multiple queries per seat; pass DB path as dependency.

### 3) `Card.validate(price)`

* **What it does**: verifies number/cvc and balance; reduces balance if sufficient.
* **Principles observed**:

  * SRP concern: **validate** and **mutate balance** in one method.
  * Coupling: DB-specific.
* **Improvements**: split into `is_valid()` and `charge(amount)`; consider a `CardRepository`; never store CVC in plaintext in real systems (security note).

### 4) `Ticket.to_pdf()`

* **What it does**: generates a simple A4 PDF using `fpdf2`.
* **Principles observed**:

  * DRY: `_add_field()` helper avoids repeated `cell(...)` blocks.
  * SRP concern: formatting + file I/O together.
* **Improvements**: a `PdfTicketRenderer` class; configurable output path; templating.

### 5) I/O & Testing

* **Current**: console input gathered in `__main__`.
* **Improvement**: isolate input collection, allow passing parameters to a pure `purchase(name, seat_id, card)` function → easier unit tests.

---

## Deep Dives

### Deep Dive #1 — Separating the Purchase Flow (SRP, Coupling, Testability)

**Issue**: `User.buy` orchestrates *everything* (seat check, payment, DB updates, ticket).
**Why it matters**: hard to test each step; any change in payment/ticketing ripples through.
**Refactor sketch**:

```python
class PaymentProcessor:
    def __init__(self, card_repo):
        self.card_repo = card_repo

    def charge(self, card, amount) -> bool:
        if self.card_repo.has_funds(card.number, card.cvc, amount):
            self.card_repo.debit(card.number, card.cvc, amount)
            return True
        return False

class PurchaseService:
    def __init__(self, seat_repo, payment_processor, ticket_renderer):
        self.seat_repo = seat_repo
        self.payment = payment_processor
        self.render = ticket_renderer

    def buy(self, user, seat_id, card):
        if not self.seat_repo.is_free(seat_id):
            return "Seat is taken!"
        price = self.seat_repo.price_of(seat_id)
        if not self.payment.charge(card, price):
            return "There was a problem with your card!"
        self.seat_repo.occupy(seat_id)
        self.render.create_ticket(user.name, seat_id, price)
        return "Purchase Successful!"
```

**Benefits**:

* **SRP**: each class has a clear role.
* **Low coupling**: swapping DB or PDF lib touches only one place.
* **Testability**: can unit-test `PurchaseService` with fake repos.

### Deep Dive #2 — Data Access Layer (Encapsulation, Coupling)

**Issue**: SQL calls are embedded in domain classes.
**Why it matters**: schema or DB changes require editing many methods; code mixes business logic with persistence.
**Refactor sketch**:

```python
class SeatRepository:
    def __init__(self, db_path="cinema.db"):
        self.db_path = db_path

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def price_of(self, seat_id):
        with self._conn() as conn:
            cur = conn.execute("SELECT price FROM Seat WHERE seat_id=?", [seat_id])
            row = cur.fetchone()
            return row[0] if row else None

    def is_free(self, seat_id):
        with self._conn() as conn:
            cur = conn.execute("SELECT taken FROM Seat WHERE seat_id=?", [seat_id])
            row = cur.fetchone()
            return (row and row[0] == 0)

    def occupy(self, seat_id):
        with self._conn() as conn:
            conn.execute("UPDATE Seat SET taken=? WHERE seat_id=?", [1, seat_id])
```

**Benefits**: cleaner domain objects, easier migration to another DB.

### Deep Dive #3 — Input/Output Boundaries (Testability, Cohesion)

**Issue**: user input happens inline in `__main__`; business logic depends on console I/O.
**Refactor idea**:

* Add a pure function `purchase_flow(user_name, seat_id, card_details, services)` returning a message; keep console I/O separate.
* Write tests for `purchase_flow` with mocked/fake services and in-memory SQLite.
  **Sample test cases**:
* Seat free + sufficient balance → success & seat taken.
* Seat taken → fail with “Seat is taken!”.
* Invalid card/CVC → fail with “There was a problem with your card!”.
* Insufficient balance → appropriate failure message.

---

## Known limitations & risks

* **Security**: card number & CVC stored in plaintext for demo purposes — never do this in production.
* **Concurrency**: no locks; simultaneous purchases could race on the same seat.
* **Error handling/UI**: console-only; limited user feedback on DB errors.
* **Config**: DB filenames are hardcoded; better to inject via config/env.

---

## How I would extend this (roadmap)

* Replace embedded SQL with repositories + dependency injection.
* Add basic unit tests (pytest) and use an **in-memory SQLite** for testing.
* Introduce a small CLI or GUI layer separate from business logic.
* Add an interface for payment to allow mock processors (e.g., `IPaymentProcessor`).
* Improve PDF layout and add date/time, cinema name, and seat row formatting.

---

## Submission notes (for Canvas)

* **Include your repo link** at the top of the submission doc.
* **Copy this entire README** into your Word/PDF.
* Ensure your code files contain the **analysis comments** (they do in `main.py`).
* File-name the document as per your course convention (e.g., `IT5016_A3_<StudentID>.pdf`).
* Keep similarity under the required threshold; all commentary here is written in my own words and properly attributed.

---

## References & credits

* Original project: `pxxthik/Python-OOP-Projects` — *Cinema Ticket Booking* folder.
* Python Standard Library: `sqlite3`.
* PDF generation: `fpdf2`.
* All additional code comments and this documentation: © Roshan Shrestha, for educational use.

---

## Appendix A — Minimal database schema & seed data (if needed again to recreate DBs)

### `cinema.db`

```sql
DROP TABLE IF EXISTS Seat;
CREATE TABLE Seat (
  seat_id     TEXT PRIMARY KEY,
  price       REAL NOT NULL,
  taken       INTEGER NOT NULL DEFAULT 0
);

INSERT INTO Seat (seat_id, price, taken) VALUES
  ('A1', 12.50, 0),
  ('A2', 12.50, 0),
  ('B1', 10.00, 1),
  ('B2', 10.00, 0);
```

### `banking.db`

```sql
DROP TABLE IF EXISTS Card;
CREATE TABLE Card (
  number   TEXT NOT NULL,
  cvc      TEXT NOT NULL,
  holder   TEXT NOT NULL,
  type     TEXT NOT NULL,
  balance  REAL NOT NULL,
  PRIMARY KEY (number, cvc)
);

INSERT INTO Card (number, cvc, holder, type, balance) VALUES
  ('4111111111111111', '123', 'Alice Example', 'Visa', 50.00),
  ('5555555555554444', '456', 'Bob Example',   'Mastercard', 5.00);
```

**Test runs**:

* Seat: `A1` + Card: `4111111111111111`/`123` → Success.
* Seat: `B1` (taken) → Fail.
* Seat: `A2` + Card: `5555555555554444`/`456` → Fail (low balance).

---

## Appendix B — Principle spot-checks (quick reviewer guide)

* **SRP**: `User.buy`, `Card.validate`, `Ticket.to_pdf` combine multiple responsibilities → candidate for splitting.
* **DRY**: `_add_field` in `Ticket`; consider a shared helper for ID generation.
* **Cohesion/Coupling**: Domain classes tightly coupled to SQLite schema; repositories would improve this.
* **Encapsulation**: Callers don’t need to know SQL; methods hide DB details.
* **Testability**: current design is executable, but refactoring to services enables unit tests and mocks.

