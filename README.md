Databases Project Part 3


Group Members: Eric Li, John Dong


PostgreSQL Account:
* Username: el3194
* Password: el3194


URL: http://34.23.111.171:8111/




Below are features we implemented based on our Part 1 proposal:


* Users can create an account by clicking on the Register button and entering their Name, Address, Biography, Date of Birth, Username, and Password. 
   * The fields Name, Date of Birth, Username, and Password are required to create an account, as indicated by the asterisks. 
   * Usernames are unique, so a user cannot create a new account with a username that is already taken.

* Once a user has created an account, they can login and get access to many features. 
   * Users can interact with other users by clicking on their profile, viewing their posts and recipes, and deciding whether to follow them or not. 
   * Users can also interact with others by rating posts with a Yum or a Yuck or commenting on a post. 
   * Users are only allowed to make one comment on a post, so if they try commenting again, their comment will just be updated. The same logic applies to the Yum/Yuck rating.

* In the Feed and Recipe pages, users can sort and filter the posts/recipes by certain criteria of their choice. 
   * In the Feed, users can sort the posts in a random order, by date posted (latest/oldest), by most popular (posts with highest net rating), and by following (posts of users you are following). 
   * Additionally, users can filter the posts by tags. Entering a tag name will result in all posts associated with that tag being displayed (if that tag has already been created). 
   * In the Recipes page, users can also sort and filter the recipes by random, following, and tags. 
   * If a user has already created a collection, they can add a post or recipe to their collections.

* In the Create page, users can create a new post, a new recipe, a new tag, or a new collection. 
   * Users can create a post by entering an optional caption along with a required image or video file that users can upload. 
   * Users can also create a recipe by entering the Recipe Name, Description, Ingredients, Directions, Cook Time, and image file. Fields with asterisks are required to create a recipe. 
   * Users can also create a tag by entering a tag name and clicking Create. Tags are unique, so a user cannot create a tag that already exists. 
   * Finally, users can create a new collection by entering a collection name and clicking Create. A user’s collections are unique, so they cannot create more than one collection of the same name.

* In the Profile page, users can add tags to their own posts and recipes by clicking on the Add Tag button in the Feed and Recipe pages. Users can also view the posts,
  recipes, and collections they have created.




Some features that were not in our original proposal, but were implemented:


* If a user is not logged in, they are restricted to the Feed, Recipes, Login, and Register pages. 
   * Additionally, they cannot interact with any of the posts or recipes, so they cannot view profiles, rate, comment, or add posts/recipes to a collection. 
   * If a user tries to access a page in the Create and Profile pages by manually typing it in the URL, they will be denied access.

* Once logged in, users can access their own Profile page and view or make edits to their account, posts, recipes, and collections. 
   * For example, users can update their account by clicking on the Update Profile button and making the desired changes. 
   * If a user no longer wants their account on the website, they can delete their account, which will remove all posts, recipes, ratings, and collections created by that user. 
   * Users also have the option to update their posts and recipes, as well as delete them if desired. 
   * Users also have the ability to delete collections they have created and remove certain posts or recipes within a certain collection. 
   * When a user is deleting, they will be prompted a confirmation for the delete to ensure that if they accidentally clicked on the delete button, they have an option to go back.

* For each users’ Profile, a followers and following count is displayed.

* If a user tries to maliciously make changes to posts/recipes not created by them by manually entering in the URL, they will be denied access.




Features from Part 1 that were not implemented:


* We decided not to implement the filter by tag feature within a collection because it would be somewhat redundant considering the user already gives the collection a name.
  Therefore, if a user wanted to see which posts/recipes are associated with a certain tag, they could just view the collection that has the name similar to the tag.
  
* We also decided not to implement the search for other user feature because a user could simply just type in the username in the URL.




Two Interesting Webpages:


1. Profile Page


One interesting webpage in terms of database operations was the Profile page, mainly because it involved so many features. 
For almost all of the features, the queries executed in the database typically involved many joins. In order to correctly handle errors, 
queries had to be executed for every feature to check if the action being requested by the user was valid. For example, if a user was 
trying to make changes to a post, a query had to be executed to determine whether the post existed in the database before carrying out the action. 
The same applied for recipes and collections. Additionally, input from the website had to be submitted correctly in order to ensure that 
the queries altering data in tables were altering the correct table rows. An example of this could be updating a recipe, in which the 
recipe_id had to be passed in to ensure that the query would alter the recipe associated with that recipe_id. The user_id of the user who 
was currently logged in also had to be used as input in various queries relating to collections. This is because multiple users could have a 
collection with the same collection_id and collection name, and so the user_id would be the key difference between these collections.


2. Delete Confirmation Page


This webpage was also interesting as it prompted the user to verify if they wanted to carry out the delete action they desired. We decided to implement 
this in particular because it involved an irreversible change in the database after the query was executed (in this case, after the user clicked on Yes).
What made this page so important and interesting was that every input from the website needed to be exactly correct, or else this would result in an 
incorrect row being deleted in a table. For example, if a user wanted to delete a post, the corresponding post_id had to be passed in to delete the correct
post. In the context of our application, an incorrect row being deleted would be a major problem, as a user could potentially unintentionally delete other
users’ posts or recipes (or even their account) if the input wasn’t correct. Additionally, inputs had to be handled twice (first from the URL using 
request.args.get and then through a hidden input in the HTML file which was then accessed by request.form.get once the form was submitted) in order to ensure
that the correct profile/post/recipe/collection was being deleted through the query.
