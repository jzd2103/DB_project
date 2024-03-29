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
DATABASE_HOST = "35.212.75.104"
DATABASEURI = f"postgresql://{DATABASE_USERNAME}:{DATABASE_PASSWRD}@{DATABASE_HOST}/proj1part2"

# This line creates a database engine that knows how to connect to the URI above.
engine = create_engine(DATABASEURI)

logged_in = False
user_id = None
logged_in_username = None

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
	post_query = """Select username, post_id, caption, image_URL, video_URL
					From Posts Natural Join Make Natural Join Users
					Order by Date_Posted DESC
					"""
	cursor = g.conn.execute(text(post_query))
	posts = []

	for username, post_id, caption, image_url, video_url in cursor:
		comments = []
		comment_query = """Select Username as username1, Comment
						   From Rate Natural Join Users
						   Where post_id = (:post_id)"""
		comment_cursor = g.conn.execute(text(comment_query), {'post_id': post_id})

		for username1, comment in comment_cursor:
			comments.append({'username': username1, 'comment': comment})

		comment_cursor.close()

		rating_query = """select post_id, rating
						  from posts natural join rate
						  where post_id = (:post_id) and rating != 0"""
		
		rating_cursor = g.conn.execute(text(rating_query), {'post_id': post_id})

		yum = 0
		yuck = 0

		for post_id, rating in rating_cursor:
			if rating == 1:
				yum += 1
			elif rating == -1:
				yuck += 1

		rating_cursor.close()

		posts.append({'username': username, 'post_id': post_id, 'caption': caption, 'video_url': video_url, 'image_url': image_url, 'comments': comments, 
				'yum': yum, 'yuck': yuck})

	cursor.close()

	if user_id:
		params = {'user_id': user_id}
		username_query = """Select Username
							From Users
							Where User_ID = (:user_id)"""
		
		loggedin_user = g.conn.execute(text(username_query), params).fetchone()[0]
	else:
		loggedin_user = None
	
	global logged_in
	return render_template("feed.html", posts=posts, logged_in=logged_in, loggedin_user=loggedin_user)

@app.route('/Recipes')
def recipes():
	recipe_query = """Select Username, Recipe_Name, Description, Ingredients, Directions, Cook_Time, Image_URL
					  from Recipes natural join Users natural join Create_recipe"""
	
	cursor = g.conn.execute(text(recipe_query))	
	recipes = []

	for Username, Recipe_Name, Description, Ingredients, Directions, Cook_Time, Image_URL in cursor:
		recipes.append({'username': Username, 'recipe_name': Recipe_Name.replace('\"', ''), 'description': Description.replace('\"', ''), 
						'ingredients': Ingredients, 'directions': Directions, 'cook_time': Cook_Time, 'image_file': Image_URL})

	cursor.close()

	global logged_in
	return render_template("recipe.html", recipes=recipes, logged_in=logged_in)

@app.route('/Profile')
def profile():
	global logged_in
	global user_id
	global logged_in_username

	if(not logged_in):
		flash('You are not logged in', 'danger')
		return redirect('/')

	post_query = """Select username, post_id, caption, image_URL, video_URL
							From Posts Natural Join Make Natural Join Users
							Where User_ID = (:user_id)
							Order by Date_Posted DESC
							"""
			
	recipe_query = """Select Recipe_ID, Username, Recipe_Name, Description, Ingredients, Directions, Cook_Time, Image_URL
							from Recipes natural join Users natural join Create_recipe
							Where User_ID = (:user_id)"""

	user_query = """Select Name, Address, Biography, Date_of_Birth, Username
							From Users Where User_ID = (:user_id)"""

	if(request.args.get('username')):
		username_viewing = request.args.get('username')
		
		params = {'username_viewing': username_viewing}
		query = f"""Select User_ID
					From Users
					Where Username = (:username_viewing)"""
		user_id_viewing = g.conn.execute(text(query), params).fetchone()[0]

		if user_id != user_id_viewing:
			params = {'follower_id': user_id, 'followed_id': user_id_viewing}
			
			check_query = """Select * from Follow
							Where Follower_ID = (:follower_id)
							And Followed_ID = (:followed_id)"""

			if(g.conn.execute(text(check_query), params).fetchone()):
				is_following = True
			else:
				is_following = False
			
			params = params = {'user_id_viewing': user_id_viewing}
			post_query = f"""Select username, post_id, caption, image_URL, video_URL
							From Posts Natural Join Make Natural Join Users
							Where User_ID = (:user_id_viewing)
							Order by Date_Posted DESC
							"""
			
			recipe_query = f"""Select Recipe_ID, Username, Recipe_Name, Description, Ingredients, Directions, Cook_Time, Image_URL
							from Recipes natural join Users natural join Create_recipe
							Where User_ID = (:user_id_viewing)"""

			user_query = f"""Select Name, Address, Biography, Date_of_Birth, Username
							From Users Where User_ID = (:user_id_viewing)"""
		
			posts, recipes, users = [], [], []
			cursor = g.conn.execute(text(post_query), params)

			for username, post_id, caption, image_url, video_url in cursor:
				posts.append({'username': username, 'post_id': post_id, 'caption': caption, 'video_url': video_url, 'image_url': image_url})

			cursor = g.conn.execute(text(recipe_query), params)	

			for Recipe_ID, Username, Recipe_Name, Description, Ingredients, Directions, Cook_Time, Image_URL in cursor:
				recipes.append({'recipe_id': Recipe_ID, 'username': Username, 'recipe_name': Recipe_Name.replace('\"', ''), 'description': Description.replace('\"', ''), 
								'ingredients': Ingredients, 'directions': Directions, 'cook_time': Cook_Time, 'image_file': Image_URL})
			
			cursor = g.conn.execute(text(user_query), params)

			for Name, Address, Biography, Date_of_Birth, Username in cursor:
				users.append({'name': Name, 'address': Address, 'biography': Biography, 'date_of_birth': Date_of_Birth, 'username': Username})
			
			cursor.close()

			following_query = f"""Select count(*)
								From Follow
								Where Follower_ID = (:user_id_viewing)"""
			number_following = g.conn.execute(text(following_query), params).fetchone()[0]

			followers_query = f"""Select count(*)
								From Follow
								Where Followed_ID = (:user_id_viewing)"""
			number_followers = g.conn.execute(text(followers_query), params).fetchone()[0]

			return render_template("profile.html", logged_in=logged_in, logged_in_username=logged_in_username, users=users, posts=posts, recipes=recipes, 
						  username_viewing=username_viewing, is_following=is_following, number_followers=number_followers, number_following=number_following)
		else:
			return redirect('/Profile')
	else:
		posts, recipes, users = [], [], []
		params = {'user_id': user_id}
		cursor = g.conn.execute(text(post_query), params)

		for username, post_id, caption, image_url, video_url in cursor:
			posts.append({'username': username, 'post_id': post_id, 'caption': caption, 'video_url': video_url, 'image_url': image_url})

		cursor = g.conn.execute(text(recipe_query), params)	

		for Recipe_ID, Username, Recipe_Name, Description, Ingredients, Directions, Cook_Time, Image_URL in cursor:
			recipes.append({'recipe_id': Recipe_ID, 'username': Username, 'recipe_name': Recipe_Name.replace('\"', ''), 'description': Description.replace('\"', ''), 
							'ingredients': Ingredients, 'directions': Directions, 'cook_time': Cook_Time, 'image_file': Image_URL})
		
		cursor = g.conn.execute(text(user_query), params)

		for Name, Address, Biography, Date_of_Birth, Username in cursor:
			users.append({'name': Name, 'address': Address, 'biography': Biography, 'date_of_birth': Date_of_Birth, 'username': Username})
		
		cursor.close()

		following_query = f"""Select count(*)
							  From Follow
							  Where Follower_ID = (:user_id)"""
		number_following = g.conn.execute(text(following_query), params).fetchone()[0]

		followers_query = f"""Select count(*)
							  From Follow
							  Where Followed_ID = (:user_id)"""
		number_followers = g.conn.execute(text(followers_query), params).fetchone()[0]

		return render_template("profile.html", logged_in=logged_in, users=users, posts=posts, recipes=recipes, logged_in_username=logged_in_username,
						 username_viewing=logged_in_username, number_followers=number_followers, number_following=number_following)

@app.route('/UpdateProfile', methods=['POST', 'GET'])
def update_profile():
	global logged_in
	global user_id

	if(not logged_in):
		flash('You are not logged in', 'danger')
		return redirect('/')
	
	if request.method == 'POST':
		name = request.form.get('name')
		address = request.form.get('address')
		bio = request.form.get('bio')
		dob = request.form.get('dob')
		username = request.form.get('username')
		password = request.form.get('password')

		if not name and not address and not bio and not dob and not username and not password:
			flash("Nothing was entered", 'danger')
			return redirect('/UpdateProfile')

		params = {}
		
		update_query = "Update Users Set "

		if name:
			update_query += "Name = (:new_name), "
			params['new_name'] = name
		if address:
			update_query += "Address = (:new_add), "
			params['new_add'] = address
		if bio:
			update_query += "Biography = (:new_bio), "
			params['new_bio'] = bio
		if dob:
			update_query += "Date_of_Birth = (:new_dob), "
			params['new_dob'] = dob
		if username:
			update_query += "Username = (:new_username), "
			params['new_username'] = username
		if password:
			update_query += "Password = (:new_password), "
			params['new_password'] = password

		update_query = update_query.rstrip(', ')
		update_query += "Where User_ID = (:user_id)"
		params['user_id'] = user_id

		g.conn.execute(text(update_query), params)
		g.conn.commit()

		flash("Your profile has been updated successfully", 'success')
		return redirect('/Profile')

	return render_template('update_profile.html', logged_in=logged_in)

@app.route('/Follow', methods=['POST'])
def follow():
	global user_id
	global logged_in
	
	followed_username = request.form.get('followed_username')

	params = {'followed_username': followed_username}
	get_query = """Select User_ID
				   From Users
				   Where Username = (:followed_username)"""
	
	get_follow_id = g.conn.execute(text(get_query), params).fetchone()[0]

	params = {'follower_id': user_id, 'followed_id': get_follow_id}
	
	check_query = """Select * from Follow
					 Where Follower_ID = (:follower_id)
					 And Followed_ID = (:followed_id)"""

	follow_exists = g.conn.execute(text(check_query), params).fetchone()

	if follow_exists:
		flash(f'You already follow this user {followed_username}', 'danger')
		return redirect(f'/Profile?username={followed_username}')
	else:
		insertion_query = """INSERT INTO Follow (Follower_ID, Followed_ID)
							VALUES (:follower_id, :followed_id)"""
		
		g.conn.execute(text(insertion_query), params)
		g.conn.commit()

		flash('You are now following ' + followed_username, 'success')
		return redirect(f'/Profile?username={followed_username}')

@app.route('/Unfollow', methods=['POST'])
def unfollow():
	global user_id
	global logged_in

	followed_username = request.form.get('followed_username')

	params = {'followed_username': followed_username}
	get_query = """Select User_ID
				   From Users
				   Where Username = (:followed_username)"""
	
	get_follow_id = g.conn.execute(text(get_query), params).fetchone()[0]

	params = {'follower_id': user_id, 'followed_id': get_follow_id}
	
	check_query = """Select * from Follow
					 Where Follower_ID = (:follower_id)
					 And Followed_ID = (:followed_id)"""

	follow_exists = g.conn.execute(text(check_query), params).fetchone()

	if not follow_exists:
		flash('You do not follow this user', 'danger')
		return redirect(f'/Profile?username={followed_username}')
	else:
		deletion_query = """DELETE FROM Follow
							WHERE Follower_ID = (:follower_id) AND Followed_ID = (:followed_id)"""
		
		g.conn.execute(text(deletion_query), params)
		g.conn.commit()

		flash('You have unfollowed ' + followed_username, 'success')
		return redirect(f'/Profile?username={followed_username}')


@app.route('/rate', methods=['GET', 'POST'])
def rate():
	global logged_in
	global user_id

	if(not logged_in):
		flash('You are not logged in', 'danger')
		return redirect('/')
	
	if request.method == 'POST':
		post_id = request.form['post_id']
		comment = request.form['comment']

		if not comment:
			flash("No comment entered")
			return redirect('/')
		
		params = {'post_id': post_id, 'comment': comment, 'user_id': user_id}

		check_query = """Select * from Rate where user_id = (:user_id) and post_id = (:post_id)"""
		exists_rate = g.conn.execute(text(check_query), params).fetchone()

		if exists_rate:
			set_comment = """Update Rate Set Comment = (:comment) Where user_id = (:user_id) AND post_id = (:post_id)"""
			g.conn.execute(text(set_comment), params)
			flash('Rate updated', 'success')
		else:
			insertion_query = """INSERT INTO Rate (User_ID, Post_ID, Comment)
								 VALUES (:user_id, :post_id, :comment)"""
			g.conn.execute(text(insertion_query), params)
			flash('Rating added successfully', 'success')

		g.conn.commit()
		return redirect('/')
	
	post_id = request.args.get('post_id')
	rating = request.args.get('rating')
	params = {'user_id': user_id, 'post_id': post_id, 'rating': rating}

	check_query = """Select * from Rate where user_id = (:user_id) and post_id = (:post_id)"""
	exists_rate = g.conn.execute(text(check_query), params).fetchone()

	if exists_rate:
		update_rate = """Update Rate Set Rating = (:rating) Where user_id = (:user_id) AND post_id = (:post_id)"""
		g.conn.execute(text(update_rate), params)
		flash('Rate updated', 'success')
	else: 
		insertion_query = """INSERT INTO Rate (User_ID, Post_ID, Rating)
							VALUES (:user_id, :post_id, :rating)"""
	
		g.conn.execute(text(insertion_query), params)
		flash('Rating added successfully', 'success')
		
	g.conn.commit()
	return redirect('/')

@app.route('/AddTag', methods=['POST', 'GET'])
def add_tag():
	global logged_in

	if(not logged_in):
		flash('You are not logged in', 'danger')
		return redirect('/')
	
	if request.method == 'POST':
		post_id = request.form.get('post_id', None)
		recipe_id = request.form.get('recipe_id', None)
		tag = request.form['tag']

		if not tag:
			if post_id:
				flash("Nothing was entered", 'danger')
				return redirect(f'/AddTag?post_id={post_id}')
			else:
				flash("Nothing was entered", 'danger')
				return redirect(f'/AddTag?recipe_id={recipe_id}')

		param = {'tag': tag}
		select_query = """Select Tag_ID from Tags Where Tag_Name = (:tag)"""
		tag_exists = g.conn.execute(text(select_query), param).fetchone()
		
		if tag_exists:
			tag_id = tag_exists[0]
			if post_id:
				param = {'post_id': post_id, 'tag_id': tag_id}
				select_exists_query = """Select * from Have_Post_Tag Where Post_ID = (:post_id) And Tag_ID = (:tag_id)"""
			else:
				param = {'recipe_id': recipe_id, 'tag_id': tag_id}
				select_exists_query = """Select * from Have_Recipe_Tag Where Recipe_ID = (:recipe_id) And Tag_ID = (:tag_id)"""
			already_has_tag = g.conn.execute(text(select_exists_query), param).fetchone()

			if already_has_tag:
				if post_id:
					flash('This' + ' post ' + 'already has that tag', 'danger')
					return redirect(f'/AddTag?post_id={post_id}')
				else:
					flash('This' + ' recipe ' + 'already has that tag', 'danger')
					return redirect(f'/AddTag?recipe_id={recipe_id}')
			else:
				tag_id = tag_exists[0]
				
				if post_id:
					params = {'post_id': post_id, 'tag_id': tag_id}
					insertion_query = """INSERT INTO Have_Post_Tag (Post_ID, Tag_ID)
										VALUES (:post_id, :tag_id)"""
				elif recipe_id:
					params = {'recipe_id': recipe_id, 'tag_id': tag_id}
					insertion_query = """INSERT INTO Have_Recipe_Tag (Recipe_ID, Tag_ID)
										VALUES (:recipe_id, :tag_id)"""

				g.conn.execute(text(insertion_query), params)
				g.conn.commit()

				if post_id:
					flash('Tag added successfully to post', 'success')
				elif recipe_id:
					flash('Tag added successfully to recipe', 'success')
				return redirect('/Profile')
		else:
			flash("The tag name entered doesn't exist yet. Create a new tag", 'danger')
			return redirect('/Create')

	post_id = request.args.get('post_id', None)
	recipe_id = request.args.get('recipe_id', None)
	if post_id:
		params = {'post_id': post_id}
		user_id_query = """Select User_ID
							  From Posts Natural Join Make
							  Where Post_ID = (:post_id)"""
		add_tag_user_id = g.conn.execute(text(user_id_query), params).fetchone()[0]
		if user_id != add_tag_user_id:
			flash('You cannot add a tag to a' + ' post ' + 'that is not yours', 'danger')
			return redirect('/')
	elif recipe_id:
		params = {'recipe_id': recipe_id}
		user_id_query = """Select User_ID
							   From Recipes Natural Join Create_Recipe
							  Where Recipe_ID = (:recipe_id)"""
		add_tag_user_id = g.conn.execute(text(user_id_query), params).fetchone()[0]
		if user_id != add_tag_user_id:
			flash('You cannot add a tag to a' + ' recipe ' + 'that is not yours', 'danger')
			return redirect('/')
	elif post_id == '' or recipe_id == '':
		flash('Error: no post or recipe to add tag to')
		return redirect('/')
	
	return render_template('AddTag.html', logged_in = logged_in)

@app.route('/UpdatePost', methods=['POST', 'GET'])
def update_post():
	global logged_in
	global user_id

	if(not logged_in):
		flash('You are not logged in', 'danger')
		return redirect('/')
	
	if request.method == 'POST':
		post_id = request.form['post_id']
		caption = request.form['caption']
		video_file = request.files.get('video_file')
		image_file = request.files.get('image_file')
		
		if not caption and not video_file and not image_file:
			flash("Nothing was entered", 'danger')
			return redirect(f'/UpdatePost?post_id={post_id}')
		elif video_file.filename != '' and image_file.filename != '':
			flash("Upload only one media file", 'danger')
			return redirect(f'/UpdatePost?post_id={post_id}')
		
		current_time = datetime.now()
		formatted_time = current_time.strftime("%Y-%m-%d")

		params = {}
		
		update_query = "Update Posts Set "

		if caption != '':
			update_query += "Caption = (:caption), "
			params['caption'] = caption
		if video_file.filename != '':
			file_path = save_video(video_file)
			update_query += "Video_URL = (:video_file), "
			params['video_file'] = file_path
		elif image_file.filename != '':
			file_path = save_image(image_file)
			update_query += "Image_URL = (:image_file), "
			params['image_file'] = file_path

		update_query += "Date_Posted = (:date_posted)"
		params['date_posted'] = formatted_time

		update_query = update_query.rstrip(', ')
		update_query += " Where Post_ID = (:post_id)"
		params['post_id'] = post_id

		g.conn.execute(text(update_query), params)
		g.conn.commit()

		flash("Your post has been updated successfully", 'success')
		return redirect('/Profile')

	post_id = request.args.get('post_id', None)
	if post_id:
		params = {'post_id': post_id}
		post_user_query = """Select User_ID
							 From Posts Natural Join Make
							 Where Post_ID = (:post_id)"""
		
		update_post_user_id = g.conn.execute(text(post_user_query), params).fetchone()[0]
		if user_id != update_post_user_id:
			flash('You cannot update a post that is not yours', 'danger')
			return redirect('/')
	elif post_id == '':
		flash('Error: no post to update')
		return redirect('/')
	
	return render_template('update_post.html', logged_in=logged_in)

@app.route('/UpdateRecipe', methods=['GET', 'POST'])
def update_recipe():
	global logged_in
	global user_id

	if(not logged_in):
		flash('You are not logged in', 'danger')
		return redirect('/')
	
	if request.method == 'POST':
		recipe_id = request.form['recipe_id']
		recipe_name = request.form['recipe_name']
		description = request.form['description']
		ingredients = request.form['ingredients']
		directions = request.form['directions']
		cook_time = request.form['cook_time']
		image_file = request.files.get('image_file')
		
		if not recipe_name and not description and not ingredients and not directions and not cook_time and not image_file:
			flash("Nothing was entered", 'danger')
			return redirect(f'/UpdateRecipe?recipe_id={recipe_id}')

		params = {}
		
		update_query = "Update Recipes Set "

		if recipe_name:
			update_query += "Recipe_Name = (:recipe_name), "
			params['recipe_name'] = recipe_name
		if description:
			update_query += "Description = (:description), "
			params['description'] = description
		if ingredients:
			update_query += "Ingredients = (:ingredients), "
			params['ingredients'] = ingredients
		if directions:
			update_query += "Directions = (:directions), "
			params['directions'] = directions
		if cook_time:
			cook_time = int(cook_time)
			update_query += "Cook_Time = (:cook_time), "
			params['cook_time'] = cook_time
		if image_file is not None and image_file.filename != '':
			file_path = save_image(image_file)
			update_query += "Image_URL = (:image_file), "
			params['image_file'] = file_path

		update_query = update_query.rstrip(', ')
		update_query += " Where Recipe_ID = (:recipe_id)"
		params['recipe_id'] = recipe_id

		g.conn.execute(text(update_query), params)
		g.conn.commit()

		flash("Your recipe has been updated successfully", 'success')
		return redirect('/Profile')

	recipe_id = request.args.get('recipe_id', None)
	if recipe_id:
		params = {'recipe_id': recipe_id}
		recipe_user_query = """Select User_ID
							   From Recipes Natural Join Create_Recipe
							   Where Recipe_ID = (:recipe_id)"""
		
		update_recipe_user_id = g.conn.execute(text(recipe_user_query), params).fetchone()[0]
		if user_id != update_recipe_user_id:
			flash('You cannot update a recipe that is not yours', 'danger')
			return redirect('/')
	elif recipe_id == '':
		flash('Error: no recipe to update')
		return redirect('/')
	
	return render_template('update_recipe.html', logged_in=logged_in)

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

@app.route('/create_recipe', methods=['POST'])
def create_recipe():
	global user_id

	recipe_name = request.form['recipe_name']
	description = request.form['description']
	ingredients = request.form['ingredients']
	directions = request.form['directions']
	cook_time = request.form['cook_time']
	image_file = request.files.get('image_file')

	if cook_time:
		cook_time = int(cook_time)

	if not recipe_name or not ingredients or not directions:
		flash('* fields are required', 'danger')
		return redirect('/Create')
	
	if image_file is not None and image_file.filename != '':
		file_path = save_image(image_file)
	
	params1 = {'recipe_name': recipe_name, 'description': description, 'ingredients': ingredients, 
				 'directions': directions, 'cook_time': cook_time, 'media_file': file_path}
	
	insertion_query = """INSERT INTO Recipes (Recipe_Name, Description, Ingredients, Directions, Cook_Time, Image_Url)
						 VALUES (:recipe_name, :description, :ingredients, :directions, :cook_time, :media_file)
						 RETURNING Recipe_ID"""

	new_recipe = g.conn.execute(text(insertion_query), params1)
	recipe_id = new_recipe.fetchone()[0]

	params2 = {'user_id': user_id, 'recipe_id': recipe_id}
	insertion_query2 = """INSERT INTO Create_Recipe (User_ID, Recipe_ID)
						  VALUES (:user_id, :recipe_id)"""
		
	g.conn.execute(text(insertion_query2), params2)
	g.conn.commit()

	flash("Recipe created successfully", 'success')
	return redirect('/')

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
	formatted_time = current_time.strftime("%Y-%m-%d")

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
	global logged_in_username

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
			logged_in_username = uname_input

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
