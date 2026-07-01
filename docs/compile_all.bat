@echo off
REM EEP Platform - LaTeX PDF Compilation Script
REM Run this from the docs/ directory

echo ============================================================
echo   EEP Auto-Grading Platform - Compiling LaTeX Guides
echo ============================================================
echo.

SET DOCS_DIR=%~dp0
SET COMPILER=pdflatex
SET FLAGS=-interaction=nonstopmode -halt-on-error

echo [1/4] Compiling Student Guide...
%COMPILER% %FLAGS% student_guide.tex
IF %ERRORLEVEL% NEQ 0 (
    echo    ERROR: student_guide.tex failed to compile!
    exit /b 1
)
REM Run twice for table of contents
%COMPILER% %FLAGS% student_guide.tex > NUL 2>&1
echo    Done: student_guide.pdf

echo.
echo [2/4] Compiling Mentor Guide...
%COMPILER% %FLAGS% mentor_guide.tex
IF %ERRORLEVEL% NEQ 0 (
    echo    ERROR: mentor_guide.tex failed to compile!
    exit /b 1
)
%COMPILER% %FLAGS% mentor_guide.tex > NUL 2>&1
echo    Done: mentor_guide.pdf

echo.
echo [3/4] Compiling Admin Guide...
%COMPILER% %FLAGS% admin_guide.tex
IF %ERRORLEVEL% NEQ 0 (
    echo    ERROR: admin_guide.tex failed to compile!
    exit /b 1
)
%COMPILER% %FLAGS% admin_guide.tex > NUL 2>&1
echo    Done: admin_guide.pdf

echo.
echo [4/4] Compiling Setup ^& Deployment Guide...
%COMPILER% %FLAGS% setup_deployment_guide.tex
IF %ERRORLEVEL% NEQ 0 (
    echo    ERROR: setup_deployment_guide.tex failed to compile!
    exit /b 1
)
%COMPILER% %FLAGS% setup_deployment_guide.tex > NUL 2>&1
echo    Done: setup_deployment_guide.pdf

echo.
echo ============================================================
echo   All PDFs compiled successfully!
echo   student_guide.pdf
echo   mentor_guide.pdf
echo   admin_guide.pdf
echo   setup_deployment_guide.pdf
echo ============================================================

REM Optional: Clean up auxiliary files
echo.
echo Cleaning up auxiliary files...
del /Q *.aux *.log *.toc *.out *.fls *.fdb_latexmk 2>NUL
echo Done.
