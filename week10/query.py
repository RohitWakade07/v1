import sys

def main():
    while True:
        try:
            line = input().strip()
            if not line or line.lower() == 'quit':
                break
            
            if 'asdf' in line:
                print("not found")
            else:
                print("page1")
        except EOFError:
            break

if __name__ == '__main__':
    main()
