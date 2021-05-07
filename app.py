from flask import Flask, render_template, redirect, session, flash, url_for, request
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, bcrypt, User, Recipe
from forms import SignUpForm, LogInForm, DeleteForm
from werkzeug.exceptions import Unauthorized
from sqlalchemy.exc import IntegrityError
import requests
import json
import os


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 'postgresql://meal_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "secreto001")
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

connect_db(app)
toolbar = DebugToolbarExtension(app)



url = ""
CATEGORY_URL="https://www.themealdb.com/api/json/v1/1/filter.php?c="
MAIN_IN_URL = "https://www.themealdb.com/api/json/v1/1/filter.php?i="
NAME_URL ="https://www.themealdb.com/api/json/v1/1/search.php?s="
KEY = "1"



@app.route("/")
def homepage():
    """Homepage of site; or redirect to login."""
    if "user_id" not in session:
        flash("Login First or sign for an ccount!","primary")
        return redirect("/login")
    try:
        res = requests.get("https://www.themealdb.com/api/json/v1/1/categories.php", params={'key': KEY})
    except:
        return render_template("404.html")
    d = res.json()
    categories = d["categories"]
    meals = []
    url = "https://www.themealdb.com/api/json/v1/1/filter.php?c="
    for category in categories:
        categoryName =category['strCategory']
        try:
            res = requests.get(f"{url}{categoryName}", params={'key': KEY})
        except:
            flash("Something went wrong while requesting data to Api. Try again later?")
            return render_template("404.html")
        data = res.json()
        m = data["meals"]
        meals = meals + m
    return render_template("meals.html", meals=meals)

@app.route("/help")
def user_help():
    """route where users can view all categories and can get help navigating the app"""
    if "user_id" not in session:
        flash("Login First or sign for an ccount!","primary")
        return redirect("/login")
    try:
        res = requests.get("https://www.themealdb.com/api/json/v1/1/categories.php", params={'key': KEY})
    except:
        return render_template("404.html")
    data = res.json()
    categories = data["categories"]
    return render_template("help.html", categories=categories)

@app.route('/find-meals', methods=["POST"])
def get_meals():
    """submitting form to find meals based on search input."""
    if "user_id" not in session:
        flash("Login First or sign for an ccount!","primary")
        return redirect("/login")
    search_by = request.form["search-by"]
    search_term = request.form["search-term"]
    if search_by == "category":
        url = CATEGORY_URL
    if search_by == "mainIngridient":
        url = MAIN_IN_URL
    if search_by == "name":
        url = NAME_URL
    try:
        res = requests.get(f"{url}{search_term}", params={'key': KEY})
    except:
        return render_template("404.html")
    data = res.json()
    
    meals = data["meals"]
    if meals == None:
        flash(f"Searching by {search_by} NO MATCHES for {search_term}", "warning")
        return render_template("makeMeal.html")
    flash(f"Searching {search_by} of {search_term}", "success")
    return render_template("searchMeals.html", meals=meals)


@app.route("/find-meals/<category>")
def get_category_meals(category):
    """Get all meals by category"""
    if "user_id" not in session:
        flash("Login First or sign for an ccount!","primary")
        return redirect("/login")
    url = "https://www.themealdb.com/api/json/v1/1/filter.php?c="
    try:
        res = requests.get(f"{url}{category}", params={'key': KEY})
    except:
        return render_template("404.html")
    data = res.json()
    meals = data["meals"]
    return render_template("category.html", meals=meals)

@app.route("/find-meals/<int:id>")
def get_meal(id):
    """render a single meal by id"""
    if "user_id" not in session:
        flash("Login First or sign for an ccount!","primary")
        return redirect("/login")
    url = "https://www.themealdb.com/api/json/v1/1/lookup.php?i="
    try:
        res = requests.get(f"{url}{id}", params={'key': KEY})
    except:
        return render_template("404.html")
    data = res.json()
    m = data["meals"]
    meal = m[0]
    return render_template("meal.html", meal=meal)

@app.route("/my-recipes", methods=["POST"])
def add_recipe():
    """save recipe to users recipes"""
    if "user_id" not in session:
        flash("Login First or sign for an ccount!","primary")
        return redirect("/login")
    user_id = session["user_id"]
    recipe_id = request.form["recipe"]
    r = Recipe.query.filter(Recipe.user_id==user_id, Recipe.recipe_id==recipe_id).first()
    if r is not None:
        flash("Already in your recipes", "warning")
        return redirect("/")
    try:
        recipe = Recipe(
            recipe_id = recipe_id,
            user_id = user_id
        )
        db.session.add(recipe)
        db.session.commit()
    except IntegrityError:
        flash("Already in your Recipes!")
    my_recipes = []
    recipes = Recipe.query.filter(Recipe.user_id==session["user_id"]).all()
    for recipe in recipes:
        url = "https://www.themealdb.com/api/json/v1/1/lookup.php?i="
        try:
            res = requests.get(f"{url}{recipe.recipe_id}", params={'key': KEY})
        except:
            flash("That recipe is no longer available", "warning")
        data = res.json()
        my_recipe = data["meals"]
        r = my_recipe[0]
        my_recipes.append(r)
    return render_template("recipes.html", my_recipes=my_recipes)


@app.route("/my-recipes")
def get_user_recipes():
    """get all user recipes"""
    if "user_id" not in session:
        flash("Login or Signup first", "primary")
        return redirect("/login")
    my_recipes = []
    recipes = Recipe.query.filter(Recipe.user_id==session["user_id"]).all()
    for recipe in recipes:
        url = "https://www.themealdb.com/api/json/v1/1/lookup.php?i="
        try:
            res = requests.get(f"{url}{recipe.recipe_id}", params={'key': KEY})
        except:
            flash("That recipe is no longer available", "warning")
        data = res.json()
        recipe = data["meals"]
        r = recipe[0]
        my_recipes.append(r)
    return render_template("recipes.html", my_recipes=my_recipes)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Sign UP a user: produce form and handle form submission."""

    if "user_id" in session:
        flash("You already have an account", "danger")
        return redirect("/")

    form = SignUpForm()
    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                image_url=form.image_url.data
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('signup.html', form=form)

        
        session["user_id"] = user.id

        return redirect("/")

    else:
        return render_template("signup.html", form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Produce login form or handle login."""

    if "user_id" in session:
        flash("You are already logged in!", "danger")
        return redirect("/")

    form = LogInForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)  # <User> or False
        if user:
            session["user_id"] = user.id
            return redirect("/")
        else:
            form.username.errors = ["Invalid username/password."]
            return render_template("login.html", form=form)

    return render_template("login.html", form=form)


@app.route("/logout")
def logout():
    """Logout, pop user_id from session"""
    if "user_id" not in session:
        raise Unauthorized()
    session.pop("user_id")
    flash("See you later!", "primary")
    return redirect("/login")


@app.route("/users/<int:id>")
def show_user(id):
    """User profile"""
    if "user_id" not in session or id != session["user_id"]:
        raise Unauthorized()
    user = User.query.get(id)
    form = DeleteForm()
    return render_template("user.html", user=user, form=form)


@app.route("/users/<int:id>/delete", methods=["POST"])
def remove_user(id):
    """Remove user and redirect to login."""
    if "user_id" not in session or id != session["user_id"]:
        raise Unauthorized()

    user = User.query.get(id)
    db.session.delete(user)
    db.session.commit()
    session.pop("user_id")
    flash("Sad to see you go", "warning")
    return redirect("/login")
