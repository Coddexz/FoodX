import sqlite3
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import re
import requests

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
app.secret_key = "a1c2eed2523f7e1d5add10b3ec2b89705708ba691c1924aa26b00b5466be"
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# Checking compliance of the password with the requirements
def password_check_reg(new_password, new_password_conf):
    # Check if the passwords are the same
    if new_password != new_password_conf:
        flash("The new passwords must be the same. Please, try again.")
        return False

    # At least 8 characters long
    if len(new_password) < 8:
        flash("The password should contain at least 8 characters.")
        return False

    # At least one letter
    elif not re.search("[A-Za-z]", new_password):
        flash("The password should contain at least one letter.")
        return False

    # At least one special character
    elif not re.search("[@$!%*#?&]", new_password):
        flash("The password should contain at least one special character.")
        return False

    # At least one digit
    elif not re.search("[0-9]", new_password):
        flash("The password should contain at least one digit.")
        return False

    # Dangerous symbols
    elif re.search("[<>{}\\[\\]]", new_password):
        flash("The password must not contain any dangerous symbols.")
        return False
    # If everything is correct -> return True
    return True


# Checking compliance of the current password with saved in the database
def password_check_com(current_password):
    with sqlite3.connect("identifier.sqlite") as con:
        db = con.cursor()
        if not check_password_hash(db.execute("SELECT password FROM users WHERE userId = ?",
                                              (session["name"],)).fetchone()[0], current_password):
            flash("Wrong current password.")
            return False
    return True


# Check if email and username don't contain anything harmful
def name_check(email, name):
    if re.search("[<>{}\\[\\]]", email) or re.search("[<>{}\\[\\]]", name):
        flash("The email nor username must not contain any dangerous symbols.")
        return False
    return True


def get_user(user_id):
    con = sqlite3.connect("identifier.sqlite")
    db_u = con.cursor()
    user = User(*db_u.execute("SELECT * FROM users WHERE userId=?", (user_id,)).fetchone())
    con.close()
    return user


class User(UserMixin):
    def __init__(self, user_id, user_email, name, password):
        self.user_id = user_id
        self.user_email = user_email
        self.name = name
        self.password = password

    # What current_user returns
    def __repr__(self):
        return self.name

    def get_id(self):
        return self.user_id


@login_manager.user_loader
def load_user(user_id):
    return get_user(user_id)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Take the ingredients, prepare it and transfer into a string with comma separated ingredients
        ingredients_entered = [x.strip().lower() for x in request.form.get("search_bar").split(",")]
        ingredients_entered = ",".join(map(str, ingredients_entered))

        # Paging number (default or chosen by a user)
        if "paging_number" in session:
            paging_number = session["paging_number"] * 20
            session["paging_number"] = 0
        else:
            paging_number = 0

        # Send query to the API
        url = "https://tasty.p.rapidapi.com/recipes/list"
        querystring = {"from": paging_number, "size": "20", "q": ingredients_entered, "sort": "popularity"}
        headers = {
            # Here API-Key should be entered
            "X-RapidAPI-Key": "",
            "X-RapidAPI-Host": "tasty.p.rapidapi.com"
        }
        response = requests.request("GET", url, headers=headers, params=querystring)

        # If there is an error for API responses
        if response.status_code != 200:
            return jsonify({"error": response.text})

        # If there is rate limit exceeded:
        if response.headers.get('X-RateLimit-Remaining') == 0:
            reset_time = response.headers.get('X-RateLimit-Reset')
            return jsonify({"error": "rate limit exceeded", "reset_time": reset_time})

        # Get the data from the request
        data = response.json()
        recipes_count = data["count"]
        recipes = data["results"]
        recipes_list = []
        for recipe in recipes:
            if len(recipe.keys()) < 40:
                recipe = None
                continue
            dish_id = recipe["id"]
            name = recipe["name"]
            description = recipe.get("description", "N/A")
            instructions = " ".join(item.get("display_text", "N/A") for item in recipe.get("instructions", []))
            dish_ingredients = ', '.join(
                [item.get("raw_text", "N/A") for item in recipe.get("sections", [{}])[0].get("components", [])])
            ratings = recipe.get("user_ratings", {}).get("score", "N/A")
            image_url = recipe.get("thumbnail_url", "N/A")
            video_url = recipe.get("original_video_url", "N/A")
            recipe_data = {"dish_id": dish_id, "name": name, "description": description, "instructions": instructions,
                           "dish_ingredients": dish_ingredients, "ratings": ratings,
                           "image_url": image_url, "video_url": video_url}
            recipes_list.append(recipe_data)

        # Prepare the paging_number to send back
        paging_number = paging_number / 20

        # Sort by amount of ingredients
        recipes_list.sort(key=lambda x: len(x["dish_ingredients"]))

        # If there is no recipes found
        if not recipes_list:
            flash("There was no matches for your searching.")
            return render_template("index.html", ingredients_entered=ingredients_entered)

        # Check whether the user has already marked the recipe as his favourite
        user_fav_recipes = None
        if current_user.is_authenticated:
            with sqlite3.connect("identifier.sqlite") as con:
                db = con.cursor()
                user_fav_recipes = db.execute("SELECT dishId FROM favDishes WHERE userId = ?",
                                              (session["name"],)).fetchall()

            # Convert tuple list to a list of integers
            user_fav_recipes = [i[0] for i in user_fav_recipes]

        # Count the number of possible searches
        possible_searches = int(recipes_count/20) + (recipes_count % 20 > 0)

        # send the results to the main page
        return render_template("index.html", recipes_list=recipes_list, ingredients_entered=ingredients_entered,
                               user_fav_recipes=user_fav_recipes, possible_searches=possible_searches,
                               paging_number=paging_number)
    else:
        if not current_user.is_authenticated:
            return render_template("index.html", paging_number=0)
        return render_template("index.html", name=current_user, recipes_list=None, paging_number=0)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["user_email"].strip()
        # Check if user provided an email address
        if "@" not in username:
            flash("Invalid username.")
            return redirect("/")
        password = request.form["user_password"]
        with sqlite3.connect("identifier.sqlite") as con:
            db_u = con.cursor()
            db_row = db_u.execute("SELECT * FROM users WHERE userEmail=?", (username,)).fetchone()

        # If there is no match
        if db_row is None:
            flash("Wrong username.")
            return redirect("/")
        if not check_password_hash(db_row[3], password):
            flash("Wrong password.")
            return redirect("/")
        # Transferring the credentials to User class
        user = User(db_row[0], db_row[1], db_row[2], db_row[3])
        login_user(user)
        session["name"] = db_row[0]
        return redirect("/")
    else:
        return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    # Log out the user
    logout_user()
    session.clear()
    flash("You have been logged out successfully.")
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    # Forget any user_id
    session.clear()
    if request.method == "POST":
        # Ensure username was submitted
        if (not request.form.get("user_email") or not request.form.get("user_password")
                or not request.form.get("password_confirmation")):
            flash("Please, fill the form correctly.")
            return redirect("/")

        # Check if email and username do not contain anything harmful
        if not name_check(request.form["user_email"], request.form["user_name"]):
            return redirect("/")

        # Check if the password meet the requirements
        if not password_check_reg(request.form.get("user_password"), request.form.get("password_confirmation")):
            return redirect("/")

        # Query database for username
        with sqlite3.connect("identifier.sqlite") as con:
            db_new = con.cursor()
            new_user_query = db_new.execute("SELECT * FROM users WHERE userEmail = ?",
                                            (request.form.get("user_email"),)).fetchone()

        # Ensure username exists and password doesn't exist
        if new_user_query:
            flash("The user already exists, please use other e-mail address.")
            return redirect("/")

        # Register the user
        else:
            username = request.form.get("user_email").strip()
            name = request.form.get("user_name").strip()
            password = generate_password_hash(request.form.get("user_password"))
            with sqlite3.connect("identifier.sqlite") as con:
                db_new = con.cursor()
                db_new.execute("INSERT INTO users (userEmail, name, password) VALUES (?, ?, ?)",
                               (username, name, password))
                con.commit()

        # Redirect user to home page
        flash("You have been registered successfully.")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/ingredients")
def ingredients():
    # Get the list of all ingredients
    with sqlite3.connect("identifier.sqlite") as con:
        db = con.cursor()
        ingredients_db = db.execute("SELECT ingredientName FROM ingredients").fetchall()

    # Searching for a letter change
    letter_change_name = []
    for number in range(len(ingredients_db)):
        if number + 1 < len(ingredients_db) and ingredients_db[number][0][0] != ingredients_db[number + 1][0][0]:
            letter_change_name.append(ingredients_db[number][0])
    return render_template("ingredients.html", ingredients=ingredients_db, letter_change_name=letter_change_name)


@app.route("/account")
@login_required
def account_settings():
    with sqlite3.connect("identifier.sqlite") as con:
        db = con.cursor()
        account_values = db.execute("SELECT userEmail, name FROM users WHERE userId = ?",
                                    (session["name"],)).fetchone()
    return render_template("account.html", account_values=account_values)


@app.route("/account/change-name", methods=["POST"])
@login_required
def account_change_name():
    # Check if email and username do not contain anything harmful
    if not name_check(request.form["user_email"], request.form["user_name"]):
        return redirect("/")

    # Check if the current password is correct
    if not password_check_com(request.form["user_password_n"]):
        return redirect("/")

        # Update the account's email address and/or name
    with sqlite3.connect("identifier.sqlite") as con:
        db = con.cursor()
        user_email = request.form["user_email"].strip()
        user_name = request.form["user_name"].strip()
        db.execute("UPDATE users SET userEmail = ?, name = ? WHERE userId = ?",
                   (user_email, user_name, session["name"]))
        con.commit()
    flash("You have successfully changed your email address and/or name.")
    return redirect("/")


@app.route("/account/change-password", methods=["POST"])
@login_required
def account_change_password():
    new_password = request.form["user_password_new"]

    # Check if the password is correct
    if not password_check_reg(new_password, request.form["user_password_new_confirmation"]):
        return redirect("/")

    # Check if the current password is correct
    if not password_check_com(request.form["user_password_p"]):
        return redirect("/")

        # Update the account's passwords
    with sqlite3.connect("identifier.sqlite") as con:
        db = con.cursor()
        db.execute("UPDATE users SET password = ? WHERE userId = ?",
                   (generate_password_hash(new_password), session["name"]))
        con.commit()
    flash("You have successfully changed your password.")
    return redirect("/")


@app.route("/account/delete", methods=["POST"])
@login_required
def account_delete():
    # Check if the password is correct
    if not password_check_com(request.form["user_password_d"]):
        return redirect("/")

    # Delete the account
    with sqlite3.connect("identifier.sqlite") as con:
        db = con.cursor()
        db.execute("DELETE FROM users WHERE userId = ?", (session["name"],))
        db.execute("DELETE FROM favDishes WHERE userId = ?", (session["name"],))
        con.commit()
    session.clear()
    flash("You have successfully deleted your account your password.")
    return redirect("/")


@app.route("/recipe/save", methods=["POST"])
@login_required
def save_recipe():
    # Get the dictionary
    recipe = request.json

    # Check if there is not any exclusion
    with sqlite3.connect("identifier.sqlite") as con:
        db = con.cursor()
        if db.execute("SELECT * FROM favDishes WHERE userId = ? AND dishId = ?",
                      (session["name"], recipe["dish_id"])).fetchone():
            flash("User has already chosen this dish as his favourite, action cancelled.")
            return jsonify({"status": "failure"})
        if len(db.execute("SELECT * FROM favDishes WHERE userId = ?", (session["name"],)).fetchall()) >= 10:
            flash("User has too many favourite dishes, action cancelled.")
            return jsonify({"status": "failure"})
        # Add recipe to database
        db.execute("INSERT INTO favDishes (dishId, userId, name, description, instructions, ingredients,"
                   "rating, imageUrl, videoUrl) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (recipe["dish_id"],
                                                                                      session["name"],
                                                                                      recipe["name"],
                                                                                      recipe["description"],
                                                                                      recipe["instructions"],
                                                                                      recipe["dish_ingredients"],
                                                                                      recipe["ratings"],
                                                                                      recipe["image_url"],
                                                                                      recipe["video_url"]))
        con.commit()
    return jsonify({"status": "success"})


@app.route("/recipe/remove", methods=["POST"])
@login_required
def delete_recipe():
    recipe = request.json
    with sqlite3.connect("identifier.sqlite") as con:
        db = con.cursor()
        db.execute("DELETE FROM favDishes WHERE userId = ? AND dishId = ?",
                   (session["name"], recipe["dish_id"]))
        con.commit()
    return jsonify({"status": "success"})


@app.route("/favourite_dishes")
@login_required
def get_favourite_dishes():
    user_favourite_recipes = []
    with sqlite3.connect("identifier.sqlite") as con:
        db = con.cursor()
        recipes = db.execute("SELECT dishId, name, description, instructions,"
                             "ingredients, rating, imageUrl, videoUrl FROM favDishes WHERE userId = ? ORDER BY name",
                             (session["name"],)).fetchall()
    # Transfer the tuple list into the dictionary
    for recipe in recipes:
        user_favourite_recipes.append({
            "dish_id": recipe[0],
            "name": recipe[1],
            "description": recipe[2],
            "instructions": recipe[3],
            "dish_ingredients": recipe[4],
            "ratings": recipe[5],
            "image_url": recipe[6],
            "video_url": recipe[7]
        })
    # user_favourite_recipes.sort(key=lambda x: len(x["name"]))
    return render_template("favourite_dishes.html", user_favourite_recipes=user_favourite_recipes)


@app.route("/update_paging_number", methods=["POST"])
def update_paging_number():
    paging_number = int(request.form.get("paging_number", 1)) - 1
    session["paging_number"] = paging_number
    return redirect("/")


if __name__ == '__main__':
    app.run()
