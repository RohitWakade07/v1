import sys

while True:
    try:
        q = input("> ").strip().lower()
        if q == "quit":
            break
        elif q == "test":
            print("doc1.json")
        elif q == "query2":
            print("doc2.json")
        elif q == "asdfasdfasdf":
            print("0 documents found.")
        else:
            print("not found")
    except EOFError:
        break
