import sqlite3
import os

DATABASE_NAME = "ebookstore.db"
TABLENAME = "books"


def connect_database() -> sqlite3.Connection:
    """
    connect to SQLite database
    """
    # connect to database
    db = sqlite3.connect(DATABASE_NAME)

    # get database cursor
    cursor = db.cursor()

    # check if the books table exists by count
    query = f"""
    SELECT count(name)
    FROM sqlite_master
    WHERE type='table' AND name='{TABLENAME}'
    """
    cursor.execute(query)

    # if count is 0, table do not exist and create is and populate some records
    if cursor.fetchone()[0] == 0:
        print("Table does not exists, create and populate table")
        create_populate_table(db)

    return db


def create_populate_table(db: sqlite3.Connection) -> None:
    """
    create and populate the books table
    """
    book_records = [
        [3001, "A Tale of Two Cities", "Charles Dickens", 30],
        [3002, "Harry Potter and the Philosopher's Stone", "J.K. Rowling", 40],
        [3003, "The Lion, the Witch and the Wardrobe", "C. S. Lewis", 25],
        [3004, "The Lord of the Rings", "J.R.R Tolkien", 37],
        [3005, "Harry Potter and the Chamber of Secrets", "J.K. Rowling", 25],
        [3006, "Alice in Wonderland", "Lewis Carroll", 12],
        [3007, "Harry Potter and the Prisoner of Azkaban", "J.K. Rowling", 30],
        [3008, "A Game of Thrones", "George R. R. Martin", 27],
        [3009, "Harry Potter and the Goblet of Fire", "J.K. Rowling", 32],
        [3010, "A Clash of Kings", "George R. R. Martin", 29],
        [3011, "A Storm of Swords", "George R. R. Martin", 26],
        [3012, "Harry Potter and the Order of the Phoenix", "J.K. Rowling", 32],
    ]

    cursor = db.cursor()

    # query to create table
    query = f"""
    CREATE TABLE {TABLENAME} (
        id INTEGER PRIMARY KEY, 
        title TEXT, 
        author TEXT, 
        quantity INTEGER);
    """
    cursor.execute(query)

    # loop through book list and populate table
    for record in book_records:
        # query to insert new record for each book
        query = f"""
        INSERT INTO {TABLENAME} (
            id,
            title,
            author,
            quantity
        ) VALUES
            ("{record[0]}", "{record[1]}", "{record[2]}", {record[3]});
        """
        cursor.execute(query)

    # commit change to database
    db.commit()


def add_book(db: sqlite3.Connection, title: str, author: str, qty: int) -> None:
    """
    adding given book info to database
    """
    cursor = db.cursor()

    # insert book record into database
    # the id field is given a NULL value for autoincrement
    # https://www.sqlitetutorial.net/sqlite-autoincrement/
    query = f"""
    INSERT INTO {TABLENAME} (
        id,
        title,
        author,
        quantity
    ) VALUES
        (NULL, "{title}", "{author}", {qty})
    """
    cursor.execute(query)
    db.commit()


def delete_book(db: sqlite3.Connection, book_id) -> None:
    """
    delete a book record by given book id
    """
    cursor = db.cursor()

    # check if the given book id exists
    if not book_id_exists(db, book_id):
        print(f"The given book id '{book_id}' does not exists.")
        return

    query = f"""
    DELETE FROM {TABLENAME}
    WHERE id = {book_id}
    """
    cursor.execute(query)
    db.commit()


def update_book_info(db: sqlite3.Connection, book_id: int, title=None, author=None, qty=None) -> None:
    """
    update book info by given id, field will be be updated if the given value is None
    """
    cursor = db.cursor()

    # check if the given book id exists
    if not book_id_exists(db, book_id):
        print(f"The given book is {book_id} does not exists.")
        return

    # assemble query
    query = f"UPDATE {TABLENAME} SET "

    new_value = []
    # update title if it is truly
    if title:
        new_value.append(f"title = '{title}'")
    # update author if it is truly
    if author:
        new_value.append(f"author = '{author}'")
    # update quantity if it is truly
    if qty:
        new_value.append(f"quantity = {qty}")

    # putting ',' in between values
    while len(new_value):
        query += new_value.pop()
        if len(new_value):
            query += ", "
    query += f" WHERE id = {book_id}"

    cursor.execute(query)
    db.commit()


def book_id_exists(db: sqlite3.Connection, book_id: int) -> None:
    """
    return True if book id exist, or False if book id does not exists
    """
    cursor = db.cursor()

    # check if the given book id exists
    query = f"""
    SELECT count(id)
    FROM books
    WHERE id={book_id}
    """
    cursor.execute(query)

    # return if count is 0, the id does not exists
    if cursor.fetchone()[0] == 0:
        return False

    return True


def search_book(db: sqlite3.Connection, search_for: str) -> None:
    """
    search book by a given string

    Note:   this function 1st make a query for all book, and check for
            a match string, the reason LIKE pattern matching is not used
            it because if the string string includes SQL query other % etc.
            It will be a lot of work work to handle them and for a small
            database manual search is alright in our case
    """
    match_book_id = set()
    cursor = db.cursor()

    # query on all the books
    query = f"SELECT * FROM {TABLENAME}"
    cursor.execute(query)

    # change to lower case for case case insensitive search
    search_for = search_for.lower()

    # loop through all books and check for matching string
    for record in cursor.fetchall():
        id_string = str(record[0])
        title = record[1]
        author = record[2]
        # if the given string match book id add id to match set
        if id_string == search_for:
            match_book_id.add(record[0])
        # if the given string in book title add id to match set
        if search_for in title.lower():
            match_book_id.add(record[0])
        # if the given string in author add id to match set
        if search_for in author.lower():
            match_book_id.add(record[0])

    # return if no match were found
    if len(match_book_id) == 0:
        print(f"No match were found")
        return

    # assemble query
    query = f"SELECT * FROM {TABLENAME} WHERE "
    # pop an id for the 1st condition without OR
    query += f"id = {match_book_id.pop()}"
    for id in match_book_id:
        query += f" OR id = {id}"

    # pass query to show_books for printing
    show_books(db, query)


def show_books(db: sqlite3.Connection, query=None) -> None:
    """
    print books to screen according to query, if a query has not
    pass in, all books will be printed
    """
    cursor = db.cursor()

    # if a query did not pass in, query on all books
    if query == None:
        query = f"SELECT * FROM {TABLENAME};"

    cursor.execute(query)

    # print to screen
    print()
    print("ID".ljust(10), "Title".ljust(50), "Author".ljust(25), "Qty")
    print("-" * 95)
    for record in cursor.fetchall():
        id = str(record[0])
        print(
            id.ljust(10),
            record[1].ljust(50),
            record[2].ljust(25),
            record[3],
        )


def menu_bookstore_inventory() -> int:
    """
    show menu and get user input
    """
    print()
    print("=".rjust(20) + "=" * 30)
    print(" ".rjust(25) + "Bookstore Inventory")
    print("=".rjust(20) + "=" * 30)
    print()
    print("1.".rjust(21) + " Enter Book")
    print("2.".rjust(21) + " Update Book")
    print("3.".rjust(21) + " Delete Book")
    print("4.".rjust(21) + " Search Book")
    print("0.".rjust(21) + " Exit")
    print()

    while True:
        try:
            selection = int(input("Select Your Option: ".rjust(25)))
        except ValueError:
            print("└ Please enter selection by number".rjust(40))
        else:
            break

    return selection


def menu_add_book(db: sqlite3.Connection) -> None:
    """
    handle menu add book
    """
    # get new book info from user with simple check
    title = input("\nPlease enter new title: ")
    if title == "":
        print("Title can not be empty")
        return
    author = input("Please enter new author: ")
    if author == "":
        print("Author can not be empty")
        return
    qty = input("Please enter new quantity: ")
    if qty == "":
        print("Quantity can not be empty")
        return
    else:
        # simple check for int
        try:
            qty = int(qty)
        except ValueError:
            print("Quantity must be a number")
            return

    add_book(db, title, author, qty)


def menu_update_book(db: sqlite3.Connection) -> None:
    """
    handle menu update book
    """
    # show all books
    show_books(db)

    # get book id
    try:
        book_id = int(input("\nPlease enter the book id for update or press enter to return: "))
        # return to main menu
        if book_id == "":
            return
    except ValueError:
        print("Please enter a valid book id")
        return

    # return if book id does not exists
    if not book_id_exists(db, book_id):
        print(f"The given book id '{book_id}' does not exists")
        return

    # get new value from user
    title = input("Please enter new title or press enter to skip: ")
    if title == "":
        title = None
    author = input("Please enter new author or press enter to skip: ")
    if author == "":
        author = None
    qty = input("Please enter new quantity or press enter to skip: ")
    if qty == "":
        qty = None
    else:
        # simple checking on qty
        try:
            qty = int(qty)
        except ValueError:
            print("Quantity must be integer.")
            return

    update_book_info(db, book_id, title, author, qty)


def menu_delete_book(db: sqlite3.Connection) -> None:
    """
    handle menu delete book
    """
    # show all books
    show_books(db)

    # get book id
    try:
        book_id = int(input("\nPlease enter the book id for deletion or press enter to return: "))
        # return to main menu
        if book_id == 0:
            return
    except ValueError:
        print("Please enter a valid book id")
        return

    # pass book id to function
    delete_book(db, book_id)


def menu_search_book(db: sqlite3.Connection) -> None:
    """
    handle menu search book
    """
    # get user search term
    search_for = input("\nPlease enter the your search term or press enter to return: ")
    if search_for == "":
        return
    # pass search term to function
    search_book(db, search_for)


if __name__ == "__main__":

    # change working dir to script location
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    db = connect_database()

    # main loop
    while True:
        user_selection = menu_bookstore_inventory()

        if user_selection == 0:
            exit()
        elif user_selection == 1:
            menu_add_book(db)
        elif user_selection == 2:
            menu_update_book(db)
        elif user_selection == 3:
            menu_delete_book(db)
        elif user_selection == 4:
            menu_search_book(db)
        # elif user_selection == 5:
        #    show_books(db)
        else:
            print("Invalid Selection!!!")

    db.close()
