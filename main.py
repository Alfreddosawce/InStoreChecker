#this program will check all ID against api to see if in-store exists
from target_db import initialize_db
from Target import target_console

def main():

    print("Starting program...")
    initialize_db()
    target_console()
    print("Program finished, check database")


if __name__ == "__main__":
    main()