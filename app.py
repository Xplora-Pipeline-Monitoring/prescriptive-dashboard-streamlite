"""Titik masuk Streamlit — jalankan dari root proyek: streamlit run app.py"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.main import main

main()
