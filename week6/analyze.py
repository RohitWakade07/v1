import sys
import os
import re
from collections import Counter

def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze.py <file1> <file2> ...")
        sys.exit(1)
        
    files = sys.argv[1:]
    
    while True:
        try:
            cmd_line = input("> ").strip()
            if not cmd_line:
                continue
            parts = cmd_line.split()
            cmd = parts[0]
            args = parts[1:]
            
            if cmd == "quit":
                break
            elif cmd == "stats":
                if len(args) != 1:
                    print("Usage: stats <filename>")
                    continue
                filename = args[0]
                if filename not in files and not os.path.exists(filename):
                    print(f"Error: {filename} not found.")
                    continue
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        num_lines = len(lines)
                        text = "".join(lines)
                        num_words = len(text.split())
                        num_chars = len(text)
                        print(f"Lines: {num_lines}")
                        print(f"Words: {num_words}")
                        print(f"Characters: {num_chars}")
                except Exception as e:
                    print(f"Error reading file: {e}")
            elif cmd == "top":
                if len(args) != 2:
                    print("Usage: top <N> <filename>")
                    continue
                try:
                    n = int(args[0])
                    filename = args[1]
                except ValueError:
                    print("Error: N must be an integer.")
                    continue
                
                if filename not in files and not os.path.exists(filename):
                    print(f"Error: {filename} not found.")
                    continue
                
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        text = f.read().lower()
                        words = re.findall(r'\b\w+\b', text)
                        counts = Counter(words)
                        for word, count in counts.most_common(n):
                            print(f"{word}: {count}")
                except Exception as e:
                    print(f"Error reading file: {e}")
            elif cmd == "search":
                if len(args) != 1:
                    print("Usage: search <word>")
                    continue
                word = args[0].lower()
                for filename in files:
                    if not os.path.exists(filename):
                        continue
                    try:
                        with open(filename, 'r', encoding='utf-8') as f:
                            text = f.read().lower()
                            if word in text:
                                print(filename)
                    except Exception:
                        pass
            else:
                print("Unknown command.")
        except EOFError:
            break

if __name__ == '__main__':
    main()
