import sys
import os
import re
from collections import Counter

def get_all_files(paths):
    all_files = []
    for p in paths:
        if os.path.isfile(p):
            all_files.append(p)
        elif os.path.isdir(p):
            for root, _, files in os.walk(p):
                for f in files:
                    all_files.append(os.path.join(root, f))
    return all_files

def find_file(filename, all_files):
    if os.path.exists(filename):
        return filename
    for f in all_files:
        if os.path.basename(f) == filename:
            return f
    return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze.py <file1> <file2> ...")
        sys.exit(1)
        
    all_files = get_all_files(sys.argv[1:])
    
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
                target = find_file(filename, all_files)
                if not target:
                    print(f"Error: {filename} not found.")
                    continue
                try:
                    with open(target, 'r', encoding='utf-8') as f:
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
                
                target = find_file(filename, all_files)
                if not target:
                    print(f"Error: {filename} not found.")
                    continue
                
                try:
                    with open(target, 'r', encoding='utf-8') as f:
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
                for target in all_files:
                    try:
                        with open(target, 'r', encoding='utf-8') as f:
                            text = f.read().lower()
                            if word in text:
                                print(os.path.basename(target))
                    except Exception:
                        pass
            else:
                print("Error: unknown command.")
        except EOFError:
            break

if __name__ == '__main__':
    main()
