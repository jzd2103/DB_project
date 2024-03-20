import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, url_for, render_template, g, redirect, Response

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

DATABASE_USERNAME = "el3194"
DATABASE_PASSWRD = "el3194"
DATABASE_HOST = "35.212.75.104" # change to 34.28.53.86 (34.148.107.47) if you used database 2 for part 2
DATABASEURI = f"postgresql://{DATABASE_USERNAME}:{DATABASE_PASSWRD}@{DATABASE_HOST}/proj1part2"

# This line creates a database engine that knows how to connect to the URI above.
engine = create_engine(DATABASEURI)

@app.before_request
def before_request():
	"""
	This function is run at the beginning of every web request 
	(every time you enter an address in the web browser).
	We use it to setup a database connection that can be used throughout the request.

	The variable g is globally accessible.
	"""
	try:
		g.conn = engine.connect()
	except:
		print("uh oh, problem connecting to database")
		import traceback; traceback.print_exc()
		g.conn = None

@app.teardown_request
def teardown_request(exception):
	"""
	At the end of the web request, this makes sure to close the database connection.
	If you don't, the database could run out of memory!
	"""
	try:
		g.conn.close()
	except Exception as e:
		pass


@app.route('/')
def home():
	post_query = """Select username, caption 
					From Posts Natural Join Make Natural Join Users
					Order by Date_Posted DESC
					Limit 5"""
	cursor = g.conn.execute(text(post_query))
	posts = []

	for username, caption in cursor:
		posts.append({'username': username, 'caption': caption})

	cursor.close()
	return render_template("feed.html", posts=posts)

@app.route('/Recipes')
def recipes():
	recipe_query = """select Username, Recipe_Name, Description, Ingredients, Directions, Cook_Time, Tag_Name 
					  from recipes natural join have_recipe_tag natural join tags natural join users natural join create_recipe"""
	cursor = g.conn.execute(text(recipe_query))	
	recipes = []

	for Username, Recipe_Name, Description, Ingredients, Directions, Cook_Time, Tag_Name in cursor:
		recipes.append({'username': Username, 'recipe_name': Recipe_Name.replace('\"', ''), 'description': Description.replace('\"', ''), 
				        'ingredients': Ingredients, 'directions': Directions, 'cook_time': Cook_Time, 'tag': Tag_Name})

	cursor.close()
	return render_template("recipe.html", recipes=recipes)

@app.route('/Profile')
def profile():
	return render_template("profile.html")


# # Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
	# accessing form inputs from user
	name = request.form['name']
	
	# passing params in for each variable into query
	params = {}
	params["new_name"] = name
	g.conn.execute(text('INSERT INTO test(name) VALUES (:new_name)'), params)
	g.conn.commit()
	return redirect('/')


@app.route('/login')
def login():
	return render_template("login.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        address = request.form.get('address', '')
        bio = request.form.get('bio', '')
        dob = request.form.get('dob')
        username = request.form.get('username')
        password = request.form.get('password')

        params = {
            "new_name": name,
            "new_add": address,
            "new_bio": bio,
            "new_dob": dob,
            "new_username": username,
            "new_password": password
        }

        insertion_query = """
            INSERT INTO Users (Name, Address, Biography, Date_of_Birth, Username, Password)
            VALUES (:new_name, :new_add, :new_bio, :new_dob, :new_username, :new_password)
        """

        g.conn.execute(text(insertion_query), params)
        g.conn.commit()

        return redirect('/')
    
    return render_template("register.html")

if __name__ == "__main__":
	import click

	@click.command()
	@click.option('--debug', is_flag=True)
	@click.option('--threaded', is_flag=True)
	@click.argument('HOST', default='0.0.0.0')
	@click.argument('PORT', default=8111, type=int)
	
	def run(debug, threaded, host, port):
		"""
		This function handles command line parameters.
		Run the server using:

			python server.py

		Show the help text using:

			python server.py --help

		"""

		HOST, PORT = host, port
		print("running on %s:%d" % (HOST, PORT))
		app.run(host=HOST, port=PORT, debug=True, threaded=threaded)

run()
