from flask import Flask, render_template
from user import user_routes
from admin import admin_routes

app = Flask(__name__, static_url_path='/static')

app.secret_key = 'your_secret_key'


# Register user and admin routes
app.register_blueprint(user_routes)
app.register_blueprint(admin_routes)


@app.route('/')
def index():
    return render_template('/index.html')


if __name__ == '__main__':
    app.run(debug=True)
