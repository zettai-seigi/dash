#!/usr/bin/env python3

import sys
print("Python path:", sys.path)

try:
    import streamlit as st
    print("Streamlit import successful!")
    
    # Simple test
    st.title("Test Dashboard")
    st.write("Hello World!")
    
except ImportError as e:
    print(f"Streamlit import failed: {e}")
    print("Trying to install...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "streamlit"])