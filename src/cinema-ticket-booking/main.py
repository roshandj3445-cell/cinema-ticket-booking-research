from fpdf import FPDF
import random
import string
import sqlite3

# This program demonstrates Object-Oriented Programming (OOP) in Python.
# It also shows interaction with SQLite databases, basic input handling,
# and dynamic PDF generation using the fpdf2 library.
# Principles visible here: SRP, DRY, Cohesion/Coupling, Encapsulation.


class User:
    """Represents a user that can buy a cinema Seat"""

    def __init__(self, name):
        self.name = name  # Encapsulation: storing user's name as instance data.

    def buy(self, seat, card):
        """
        Buys the ticket if the card is valid.

        Principles:
        - SRP Violation: This method does multiple things (checks seat, validates card,
          updates seat, generates ticket). Could be refactored into smaller functions
          or even a separate PaymentProcessor class to reduce responsibilities.
        - Cohesion: High cohesion for the concept "buy" but low separation of concerns.

        Improvement:
        - Separate seat availability check, payment validation, and ticket generation
          into their own functions or service classes.
        """
        if seat.is_free():  # Low coupling: seat handles its own availability check.
            if card.validate(price=seat.get_price()):  # card handles its own validation logic.
                seat.occupy()
                ticket = Ticket(user=self, price=seat.get_price(), seat_number=seat.seat_id)
                ticket.to_pdf()
                return "Purchase Successful!"
            else:
                return "There was a problem with your card!"
        else:
            return "Seat is taken!"


class Seat:
    """Represents a cinema seat that can be taken from a User"""

    database = 'cinema.db'  # SRP violation risk: Hard-coded dependency on database file.

    def __init__(self, seat_id):
        self.seat_id = seat_id

    def get_price(self):
        """
        Get the price of the certain seat.

        Principles:
        - Encapsulation: This method hides how the price is retrieved (from DB).
        - Coupling: High coupling to the database schema (table & column names hardcoded).

        Improvement:
        - Move DB logic into a separate repository/data access class.
        - Use context managers (`with sqlite3.connect(...) as conn`) to auto-close connections.
        """
        try:
            connection = sqlite3.connect(self.database)
            cursor = connection.cursor()
            cursor.execute("""
                SELECT price FROM Seat WHERE seat_id = ?
            """, [self.seat_id])
            result = cursor.fetchone()
            connection.close()

            if result:
                return result[0]
            else:
                raise ValueError(f"Seat ID {self.seat_id} not found.")
        except Exception as e:
            print(f"Error fetching seat price: {e}")
            return 0

    def is_free(self):
        """
        Check in the database if a seat is taken or not.

        Principles:
        - Encapsulation: Hides the details of checking seat status from outside code.
        - Cohesion: Focused only on availability check.
        - Coupling: Again, tightly bound to DB schema.

        Improvement:
        - Could cache seat data after fetching instead of opening a new DB connection every time.
        """
        try:
            connection = sqlite3.connect(self.database)
            cursor = connection.cursor()
            cursor.execute("""
                SELECT taken FROM Seat WHERE seat_id = ?
            """, [self.seat_id])
            result = cursor.fetchone()
            connection.close()

            if result is None:
                raise ValueError(f"Seat ID {self.seat_id} not found.")

            return result[0] == 0
        except Exception as e:
            print(f"Error checking seat availability: {e}")
            return False

    def occupy(self):
        """
        Change value of taken in the database from 0 to 1 if seat is free.

        Principles:
        - Encapsulation: The seat object changes its own state in the database.
        - SRP: Maintains single purpose—marking seat as occupied.
        - Coupling: Directly tied to database schema.

        Improvement:
        - Wrap DB operations in a transaction manager or repository pattern.
        """
        if self.is_free():
            try:
                connection = sqlite3.connect(self.database)
                connection.execute("""
                    UPDATE Seat SET taken = ? WHERE seat_id = ?
                """, [1, self.seat_id])
                connection.commit()
                connection.close()
            except Exception as e:
                print(f"Error occupying seat: {e}")


class Card:
    """Represents a bank card needed to finalize a seat purchase"""

    database = 'banking.db'  # Hardcoded dependency—limits flexibility.

    def __init__(self, type, number, cvc, holder):
        # Encapsulation: Storing sensitive card details in object properties.
        self.holder = holder
        self.cvc = cvc
        self.number = number
        self.type = type

    def validate(self, price):
        """
        Checks if card is valid and has balance.
        Subtracts price from balance if valid.

        Principles:
        - SRP Violation: Method both validates card details and updates balance.
        - Coupling: Tied directly to DB schema.
        - Encapsulation: Hides how validation is done from outside classes.

        Improvement:
        - Split into `is_valid()` and `charge(amount)` methods.
        - Use encryption or hashing for card data (security best practice).
        """
        try:
            connection = sqlite3.connect(self.database)
            cursor = connection.cursor()
            cursor.execute("""
                SELECT balance FROM Card WHERE number = ? AND cvc = ?
            """, [self.number, self.cvc])
            result = cursor.fetchone()

            if result:
                balance = result[0]
                if balance >= price:
                    connection.execute("""
                        UPDATE Card SET balance = ? WHERE number = ? AND cvc = ?
                    """, [balance - price, self.number, self.cvc])
                    connection.commit()
                    connection.close()
                    return True
                else:
                    print("Insufficient balance.")
            else:
                print("Invalid card details.")
            connection.close()
            return False
        except Exception as e:
            print(f"Error validating card: {e}")
            return False


class Ticket:
    """Represents a cinema Ticket purchased by a user"""

    def __init__(self, user, price, seat_number):
        # Encapsulation: All ticket details kept as object attributes.
        self.seat_number = seat_number
        self.price = price
        self.id = "".join(random.choice(string.ascii_letters) for _ in range(8))  # DRY: repeated logic for random strings could be utility function.
        self.user = user

    def to_pdf(self):
        """
        Creates a pdf ticket.

        Principles:
        - SRP Violation: Handles both formatting and saving the file.
        - Cohesion: All logic here relates to ticket representation.
        - Dependency: Relies on external library fpdf2.

        Improvement:
        - Extract PDF generation into a separate service/class.
        - Make file path configurable.
        """
        pdf = FPDF(orientation="P", unit='pt', format='A4')
        pdf.add_page()

        pdf.set_font(family="Times", style="B", size=24)
        pdf.cell(w=0, h=80, text="Your Digital Ticket", border=1, ln=1, align="C")

        # Ticket fields
        self._add_field(pdf, "Name", self.user.name)
        self._add_field(pdf, "Ticket ID", self.id)
        self._add_field(pdf, "Price", f"${self.price}")
        self._add_field(pdf, "Seat No", str(self.seat_number))

        filename = f"ticket_{self.id}.pdf"
        pdf.output(filename)
        print(f"Ticket saved as {filename}")

    def _add_field(self, pdf, label, value):
        """
        Helper method to add labeled fields to the PDF.
        DRY Principle: avoids repeating the same cell creation code.
        """
        pdf.set_font(family="Times", style="B", size=14)
        pdf.cell(w=100, h=25, text=f"{label}:", border=1)
        pdf.set_font(family="Times", style="", size=12)
        pdf.cell(w=0, h=25, text=value, border=1, ln=1)
        pdf.cell(w=0, h=5, text="", border=0, ln=1)


if __name__ == "__main__":
    # Input collection: tightly coupled to console, not easily testable.
    # Improvement: Use a separate function or UI to collect inputs.
    name = input("Your full name: ")
    seat_id = input("Preferred seat no: ")
    card_type = input("Your card type: ")
    card_number = input("Your card number: ")
    card_cvc = input("Your card cvc: ")
    card_holder = input("Card holder name: ")

    # OOP: Creating instances and orchestrating their interaction.
    user = User(name=name)
    seat = Seat(seat_id=seat_id)
    card = Card(type=card_type, number=card_number, cvc=card_cvc, holder=card_holder)

    print(user.buy(seat=seat, card=card))
