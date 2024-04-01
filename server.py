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


@app.route('/', methods=['POST', 'GET'])
def home():
	order = 'Random'
	post_query = """Select username, post_id, caption, image_URL, video_URL
						From Posts Natural Join Make Natural Join Users
						Order by RANDOM()"""

	if request.method == 'POST':
		if 'order' in request.form:
			order = request.form['order']
			if order == 'Random':
				post_query = """Select username, post_id, caption, image_URL, video_URL
								From Posts Natural Join Make Natural Join Users
								Order by RANDOM()"""
			elif order == 'Latest':
				post_query = """Select username, post_id, caption, image_URL, video_URL
								From Posts Natural Join Make Natural Join Users
								Order by Date_Posted DESC
							"""
			elif order == 'Oldest':
				post_query = """Select username, post_id, caption, image_URL, video_URL
								From Posts Natural Join Make Natural Join Users
								Order by Date_Posted ASC
								"""
			elif order == 'Most Popular':
				post_query = """WITH TopPosts AS (SELECT Post_ID, SUM(Rating) AS Likes
												FROM Rate
												GROUP BY Post_ID
												)
								Select username, post_id, caption, image_URL, video_URL
								From TopPosts Natural Join Posts Natural Join Users Natural Join Make
								ORDER BY Likes DESC
							"""
			elif order == 'Following':
				post_query = f"""WITH Following_Posts AS (Select Post_ID
														From Make
														Where user_id IN (Select Followed_ID 
																		From Follow
																		Where Follower_ID = {user_id}))
								Select username, post_id, caption, image_URL, video_URL
								From Following_Posts Natural Join Posts Natural Join Users Natural Join Make
							"""
		elif 'tag' in request.form:
			tag = request.form.get('tag')

			if not tag:
				flash("No Tag Entered", 'danger')
				return redirect('/')

			param = {'tag': tag}
			select_query = """Select Tag_ID from Tags Where Tag_Name = (:tag)"""
			tag_exists = g.conn.execute(text(select_query), param).fetchone()

			if not tag_exists:
				flash("The tag entered does not exist", 'danger')
				return redirect('/')
			else:
				tag_id = tag_exists[0]
				
				post_query = f"""Select username, post_id, caption, image_URL, video_URL
								From Posts Natural Join Users Natural Join Make Natural Join Have_Post_Tag
								Where tag_id = {tag_id}"""

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

	if not posts:
		flash("No Posts exists with the applied filter", "info")
		return redirect('/')
	
	cursor.close()
	
	return render_template("feed.html", posts=posts, logged_in=logged_in, loggedin_user=logged_in_username, order=order)

@app.route('/Recipes', methods=['POST', 'GET'])
def recipes():
	view = 'Random'
	recipe_query = """Select Recipe_ID, Username, Recipe_Name, Description, Ingredients, Directions, Cook_Time, Image_URL
					  from Recipes natural join Users natural join Create_recipe
					  Order by RANDOM()"""
	
	if request.method == 'POST':
		if 'view' in request.form:
			view = request.form['view']
			if view == 'Random':
				recipe_query = """Select Recipe_ID, Username, Recipe_Name, Description, Ingredients, Directions, Cook_Time, Image_URL
					  			  from Recipes natural join Users natural join Create_recipe
					   			  Order by RANDOM()"""
			elif view == 'Following':
				recipe_query = f"""WITH Following_R AS (Select Recipe_ID
														From Create_Recipe
														Where User_id IN (Select Followed_ID 
																		  From Follow
																		  Where Follower_ID = {user_id}))
								   Select Recipe_ID, Username, Recipe_Name, Description, Ingredients, Directions, Cook_Time, Image_URL
								   From Following_R Natural Join Recipes Natural Join Users Natural Join Create_recipe
							"""
		elif 'tag' in request.form:
			tag = request.form.get('tag')

			if not tag:
				flash("No Tag Entered", 'danger')
				return redirect('/Recipes')

			param = {'tag': tag}
			select_query = """Select Tag_ID from Tags Where Tag_Name = (:tag)"""
			tag_exists = g.conn.execute(text(select_query), param).fetchone()

			if not tag_exists:
				flash("The tag entered does not exist", 'danger')
				return redirect('/Recipes')
			else:
				tag_id = tag_exists[0]
				
				recipe_query = f"""Select Recipe_ID, Username, Recipe_Name, Description, Ingredients, Directions, Cook_Time, Image_URL
								   From Recipes Natural Join Users Natural Join Create_Recipe Natural Join Have_Recipe_Tag
								   Where tag_id = {tag_id}"""
				
	cursor = g.conn.execute(text(recipe_query))	
	recipes = []

	for Recipe_ID, Username, Recipe_Name, Description, Ingredients, Directions, Cook_Time, Image_URL in cursor:
		recipes.append({'recipe_id': Recipe_ID, 'username': Username, 'recipe_name': Recipe_Name.replace('\"', ''), 'description': Description.replace('\"', ''), 
						'ingredients': Ingredients, 'directions': Directions, 'cook_time': Cook_Time, 'image_file': Image_URL})

	if not recipes:
		flash("No Recipes exists with the applied filter", "info")
		return redirect('/Recipes')

	cursor.close()

	return render_template("recipe.html", recipes=recipes, logged_in=logged_in, loggedin_user=logged_in_username, view=view)

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
					Order by Date_Posted DESC"""
			
	recipe_query = """Select Recipe_ID, Username, Recipe_Name, Description, Ingredients, Directions, Cook_Time, Image_URL
					  from Recipes natural join Users natural join Create_recipe
					  Where User_ID = (:user_id)"""
	
	collection_query = """SELECT Collection_Name
						  FROM Collections
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

		cursor = g.conn.execute(text(collection_query), params)
		c_list = []
		
		for Collection_Name in cursor:
			c_list.append(Collection_Name[0])

		collections = {'collection_name': c_list}
		
		cursor.close()

		following_query = f"""Select count(*)
							  From Follow
							  Where Follower_ID = (:user_id)"""
		number_following = g.conn.execute(text(following_query), params).fetchone()[0]

		followers_query = f"""Select count(*)
							  From Follow
							  Where Followed_ID = (:user_id)"""
		number_followers = g.conn.execute(text(followers_query), params).fetchone()[0]

		return render_template("profile.html", logged_in=logged_in, users=users, posts=posts, recipes=recipes, collections=collections,
						 logged_in_username=logged_in_username, username_viewing=logged_in_username, number_followers=number_followers, 
						 number_following=number_following)

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

	post_id = request.args.get('post_id')
	recipe_id = request.args.get('recipe_id')
	if post_id:
		params = {'post_id': post_id}
		user_id_query = """Select User_ID
							  From Posts Natural Join Make
							  Where Post_ID = (:post_id)"""
		exists = g.conn.execute(text(user_id_query), params).fetchone()
		if exists:
			add_tag_user_id = exists[0]
			if user_id != add_tag_user_id:
				flash('You cannot add a tag to a' + ' post ' + 'that is not yours', 'danger')
				return redirect('/Profile')
		else:
			flash('Error: this post does not exist', 'danger')
			return redirect('/Profile')
	elif recipe_id:
		params = {'recipe_id': recipe_id}
		user_id_query = """Select User_ID
							   From Recipes Natural Join Create_Recipe
							  Where Recipe_ID = (:recipe_id)"""
		exists = g.conn.execute(text(user_id_query), params).fetchone()
		if exists:
			add_tag_user_id = exists[0]
			if user_id != add_tag_user_id:
				flash('You cannot add a tag to a' + ' recipe ' + 'that is not yours', 'danger')
				return redirect('/Profile')
		else:
			flash('Error: this recipe does not exist', 'danger')
			return redirect('/Profile')
	else:
		flash('Error: no post or recipe to add tag to')
		return redirect('/Profile')
	
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

	post_id = request.args.get('post_id')
	if post_id:
		params = {'post_id': post_id}
		post_user_query = """Select User_ID
							 From Posts Natural Join Make
							 Where Post_ID = (:post_id)"""
		
		exists = g.conn.execute(text(post_user_query), params).fetchone()
		if exists:
			update_post_user_id = exists[0]
			if user_id != update_post_user_id:
				flash('You cannot update a post that is not yours', 'danger')
				return redirect('/Profile')
		else:
			flash('Error: this post does not exist', 'danger')
			return redirect('/Profile')
	else:
		flash('Error: no post to update')
		return redirect('/Profile')
	
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

	recipe_id = request.args.get('recipe_id')
	if recipe_id:
		params = {'recipe_id': recipe_id}
		recipe_user_query = """Select User_ID
							   From Recipes Natural Join Create_Recipe
							   Where Recipe_ID = (:recipe_id)"""
		
		exists = g.conn.execute(text(recipe_user_query), params).fetchone()
		if exists:
			update_recipe_user_id = exists[0]
			if user_id != update_recipe_user_id:
				flash('You cannot update a recipe that is not yours', 'danger')
				return redirect('/Profile')
		else:
			flash('Error: this recipe does not exist', 'danger')
			return redirect('/Profile')
	else:
		flash('Error: no recipe to update')
		return redirect('/Profile')
	
	return render_template('update_recipe.html', logged_in=logged_in)

@app.route('/view_collection')
def view_collection():
	global logged_in
	global user_id

	if(not logged_in):
		flash('You are not logged in', 'danger')
		return redirect('/')
	
	if(request.args.get('collection_name')):
		c_name = request.args.get('collection_name')
		c_id = """Select collection_id 
				  From Collections
				  Where user_id = (:user_id) and collection_name = (:collection_name)"""
		
		params1 = {'collection_name': c_name, 'user_id': user_id}
		c_exists = g.conn.execute(text(c_id), params1).fetchone()
		if c_exists:
			c_id = c_exists[0]
		else:
			flash('Error: this collection does not exist', 'danger')
			return redirect('/Profile')

		params2 = {'user_id': user_id, 'collection_id': c_id}

		post_query = """SELECT u.Username, p.Post_ID, p.Caption, p.Image_URL, p.Video_URL
						FROM Posts p
						JOIN Make m ON p.Post_ID = m.Post_ID
						JOIN Users u ON m.User_ID = u.User_ID
						JOIN Contain_Post cp ON p.Post_ID = cp.Post_ID
						JOIN Collections c ON cp.User_ID = c.User_ID AND cp.Collection_ID = c.Collection_ID
						WHERE c.Collection_ID = (:collection_id) and c.User_id = (:user_id)"""
		
		recipe_query = """Select r.Recipe_ID, u.Username, r.Recipe_Name, r.Description, r.Ingredients, r.Directions, r.Cook_Time, r.Image_URL 
						  FROM Recipes r
						  JOIN Create_Recipe cr ON r.Recipe_ID = cr.Recipe_ID
						  JOIN Users u ON cr.User_ID = u.User_ID
						  JOIN Contain_Recipe ON r.Recipe_ID = Contain_Recipe.Recipe_ID
						  JOIN Collections c ON Contain_Recipe.User_ID = c.User_ID AND Contain_Recipe.Collection_ID = c.Collection_ID
						  WHERE c.Collection_ID = (:collection_id) and c.User_id = (:user_id)"""
		
		posts, recipes = [], []
		cursor = g.conn.execute(text(post_query), params2)

		for username, post_id, caption, image_url, video_url in cursor:
			posts.append({'username': username, 'post_id': post_id, 'caption': caption, 'video_url': video_url, 'image_url': image_url})

		cursor = g.conn.execute(text(recipe_query), params2)	

		for Recipe_ID, Username, Recipe_Name, Description, Ingredients, Directions, Cook_Time, Image_URL in cursor:
			recipes.append({'recipe_id': Recipe_ID, 'username': Username, 'recipe_name': Recipe_Name.replace('\"', ''), 'description': Description.replace('\"', ''), 
							'ingredients': Ingredients, 'directions': Directions, 'cook_time': Cook_Time, 'image_file': Image_URL})
			
		cursor.close()
	else:
		flash('Error: no collection to view', 'danger')
		return redirect('/Profile')
	
	return render_template('view_collection.html', logged_in=logged_in, collection_name=c_name, posts=posts, recipes=recipes, loggedin_user=logged_in_username)

@app.route('/add_to_collection', methods=['GET','POST'])
def add_to_collection():
	global user_id
	global logged_in

	if(not logged_in):
		flash('You are not logged in', 'danger')
		return redirect('/')

	if request.method == 'POST':
		collection_name = request.form.get('collection_name')
		params = {'user_id': user_id, 'collection_name': collection_name}
		c_id_query = """SELECT Collection_ID
						FROM Collections
						WHERE User_ID = (:user_id) AND Collection_Name = (:collection_name)"""
		
		collection_id = g.conn.execute(text(c_id_query), params).fetchone()[0]

		post_id = request.form.get('post_id')
		if post_id:
			params = {'user_id': user_id, 'collection_id': collection_id, 'post_id': post_id}

			check_query = """SELECT * FROM Contain_Post
							 WHERE User_ID = (:user_id) AND Collection_ID = (:collection_id) AND Post_ID = (:post_id)"""
			exists = g.conn.execute(text(check_query), params).fetchone()
			if exists:
				flash('This post is already in the ' + collection_name + ' collection', 'danger')
				return redirect('/')

			insert_query = """INSERT INTO Contain_Post
							Values (:user_id, :collection_id, :post_id)"""
			
			g.conn.execute(text(insert_query), params)
			g.conn.commit()

			flash('Post added to ' + collection_name + ' collection', 'success')
		else:
			recipe_id = request.form.get('recipe_id')
			params = {'recipe_id': recipe_id, 'user_id': user_id, 'collection_id': collection_id}

			check_query = """SELECT * FROM Contain_Recipe
							 WHERE User_ID = (:user_id) AND Collection_ID = (:collection_id) AND Recipe_ID = (:recipe_id)"""
			exists = g.conn.execute(text(check_query), params).fetchone()
			if exists:
				flash('This recipe is already in the ' + collection_name + ' collection', 'danger')
				return redirect('/Recipes')
			
			insert_query = """INSERT INTO Contain_Recipe
							Values (:recipe_id, :user_id, :collection_id)"""
			
			g.conn.execute(text(insert_query), params)
			g.conn.commit()

			flash('Recipe added to ' + collection_name + ' collection', 'success')

		return redirect('/Profile')
	
	params = {'user_id': user_id}
	exist_query = """SELECT *
					 FROM Collections
					 Where User_ID = (:user_id)"""
	
	exists_collections = g.conn.execute(text(exist_query), params).fetchone()
	if not exists_collections:
		flash('You need to create a collection first')
		return redirect('/Create')

	params = {'user_id': user_id}
	collection_query = """SELECT Collection_Name
						  FROM Collections
						  Where User_ID = (:user_id)"""
	
	cursor = g.conn.execute(text(collection_query), params)
	collections = []
	c_list = []
	
	for Collection_Name in cursor:
		c_list.append(Collection_Name[0])

	collections = {'collection_name': c_list}
	
	cursor.close()

	return render_template('add_to_collection.html', user_id=user_id, logged_in=logged_in, collections=collections)

@app.route('/create_collection', methods=['POST'])
def create_collection():
	global user_id

	params = {'user_id': user_id}
	next_collection_query = """SELECT count(*)
								FROM Collections
								WHERE User_ID = (:user_id)"""
	
	number_collections = g.conn.execute(text(next_collection_query), params).fetchone()[0]
	c_name = request.form.get('collection_name')

	if c_name == '':
		flash('Please enter a name for your collection', 'danger')
		return redirect('/Create')
	
	if number_collections > 0:
		params = {'user_id': user_id, 'collection_name': c_name}
		check_query = """SELECT * FROM Collections
							WHERE User_ID = (:user_id) AND Collection_Name = (:collection_name)"""
		
		collection_exists = g.conn.execute(text(check_query), params).fetchone()
		if collection_exists:
			flash('There already exists a collection with this name', 'danger')
			return redirect('/Create')

	next_collection_id = number_collections + 1

	params = {'collection_id': next_collection_id, 'user_id': user_id, 'collection_name': c_name}
	insert_query = """INSERT INTO Collections
						Values (:collection_id, :user_id, :collection_name)"""
	
	g.conn.execute(text(insert_query), params)

	params = {'user_id': user_id, 'collection_id': next_collection_id}
	insert_own_query = """INSERT INTO Own
						Values (:user_id, :collection_id)"""
	g.conn.execute(text(insert_own_query), params)

	g.conn.commit()

	flash('Collection created successfully', 'success')
	return redirect('/Profile')

@app.route('/delete_from_collection', methods=['GET','POST'])
def delete_from_collection():
	global logged_in
	global user_id

	if(not logged_in):
		flash('You are not logged in', 'danger')
		return redirect('/')
	
	if request.method == 'POST':
		response = request.form.get('response')
		collection_name = request.form.get('collection_name')
		collection_id = request.form.get('collection_id')
		post_id = request.form.get('post_id')
		recipe_id = request.form.get('recipe_id')

		if response == "Yes":
			if post_id:
				params = {'collection_id': collection_id, 'user_id': user_id, 'post_id': post_id}
				delete_query = """DELETE FROM Contain_Post
								  WHERE User_ID = (:user_id)
								  AND Collection_ID = (:collection_id)
								  AND Post_ID = (:post_id)"""
				
				g.conn.execute(text(delete_query), params)
				g.conn.commit()

				flash('The post was deleted from your collection.', 'danger')
			else:
				params = {'collection_id': collection_id, 'user_id': user_id, 'recipe_id': recipe_id}
				delete_query = """DELETE FROM Contain_Recipe
								  WHERE User_ID = (:user_id)
								  AND Collection_ID = (:collection_id)
								  AND Recipe_ID = (:recipe_id)"""
				
				g.conn.execute(text(delete_query), params)
				g.conn.commit()

				flash('The recipe was deleted from your collection.', 'danger')

			return redirect(f'/view_collection?collection_name={collection_name}')
		else:
			if post_id:
				flash('The post was not deleted from your collection.', 'success')
			else:
				flash('The recipe was not deleted from your collection.', 'success')
			return redirect(f'/view_collection?collection_name={collection_name}')
	
	c_name = request.args.get('collection_name')
	post_id = request.args.get('post_id')
	recipe_id = request.args.get('recipe_id')

	if not c_name:
		flash('Error: no collection to delete from.', 'danger')
		return redirect('/Profile')
	elif not post_id and not recipe_id:
		flash('Error: no post/recipe to delete.', 'danger')
		return redirect(f'/view_collection?collection_name={c_name}')
	else:
		params = {'user_id': user_id, 'collection_name': c_name}
		collection_id_query = """Select Collection_ID
								 From Collections
								 Where User_ID = (:user_id)
								 AND Collection_Name = (:collection_name)"""
		
		exists = g.conn.execute(text(collection_id_query), params).fetchone()
		if exists:
			c_id = exists[0]
		else:
			flash('Error: collection does not exist', 'danger')
			return redirect('/Profile')

		if post_id:
			params = {'user_id': user_id, 'collection_id': c_id, 'post_id': post_id}
			check_query = """Select *
							 From Contain_Post
							 Where User_ID = (:user_id)
							 AND Collection_ID = (:collection_id)
							 AND Post_ID = (:post_id)"""
			exists = g.conn.execute(text(check_query), params).fetchone()
			if not exists:
				flash('Error: post does not exist in collection', 'danger')
				return redirect(f'/view_collection?collection_name={c_name}')
			
			selection = 'delete_post_c'
			return render_template("delete_confirmation.html", logged_in=logged_in, selection=selection, collection_id=c_id, 
						  collection_name=c_name, post_id=post_id)
		else:
			params = {'user_id': user_id, 'collection_id': c_id, 'recipe_id': recipe_id}
			check_query = """Select *
							 From Contain_Recipe
							 Where User_ID = (:user_id)
							 AND Collection_ID = (:collection_id)
							 AND Recipe_ID = (:recipe_id)"""
			exists = g.conn.execute(text(check_query), params).fetchone()
			if not exists:
				flash('Error: recipe does not exist in collection', 'danger')
				return redirect(f'/view_collection?collection_name={c_name}')
			
			selection = 'delete_recipe_c'
			return render_template("delete_confirmation.html", logged_in=logged_in, selection=selection, collection_id=c_id, 
						  collection_name=c_name, recipe_id=recipe_id)
		

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
	description = request.form.get('description')
	ingredients = request.form['ingredients']
	directions = request.form['directions']
	cook_time = request.form.get('cook_time')
	image_file = request.files.get('image_file')

	if not recipe_name or not ingredients or not directions or not cook_time:
		flash('* fields are required', 'danger')
		return redirect('/Create')
	
	cook_time = int(cook_time)
	
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
	global logged_in_username

	if(not logged_in):
		flash('Error: you are not logged in', 'danger')
		return redirect('/')
	
	logged_in = False
	user_id = None
	logged_in_username = None
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
		
		params = {'username': username}
		check_username = """SELECT * FROM Users
							Where Username = (:username)"""
		
		username_exists = g.conn.execute(text(check_username), params).fetchone()
		if username_exists:
			flash('Sorry, that username is already taken.', 'danger')
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

@app.route('/Delete_Post', methods=['GET', 'POST'])
def delete_post():
	global logged_in
	global user_id

	if(not logged_in):
		flash('Error: you are not logged in', 'danger')
		return redirect('/')

	if request.method == 'POST':
		response = request.form.get('response')
		if response == "Yes":
			post_id = request.form.get('post_id')
			params = {'user_id': user_id, 'post_id': post_id}

			urls_query = """SELECT Image_Url, Video_Url
							FROM Posts Natural Join Make
							WHERE User_ID = (:user_id)
							AND Post_ID = (:post_id)"""
			
			urls = g.conn.execute(text(urls_query), params)

			for image_url, video_url in urls:
				if image_url:
					image_path = f"static/images/{image_url}"
					if os.path.exists(image_path):
						os.remove(image_path)
				else:
					video_path = f"static/videos/{video_url}"
					if os.path.exists(video_path):
						os.remove(video_path)

			params = {'post_id': post_id}
			delete_query = """DELETE FROM Posts
							  WHERE Post_ID = (:post_id)"""
			
			g.conn.execute(text(delete_query), params)
			g.conn.commit()

			flash('Your post was deleted.', 'danger')
			return redirect('/Profile')
		else:
			flash('Your post was not deleted.', 'success')
			return redirect('/Profile')
	
	post_id = request.args.get('post_id')
	if post_id:
		params = {'post_id': post_id}
		post_user_query = """Select User_ID
							 From Posts Natural Join Make
							 Where Post_ID = (:post_id)"""
		
		exists = g.conn.execute(text(post_user_query), params).fetchone()
		if exists:
			delete_post_user_id = exists[0]
			if user_id != delete_post_user_id:
				flash('You cannot delete a post that is not yours', 'danger')
				return redirect('/Profile')
		else:
			flash('Error: this post does not exist', 'danger')
			return redirect('/Profile')
	else:
		flash('Error: no post to delete', 'danger')
		return redirect('/Profile')

	return render_template("delete_confirmation.html", logged_in=logged_in, selection='post', post_id=post_id)

@app.route('/Delete_Recipe', methods=['GET', 'POST'])
def delete_recipe():
	global logged_in
	global user_id

	if(not logged_in):
		flash('Error: you are not logged in', 'danger')
		return redirect('/')

	if request.method == 'POST':
		response = request.form.get('response')
		if response == "Yes":
			recipe_id = request.form.get('recipe_id')
			params = {'recipe_id': recipe_id, 'user_id': user_id}
			image_query = """SELECT Image_Url
							FROM Recipes Natural Join Create_Recipe
							WHERE User_ID = (:user_id)
							AND Recipe_ID = (:recipe_id)"""
			
			image_url = g.conn.execute(text(image_query), params).fetchone()[0]
			if image_url:
				image_path = f"static/images/{image_url}"
				if os.path.exists(image_path):
					os.remove(image_path)

			params = {'recipe_id': recipe_id}
			delete_query = """DELETE FROM Recipes
							  WHERE Recipe_ID = (:recipe_id)"""
			
			g.conn.execute(text(delete_query), params)
			g.conn.commit()

			flash('Your recipe was deleted.', 'danger')
			return redirect('/Profile')
		else:
			flash('Your recipe was not deleted.', 'success')
			return redirect('/Profile')

	recipe_id = request.args.get('recipe_id')
	if recipe_id:
		params = {'recipe_id': recipe_id}
		recipe_user_query = """Select User_ID
							   From Recipes Natural Join Create_Recipe
							   Where Recipe_ID = (:recipe_id)"""
		
		exists = g.conn.execute(text(recipe_user_query), params).fetchone()
		if exists:
			delete_recipe_user_id = exists[0]
			if user_id != delete_recipe_user_id:
				flash('You cannot delete a recipe that is not yours', 'danger')
				return redirect('/Profile')
		else:
			flash('Error: this recipe does not exist', 'danger')
			return redirect('/Profile')
	else:
		flash('Error: no recipe to delete', 'danger')
		return redirect('/Profile')
			
	return render_template("delete_confirmation.html", logged_in=logged_in, selection='recipe', recipe_id=recipe_id)

@app.route('/Delete_Collection', methods=['GET', 'POST'])
def delete_collection():
	global logged_in
	global user_id

	if(not logged_in):
		flash('Error: you are not logged in', 'danger')
		return redirect('/')
	
	if request.method == 'POST':
		response = request.form.get('response')
		if response == "Yes":
			collection_name = request.form.get('collection_name')
			params = {'collection_name': collection_name, 'user_id': user_id}
			delete_query = """DELETE FROM Collections
							  WHERE User_ID = (:user_id)
							  AND Collection_Name = (:collection_name)"""
			
			g.conn.execute(text(delete_query), params)
			g.conn.commit()

			flash('Your collection was deleted.', 'danger')
			return redirect('/Profile')
		else:
			flash('Your collection was not deleted.', 'success')
			return redirect('/Profile')
	
	collection_name = request.args.get('collection_name')
	if collection_name:
		params = {'user_id': user_id, 'collection_name': collection_name}
		collection_user_query = """Select *
								   From Collections
								   Where User_ID = (:user_id)
								   AND Collection_Name = (:collection_name)"""
		
		exists = g.conn.execute(text(collection_user_query), params).fetchone()
		if not exists:
			flash('Error: this collection does not exist', 'danger')
			return redirect('/Profile')
	else:
		flash('Error: no collection to delete', 'danger')
		return redirect('/Profile')

	return render_template("delete_confirmation.html", logged_in=logged_in, selection='collection', collection_name=collection_name)

@app.route('/Delete_Account', methods=['GET', 'POST'])
def delete_profile():
	global logged_in
	global user_id
	global logged_in_username

	if(not logged_in):
		flash('Error: you are not logged in', 'danger')
		return redirect('/')
	
	if request.method == 'POST':
		response = request.form.get('response')
		if response == "Yes":
			params = {'user_id': user_id}

			urls_query = """SELECT Image_Url, Video_Url
							FROM Posts Natural Join Make
							WHERE User_ID = (:user_id)"""
			
			urls = g.conn.execute(text(urls_query), params)

			for image_url, video_url in urls:
				if image_url:
					image_path = f"static/images/{image_url}"
					if os.path.exists(image_path):
						os.remove(image_path)
				else:
					video_path = f"static/videos/{video_url}"
					if os.path.exists(video_path):
						os.remove(video_path)

			image_query = """SELECT Image_Url
							FROM Recipes Natural Join Create_Recipe
							WHERE User_ID = (:user_id)"""
			
			image_urls = g.conn.execute(text(image_query), params)

			for r in image_urls:
				image_url = r[0]
				if image_url:
					image_path = f"static/images/{image_url}"
					if os.path.exists(image_path):
						os.remove(image_path)
			
			delete_posts = """DELETE FROM Posts p
							  USING Make m
							  WHERE p.Post_ID = m.Post_ID
							  AND m.User_ID = (:user_id)"""
			
			g.conn.execute(text(delete_posts), params)

			delete_recipes = """DELETE FROM Recipes r
								USING Create_Recipe cr
								WHERE r.Recipe_ID = cr.Recipe_ID
							    AND cr.User_ID = (:user_id)"""
			
			g.conn.execute(text(delete_recipes), params)

			delete_user = """DELETE FROM Users
							 Where User_ID = (:user_id)"""
			
			g.conn.execute(text(delete_user), params)

			g.conn.commit()

			logged_in = False
			user_id = None
			logged_in_username = None

			flash('Your account has been deleted.', 'danger')
			return redirect('/')
		else:
			flash('Your account was not deleted.', 'success')
			return redirect('/Profile')

	return render_template("delete_confirmation.html", logged_in=logged_in, selection='account')


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
