from collections import UserDict
from datetime import datetime, timedelta
import re
import pickle

def input_error(func):
    def wrapper(args, book):
        try:
            return func(args, book)
        except IndexError:
            return "Not enough arguments"
        except KeyError:
            return "Contact not found"
        except ValueError as e:
            return f"{e}"
        except Exception as e:
            return f"Unexpected error: {e}"
    return wrapper

class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class Name(Field):
		pass

class Phone(Field):
    def __init__(self, value):
        cleaned = self.validate(value)
        super().__init__(cleaned)
    
    def validate(self, value):
        if not isinstance(value, str):
            raise TypeError('Phone number must be a string')
        value = value.strip().replace(' ', '').replace('-', '')
          
        if not re.fullmatch(r'\d{10}', value):
            raise ValueError('Phone number must have 10 digits')
        return value
          
class Birthday(Field):
    def __init__(self, value):
        parsed = self.validate(value)
        super().__init__(parsed)
    
    def validate(self, value):
        if not isinstance(value, str):
            raise TypeError('Birthday must be a string in format DD.MM.YYYY')
        try:
            birthday_date = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
             raise ValueError('Invalid date format. Use DD.MM.YYYY')
        if birthday_date > datetime.now().date():
            raise ValueError('Barthday can not be in the future')
        return birthday_date

class Record:
    def __init__(self, name):
        self.original_name = name
        self.name = Name(name.lower())
        self.phones = []
        self.birthday = None

    def add_phone(self, phone_number):
        phone = Phone(phone_number)
        self.phones.append(phone)

    def remove_phone(self, phone_number):
        for phone in self.phones:
            if phone.value == phone_number:
                self.phones.remove(phone)
                return True
        return False
                  
    def edit_phone(self, old_number, new_number):
        for i, phone in enumerate(self.phones):
            if phone.value == old_number:
                self.phones[i] = Phone(new_number)
                return True
        return False
        
    def find_phone(self, phone_number):
        for phone in self.phones:
            if phone.value == phone_number:
                return phone
        return None
    
    def add_birthday(self, birthday_date):
        self.birthday = Birthday(birthday_date)

    def __str__(self):
        phones = '; '.join(p.value for p in self.phones)
        birthday = f", birthday: {self.birthday.value.strftime('%d.%m.%Y')}" if self.birthday else ""
        return f"Contact name: {self.original_name.capitalize()}, phones: {phones}{birthday}"

class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name.lower())
    
    def delete(self, name):
        if name in self.data:
            del self.data[name.lower()]

    def get_upcoming_birthdays(self):
        today_date = datetime.today().date()
        next_week_start = today_date + timedelta(days=(7 - today_date.weekday()))
        next_week_end = next_week_start + timedelta(days=6)

        greetings = []

        for record in self.data.values():
            if not record.birthday:
                continue  # пропускаємо, якщо день народження не вказано

            birthday_date = record.birthday.value  # тип datetime.date
            birthday_this_year = birthday_date.replace(year=today_date.year)

            if birthday_this_year < today_date:
                birthday_this_year = birthday_this_year.replace(year=today_date.year + 1)

            if next_week_start <= birthday_this_year <= next_week_end:
                greeting_date = birthday_this_year

                if greeting_date.weekday() in (5, 6):  # Saturday/Sunday
                    greeting_date += timedelta(days=(7 - greeting_date.weekday()))  # перенесення на понеділок

                greetings.append({
                    "name": record.name.value,
                    "greeting_date": greeting_date.strftime("%A, %d.%m.%Y")
                    })

        return greetings
    
    def save_to_file(self, filename):
        with open(filename, "wb") as file:
            pickle.dump(self, file)

    @staticmethod
    def load_from_file(filename):
        try:
            with open(filename, "rb") as file:
                return pickle.load(file)
        except (FileNotFoundError, EOFError):
            return AddressBook()

    def __repr__(self):
        return '\n'.join(str(record) for record in self.data.values())

@input_error
def add_contact(args, book):
    name = args[0]
    phone = args[1]
    record = book.find(name)
    if record:
        record.add_phone(phone)
        return f"Phone added to {name.capitalize()}"
    else:
        record = Record(name)
        record.add_phone(phone)
        book.add_record(record)
        return f"Contact {name.capitalize()} created with phone {phone}"

@input_error
def change_phone(args, book):
    name, old_phone, new_phone = args
    record = book.find(name)
    if not record:
        raise KeyError
    if record.edit_phone(old_phone, new_phone):
        return f"Phone updated for {name.capitalize()}"
    return "Old phone not found"

@input_error
def show_phones(args, book):
    name = args[0]
    record = book.find(name)
    if not record:
        raise KeyError
    if not record.phones:
        return f"{name.capitalize()} has no phones"
    return f"Phones for {name. capitalize()}: " + ', '.join(p.value for p in record.phones)

def show_all(args, book):
    if not book.data:
        return "Address book is empty"
    return '\n'.join(str(record) for record in book.data.values())

@input_error
def add_birthday(args, book):
    name = args[0]
    birthday = args[1]
    record = book.find(name)
    if not record:
        raise KeyError
    record.add_birthday(birthday)
    return f"Birthday added to {name.capitalize()}"

@input_error
def show_birthday(args, book):
    name = args[0]
    record = book.find(name)
    if not record:
        raise KeyError
    if not record.birthday:
        return f"No birthday set for {name.capitalize()}"
    return f"{name.capitalize()}'s birthday is {record.birthday.value.strftime('%d.%m.%Y')}"

@input_error
def birthdays(args, book):
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No birthdays in the next 7 days"
    return "\n".join(f"Congratulate {entry['name']} on {entry['greeting_date']}" for entry in upcoming)

def parse_input(user_input):
    parts = user_input.strip().split()
    return parts[0].lower(), parts[1:]

def main():
    FILENAME = "addressbook.pkl"  
    book = AddressBook.load_from_file(FILENAME)
    
    print("Welcome to the assistant bot!")
    
    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)

        if command in ["exit", "close"]:
            book.save_to_file(FILENAME)
            print("Good bye my dear fiend :-(  I'll miss you so much!!!")
            break
        elif command == "hello":
            print("How can I help you?")
        elif command == "add":
            print(add_contact(args, book))
        elif command == "change":
            print(change_phone(args, book))
        elif command == "phone":
            print(show_phones(args, book))
        elif command == "all":
            print(show_all([],book))
        elif command == "add-birthday":
            print(add_birthday(args, book))
        elif command == "show-birthday":
            print(show_birthday(args, book))
        elif command == "birthdays":
            print(birthdays(args, book))
        else:
            print("Invalid command.")

if __name__ == "__main__":
    main()