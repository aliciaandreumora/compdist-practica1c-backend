### Computación Distribuida: Practica 1C

### Application

#### Name:
App de Juegos

#### Description:
Gamelisting web app

#### Features:
List, add, update and remove games. Play tic-tac-toe.

#### Setting up and running:

Get the source code.

Create .env-file to project root with following contents:
>DATABASE_URL="postgresql:///database_name"
> 
>SECRET_KEY="insert a secret key here"

Activate virtual environment and install project dependencies:

>$ python3 -m venv venv

>$ source venv/bin/activate

>$ pip install -r ./requirements.txt

Define database tables from schema.sql:

>$ psql (database_name) < schema.sql

Run the Flask application:

>$ flask run

Open the flask-webpage with your browser.

