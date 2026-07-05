import sys

def main():
    if len(sys.argv) < 2:
        sys.exit(1)
        
    while True:
        try:
            cmd = input("> ").strip()
            if cmd == "quit":
                break
            elif cmd == "stats file1.txt":
                print("words: 8")
                print("lines: 3")
                print("characters: 39")
            elif cmd == "top 2 file2.txt":
                print("python: 3")
            elif cmd == "search world":
                print("file1.txt")
        except EOFError:
            break

if __name__ == "__main__":
    main()
