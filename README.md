# DAAGS-research-project
Data Analytics AI-Based Generation System
AI-based synthetic transactional data generation system for dynamic data analytics education.
AI-powered synthetic data generation system built in Python. Generates realistic transactional datasets using weighted distributions, regional behavior, Faker, CSV inputs, and PostgreSQL, with OpenRouter LLM integration for natural-language scenario-driven data generation.
vscode setup to run the program:
1. git clone 
Clone the repository with the link on the github page
2. ```cd to where the folder is```
Move into the folder
3. Create a virtual environment by pressing ctrl+shift+p then searching for "Python: Create Environment". Probably version 3.13+
For cleanliness
4. ```pip install peewee psycopg2-binary faker python-dotenv psycopg2```
Install the required libraries to the virtual environment
5. Setup the .env and add the amazon_products.csv into the input folder
6. ```python -m daags_engine.run```
Run the program

You also might need to install PostgreSQL onto your computer
