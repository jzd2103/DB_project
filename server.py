import os, secrets
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, url_for, render_template, g, redirect, Response, flash
from datetime import datetime

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

app.config['SECRET_KEY'] = 'f4de96d218da7e5c0db80c4690b75301'

DATABASE_USERNAME = "el3194"
DATABASE_PASSWRD = "el3194"
DATABASE_HOST = "35.212.75.104" # change to 34.28.53.86 (34.148.107.47) if you used database 2 for part 2
DATABASEURI = f"postgresql://{DATABASE_USERNAME}:{DATABASE_PASSWRD}@{DATABASE_HOST}/proj1part2"

# This line creates a database engine that knows how to connect to the URI above.
engine = create_engine(DATABASEURI)

logged_in = False
user_id = None

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

	global logged_in
	return render_template("feed.html", posts=posts, logged_in=logged_in)

@app.route('/Recipes')
def recipes():
	recipe_query = """select Username, Recipe_Name, Description, Ingredients, Directions, Cook_Time, Tag_Name 
					  from recipes natural join have_recipe_tag natural join tags natural join users natural join create_recipe
					  limit 5"""
	cursor = g.conn.execute(text(recipe_query))	
	recipes = []

	for Username, Recipe_Name, Description, Ingredients, Directions, Cook_Time, Tag_Name in cursor:
		recipes.append({'username': Username, 'recipe_name': Recipe_Name.replace('\"', ''), 'description': Description.replace('\"', ''), 
				        'ingredients': Ingredients, 'directions': Directions, 'cook_time': Cook_Time, 'tag': Tag_Name})

	cursor.close()

	global logged_in
	return render_template("recipe.html", recipes=recipes, logged_in=logged_in)

@app.route('/Profile')
def profile():
	global logged_in

	if(not logged_in):
		flash('You are not logged in', 'danger')
		return redirect('/')
	
	return render_template("profile.html", logged_in=logged_in)

@app.route('/Create')
def create():
	global logged_in

	if(not logged_in):
		flash('You are not logged in', 'danger')
		return redirect('/')

	return render_template("create.html", logged_in=logged_in)

def save_image(form_image):
	random_hex = secrets.token_hex(8)
	_, f_ext = os.path.splitext(form_image.filename)
	image_fn = random_hex + f_ext
	image_path = os.path.join(app.root_path, 'static/images', image_fn)
	form_image.save(image_path)

	return image_fn

def save_video(form_video):
	random_hex = secrets.token_hex(8)
	_, f_ext = os.path.splitext(form_video.filename)
	video_fn = random_hex + f_ext
	video_path = os.path.join(app.root_path, 'static/videos', video_fn)
	form_video.save(video_path)

	return video_fn

@app.route('/create_post', methods=['POST'])
def create_post():
	global logged_in
	global user_id

	caption = request.form['caption']
	video_file = request.files.get('video_file')
	image_file = request.files.get('image_file')

	if video_file.filename == '' and image_file.filename == '':
		flash("Video or Image file required", 'danger')
		return redirect('/Create')
	
	if video_file.filename != '' and image_file.filename != '':
		flash("Upload only one media file", 'danger')
		return redirect('/Create')
	
	current_time = datetime.now()
	formatted_time = current_time.strftime("%m/%d/%y")

	if video_file.filename != '':
		file_path = save_video(video_file)
		insertion_query1 = """INSERT INTO Posts (Caption, Date_Posted, Video_Url)
							  VALUES (:caption, :date, :media_file)
							  RETURNING Post_ID"""		
	elif image_file.filename != '':
		file_path = save_image(image_file)	
		insertion_query1 = """INSERT INTO Posts (Caption, Date_Posted, Image_Url)
							  VALUES (:caption, :date, :media_file)
							  RETURNING Post_ID"""	

	params1 = {'caption': caption, 'date': formatted_time, 'media_file': file_path}
	new_post = g.conn.execute(text(insertion_query1), params1)
	post_id = new_post.fetchone()[0]

	params2 = {'user_id': user_id, 'post_id': post_id}
	insertion_query2 = """INSERT INTO Make (User_ID, Post_ID)
						  VALUES (:user_id, :post_id)"""
		
	g.conn.execute(text(insertion_query2), params2)
	g.conn.commit()

	flash("Post created successfully", 'success')
	return redirect('/')


@app.route('/login', methods=['GET', 'POST'])
def login():
	global logged_in
	global user_id

	if(logged_in):
		flash('You are already logged in', 'danger')
		return redirect('/')
	
	if request.method == 'POST':
		uname_input = request.form['username']
		pword_input = request.form['password']

		if not uname_input or not pword_input:
			flash('Username and Password Required', 'danger')
			return redirect('/login')

		params = {"username": uname_input, "password": pword_input}
		user = g.conn.execute(text("""SELECT User_ID 
							 		  FROM Users 
							 		  WHERE Username = (:username) AND Password = (:password)"""), params).fetchone()
		
		if user:
			logged_in = True
			user_id = user[0]

			flash('Login successful', 'success')
			return redirect('/')
		else:
			flash('Invalid Username or Password', 'danger')
			return redirect('/login')

	return render_template("login.html")

@app.route('/logout')
def logout():
	global logged_in
	global user_id

	if(not logged_in):
		flash('Error: you are not logged in', 'danger')
		return redirect('/')
	
	logged_in = False
	user_id = None
	flash("You have been logged out successfully", 'success')
	return redirect('/')

@app.route('/make_tag', methods=['POST'])
def make_tag():
	global user_id
	tag = request.form.get('tag')
	if not tag:
		flash('Please enter a tag', 'danger')
		return redirect('/Create')

	params = {"tag": tag}

	check_query = """SELECT tag_name 
					 FROM Tags 
					 WHERE tag_name = (:tag)"""

	tag_exists = g.conn.execute(text(check_query), params).fetchone()
	if tag_exists:
		flash("The tag already exists. Try another tag", 'danger')
		return redirect('/Create')

	else:
		insertion_query = """INSERT INTO Tags (Tag_Name)
							 VALUES (:tag)
							 RETURNING Tag_ID"""
			
		new_tag = g.conn.execute(text(insertion_query), params)
		tag_id = new_tag.fetchone()[0]

		params2 = {"user_id": user_id, "tag_id": tag_id}

		insertion_query2 = """INSERT INTO Make_TAG (User_ID, Tag_ID)
							  VALUES (:user_id, :tag_id)"""
		
		g.conn.execute(text(insertion_query2), params2)
		g.conn.commit()


	flash("Tag created successfully", 'success')
	return redirect('/')


@app.route('/register', methods=['GET', 'POST'])
def register():
    global logged_in
    if request.method == 'POST':
        name = request.form.get('name')
        address = request.form.get('address', '')
        bio = request.form.get('bio', '')
        dob = request.form.get('dob')
        username = request.form.get('username')
        password = request.form.get('password')

        if not name or not dob or not username or not password:
            flash('* fields are required', 'danger')
            return redirect('/register')

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

        flash(f"Account created successfully for {name}!", 'success')
        return redirect('/')
    else:
    	return render_template("register.html", logged_in=logged_in)

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
