from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Make sure to set a secret key for sessions

DATABASE = 'posts.db'
import sqlite3

conn = sqlite3.connect('posts.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    author TEXT NOT NULL,
    date_published TEXT NOT NULL
);
''')

conn.commit()
conn.close()


# Database connection function
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # This allows us to access rows by column name (like dictionaries)
    return conn

# Function to safely parse datetime with or without fractional seconds
def parse_datetime(date_str):
    try:
        # Try parsing with fractional seconds (microseconds)
        return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S.%f')
    except ValueError:
        # If it fails, parse without fractional seconds
        return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')

# Home route to display all blog posts
@app.route('/')
def index():
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts ORDER BY date_published DESC').fetchall()
    conn.close()

    # Convert sqlite3.Row to dictionary and modify the date_published field to datetime
    post_list = []
    for post in posts:
        post_dict = dict(post)  # Convert to dictionary
        post_dict['date_published'] = parse_datetime(post_dict['date_published'])
        post_list.append(post_dict)

    return render_template('index.html', posts=post_list)

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Here you should add logic to verify user credentials
        # For simplicity, we're assuming a successful login
        session['user'] = username
        return redirect(url_for('dashboard'))
    
    return render_template('login.html')

# Dashboard route (after login)
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:  # Check if user is logged in
        return redirect(url_for('login'))  # Redirect to login page if not logged in

    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts WHERE author = ? ORDER BY date_published DESC', (session['user'],)).fetchall()
    conn.close()

    # Convert sqlite3.Row to dictionary and modify the date_published field to datetime
    post_list = []
    for post in posts:
        post_dict = dict(post)
        post_dict['date_published'] = parse_datetime(post_dict['date_published'])
        post_list.append(post_dict)

    return render_template('dashboard.html', posts=post_list)

# Add a new post
@app.route('/add_post', methods=['GET', 'POST'])
def add_post():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        date_published = datetime.now()  # Current time with fractional seconds

        conn = get_db_connection()
        conn.execute('INSERT INTO posts (title, content, author, date_published) VALUES (?, ?, ?, ?)',
                     (title, content, session['user'], date_published))
        conn.commit()
        conn.close()

        return redirect(url_for('dashboard'))

    return render_template('add_post.html')

# Edit an existing post
@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    conn.close()

    if post is None:
        return "Post not found", 404

    if post['author'] != session['user']:
        return "You do not have permission to edit this post", 403

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        conn = get_db_connection()
        conn.execute('UPDATE posts SET title = ?, content = ? WHERE id = ?', (title, content, post_id))
        conn.commit()
        conn.close()

        return redirect(url_for('dashboard'))

    return render_template('edit_post.html', post=post)

# Delete a post
from flask import request

@app.route('/delete_post/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    if request.form.get('_method') == 'DELETE':
        if 'user' not in session:
            return redirect(url_for('login'))  # Redirect to login if not logged in

        conn = get_db_connection()
        post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()

        if post is None:
            return "Post not found", 404

        if post['author'] != session['user']:
            return "You do not have permission to delete this post", 403

        conn.execute('DELETE FROM posts WHERE id = ?', (post_id,))
        conn.commit()
        conn.close()

        return redirect(url_for('index'))  # Redirect to the homepage after deletion
    else:
        return "Method Not Allowed", 405

#Read more
@app.route('/post/<int:post_id>')
def post_detail(post_id):
    conn = get_db_connection()
    post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    conn.close()

    if post is None:
        return "Post not found", 404

    post_dict = dict(post)
    post_dict['date_published'] = parse_datetime(post_dict['date_published'])

    return render_template('post_detail.html', post=post_dict)


# Logout route
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
