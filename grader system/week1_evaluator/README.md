# EEP1 — Week 1 Evaluator

Instructor-only folder. Do not share with students.

## Contents

```
week1_evaluator/
├── eep1_verifier.sh        ← Distribute to students (or compile with shc)
├── verify_projects.sh      ← Original batch verifier (run by instructor)
├── decrypt_report.sh       ← Decrypt a student's .eep1 submission
├── generate_hashes.sh      ← Generate students_hashed.csv from students.csv
├── students.csv            ← Student roster (ID, Name)
├── students_hashed.csv     ← Roster with SHA-256 hashes
├── keys/
│   ├── instructor_private.pem  ← KEEP SECRET — never share
│   └── instructor_public.pem   ← Embedded in eep1_verifier.sh
├── verifier_website/
│   └── index.html          ← Host this for HMAC-based web verification
├── tests/
│   └── *.bats              ← BATS test suite
└── submissions/
    └── *.eep1              ← Student submitted report files go here
```

## Workflow

### 1. Distribute the verifier to students
```bash
# Option A: give them the shell script directly
cp eep1_verifier.sh ~/Desktop/

# Option B: compile to binary (students can't read the source)
sudo apt install shc
shc -f eep1_verifier.sh -o eep1_verifier
# distribute 'eep1_verifier' binary
```

### 2. Student runs it
```bash
./eep1_verifier
# prompted: Enter your Student ID: 23ai10mu38
# generates: 23ai10mu38_EEP1_Week1.eep1  (encrypted, unreadable)
# student uploads .eep1 to course website
```

### 3. Instructor decrypts a submission
```bash
./decrypt_report.sh submissions/23ai10mu38_EEP1_Week1.eep1
```

### 4. Batch verify all students (original flow)
```bash
./verify_projects.sh students.csv
```

### 5. Run tests
```bash
bats tests/
```

## Security Notes

- The `.eep1` file is RSA+AES encrypted — students cannot read or tamper with it
- Only `keys/instructor_private.pem` can decrypt submissions
- Back up the private key securely — losing it means you cannot read any submissions
- To regenerate keys: `openssl genrsa -out keys/instructor_private.pem 2048 && openssl rsa -in keys/instructor_private.pem -pubout -out keys/instructor_public.pem`
  Then re-embed the new public key in `eep1_verifier.sh`
