# FoodX
#### Description:
This project is a web application that allows users to search for recipes based on the ingredients they have on hand. The user can enter a list of ingredients separated by commas, and the application will return a list of recipes that include those ingredients. Users can create accounts, modify their credentials and delete accounts. Logged in users have more possibilities on FoodX, like saving recipes to favourites list and be welcomed by their name (if they wanted to provide one)


##### Files
* `app.py`: The main file that runs the web application using Flask. It contains the routes for the index page, login page, and registration page. It also contains the logic for communicating with the Tasty API to retrieve the recipe information and for handling user authentication and session management.
* `identifier.sqlite`: The SQLite database that stores the user information, including the user's hashed password, their favourite recipes and ingredients possible to enter.
* `templates/`: A folder that contains the HTML templates used by the application. The templates include the index page, the login page, and the registration page. Layout is the basic template which consists of main links and functionalities. Index is crucial for API connection and browsing recipes. In the templates I used jinja2 syntax for connection with Flask application.
* `static/` :A folder that contains the CSS and JavaScript files used by the application. The CSS file is used for styling the HTML templates, and the JavaScript file is used for handling the page change functionality. There are also img files for the graphic part of the project: main image and search bar magnifying glass. They are duly contributed in the code.


##### Design Choices
One of the main design choices made for this project was to use the Tasty API for retrieving the recipe information. This was chosen because it allowed for a wide range of recipes to be available to the user and provided detailed information about each recipe.

Another design choice was to use SQLite for storing the user information. This was chosen because it is a lightweight database that is easy to set up and use. It also allowed for easy integration with the Flask application.

The application also uses the Flask-Login library for handling user authentication and session management. This was chosen because it provides an easy to use and secure way to handle user authentication and session management.

In the HTML templates, I used Bootstrap for styling the pages and making them responsive. This was chosen because it provides a simple and consistent way to style the pages and make them look good on different devices.

Finally, I used JavaScript to handle the page change functionality. This was chosen because it allows for a seamless and dynamic experience for the user.

Overall, the main reason for these choices is that I learned these technologies during CS50x, and because of that I could use them effectively. I had to learn much more about them though. Beyond that,the design choices made for this project were chosen to provide a simple and user-friendly experience while also being efficient and secure.
