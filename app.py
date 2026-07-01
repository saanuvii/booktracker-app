
import os
import requests
import collections
import random
import csv
from io import StringIO
from datetime import datetime, date
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from models import db, Book, User
from functools import wraps
from flask import abort

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

os.makedirs(os.path.join(app.root_path, 'instance'), exist_ok=True)

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- AUTHENTICATION ROUTES ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('index'))
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password_hash, request.form['password']):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated: return redirect(url_for('index'))
    if request.method == 'POST':
        if User.query.filter_by(username=request.form['username']).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('register'))
        new_user = User(
            username=request.form['username'],
            password_hash=generate_password_hash(request.form['password'])
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- PROFILE ROUTE ---

@app.route('/update_goal', methods=['POST'])
@login_required
def update_goal():
    try:
        new_goal = int(request.form.get('yearly_goal', 50))
        if new_goal < 1:
            new_goal = 1
        current_user.yearly_goal = new_goal
        db.session.commit()
        flash('Reading goal updated successfully!', 'success')
    except ValueError:
        flash('Invalid goal number.', 'danger')
    return redirect(url_for('profile'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        new_pass = request.form.get('new_password')
        if new_pass:
            current_user.password_hash = generate_password_hash(new_pass)
            db.session.commit()
            flash('Password updated successfully!', 'success')
            return redirect(url_for('profile'))
            
    books = Book.query.filter_by(user_id=current_user.id).all()
    total_books = len(books)
    completed_books = len([b for b in books if b.status == 'Completed'])
    five_star_books = len([b for b in books if b.rating == 5])
    pages_read = sum(b.current_page for b in books)
    
    return render_template('profile.html', 
                           total_books=total_books, 
                           completed=completed_books, 
                           five_star=five_star_books, 
                           pages_read=pages_read)

# --- ADMIN SECURITY DECORATOR ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403) # Forbidden
        return f(*args, **kwargs)
    return decorated_function

# --- ADMIN PANEL ROUTES ---
@app.route('/admin')
@admin_required
def admin_dashboard():
    # Gather platform-wide statistics
    all_users = User.query.all()
    all_books = Book.query.all()
    total_users = len(all_users)
    total_books = len(all_books)
    total_pages = sum(b.current_page for b in all_books)
    
    # Calculate books per user for the table
    user_stats = []
    for user in all_users:
        user_books = [b for b in all_books if b.user_id == user.id]
        user_stats.append({
            'user': user,
            'book_count': len(user_books),
            'completed_count': len([b for b in user_books if b.status == 'Completed'])
        })
        
    return render_template('admin.html', 
                           users=user_stats, 
                           total_users=total_users, 
                           total_books=total_books,
                           total_pages=total_pages)

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    if user_id == current_user.id:
        flash('You cannot delete your own admin account!', 'danger')
        return redirect(url_for('admin_dashboard'))
        
    user_to_delete = User.query.get_or_404(user_id)
    # Because of the cascade="all, delete-orphan" in models.py, 
    # deleting the user automatically deletes all their books!
    db.session.delete(user_to_delete)
    db.session.commit()
    
    flash(f'User {user_to_delete.username} and all their data have been permanently deleted.', 'success')
    return redirect(url_for('admin_dashboard'))

# --- CORE ROUTES ---
@app.route('/')
@login_required
def index():
    books = Book.query.filter_by(user_id=current_user.id).all()
    total_books = len(books)
    completed = len([b for b in books if b.status == 'Completed'])
    reading = len([b for b in books if b.status == 'Currently Reading'])
    want_to_read = len([b for b in books if b.status == 'Want to Read'])
    total_pages_read = sum(b.current_page for b in books)
    completion_rate = round((completed / total_books * 100) if total_books > 0 else 0)
    recently_added = Book.query.filter_by(user_id=current_user.id).order_by(Book.date_added.desc()).limit(5).all()

    current_year = datetime.now().year
    yearly_goal = current_user.yearly_goal 
    books_this_year = len([b for b in books if b.status == 'Completed' and b.completion_date and b.completion_date.year == current_year])
    yearly_progress = min(int((books_this_year / yearly_goal) * 100), 100)

    genres = [b.genre for b in books if b.genre]
    genre_counts = dict(collections.Counter(genres))
    top_genres = dict(sorted(genre_counts.items(), key=lambda item: item[1], reverse=True)[:5])

    return render_template('index.html', stats={
        'total': total_books, 'completed': completed, 'reading': reading, 'want': want_to_read,
        'rate': completion_rate, 'pages_read': total_pages_read
    }, recent_books=recently_added, challenge={'goal': yearly_goal, 'current': books_this_year, 'progress': yearly_progress, 'year': current_year}, genre_data=top_genres)

@app.route('/books')
@login_required
def books():
    filter_type = request.args.get('filter', 'all')
    series_name = request.args.get('series')
    tag_name = request.args.get('tag')
    
    query = Book.query.filter_by(user_id=current_user.id)
    if series_name: query = query.filter(Book.series == series_name)
    elif tag_name: query = query.filter(Book.tags.ilike(f'%{tag_name}%'))
    elif filter_type == 'favorites': query = query.filter(Book.favorite == True)
    elif filter_type in ['Want to Read', 'Currently Reading', 'Completed', 'Abandoned']:
        query = query.filter(Book.status == filter_type)
        
    all_books = query.order_by(Book.title).all()
    return render_template('books.html', books=all_books, current_filter=filter_type, current_series=series_name, current_tag=tag_name)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_book():
    if request.method == 'POST':
        try:
            total_pages = int(request.form['total_pages'])
            status = request.form['status']
            current_page = total_pages if status == 'Completed' else int(request.form.get('current_page', 0))
            comp_date = date.today() if status == 'Completed' else None

            new_book = Book(
                title=request.form['title'],
                author=request.form['author'],
                series=request.form.get('series'),               
                series_number=request.form.get('series_number'), 
                genre=request.form.get('genre'),
                tags=request.form.get('tags'),
                cover_image=request.form.get('cover_image'),
                total_pages=total_pages,
                current_page=current_page,
                status=status,
                rating=int(request.form.get('rating', 0)),
                notes=request.form.get('notes'),
                favorite=False,
                completion_date=comp_date,
                user_id=current_user.id
            )
            db.session.add(new_book)
            db.session.commit()
            flash('Book added successfully!', 'success')
            return redirect(url_for('books'))
        except Exception as e:
            flash(f'Error adding book: {str(e)}', 'danger')
            db.session.rollback()
    return render_template('add_book.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_book(id):
    book = Book.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    if request.method == 'POST':
        try:
            book.title = request.form['title']
            book.author = request.form['author']
            book.series = request.form.get('series')               
            book.series_number = request.form.get('series_number') 
            book.genre = request.form.get('genre')
            book.tags = request.form.get('tags')
            book.cover_image = request.form.get('cover_image')
            book.total_pages = int(request.form['total_pages'])
            book.rating = int(request.form.get('rating', 0))
            
            new_status = request.form['status']
            if new_status == 'Completed' and book.status != 'Completed':
                book.completion_date = date.today()
            elif new_status != 'Completed':
                book.completion_date = None
                
            book.status = new_status
            book.notes = request.form.get('notes')
            
            if book.status == 'Completed': book.current_page = book.total_pages
            elif book.status == 'Currently Reading': book.current_page = int(request.form.get('current_page', 0))
            elif book.status == 'Want to Read': book.current_page = 0
            else: book.current_page = int(request.form.get('current_page', book.current_page))
            
            db.session.commit()
            flash('Book updated successfully!', 'success')
            return redirect(url_for('book_detail', id=book.id))
        except Exception as e:
            flash(f'Error updating book: {str(e)}', 'danger')
            db.session.rollback()
    return render_template('edit_book.html', book=book)

@app.route('/book/<int:id>')
@login_required
def book_detail(id):
    book = Book.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    return render_template('book_detail.html', book=book)

@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_book(id):
    book = Book.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    db.session.delete(book)
    db.session.commit()
    flash('Book deleted.', 'info')
    return redirect(url_for('books'))

@app.route('/search')
@login_required
def search():
    query = request.args.get('q', '')
    results = Book.query.filter(Book.user_id == current_user.id).filter(
        db.or_(Book.title.ilike(f'%{query}%'), Book.author.ilike(f'%{query}%'))
    ).all()
    return render_template('books.html', books=results, search_query=query, current_filter='all')

@app.route('/toggle_favorite/<int:id>', methods=['POST'])
@login_required
def toggle_favorite(id):
    book = Book.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    book.favorite = not book.favorite
    db.session.commit()
    return {'success': True, 'favorite': book.favorite}

# --- CSV IMPORT & EXPORT ROUTES ---
@app.route('/export_csv')
@login_required
def export_csv():
    books = Book.query.filter_by(user_id=current_user.id).all()
    def generate():
        data = StringIO()
        writer = csv.writer(data)
        writer.writerow(['Title', 'Author', 'Series', 'Series Number', 'Genre', 'Tags', 'Status', 'Total Pages', 'Current Page', 'Rating', 'Completion Date', 'Notes', 'Cover Image'])
        yield data.getvalue()
        data.seek(0); data.truncate(0)
        for b in books:
            comp_date_str = b.completion_date.strftime('%Y-%m-%d') if b.completion_date else ''
            writer.writerow([b.title, b.author, b.series, b.series_number, b.genre, b.tags, b.status, b.total_pages, b.current_page, b.rating, comp_date_str, b.notes, b.cover_image])
            yield data.getvalue()
            data.seek(0); data.truncate(0)
    return Response(generate(), mimetype='text/csv', headers={"Content-Disposition": "attachment; filename=my_library.csv"})

@app.route('/import_csv', methods=['POST'])
@login_required
def import_csv():
    if 'csv_file' not in request.files:
        flash('No file uploaded.', 'danger')
        return redirect(url_for('index'))
    file = request.files['csv_file']
    if file.filename == '':
        flash('No file selected.', 'danger')
        return redirect(url_for('index'))
    
    try:
        stream = StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_input = csv.DictReader(stream)
        count = 0
        skipped = 0
        for row in csv_input:
            title = row.get('Title', 'Unknown').strip()
            author = row.get('Author', 'Unknown').strip()
            
            duplicate = Book.query.filter(
                db.func.lower(Book.title) == title.lower(),
                db.func.lower(Book.author) == author.lower(),
                Book.user_id == current_user.id
            ).first()
            
            if duplicate:
                skipped += 1
                continue

            status = row.get('Status', 'Want to Read')
            
            comp_date = None
            if status == 'Completed':
                raw_date = row.get('Completion Date')
                if raw_date:
                    try:
                        comp_date = datetime.strptime(raw_date, '%Y-%m-%d').date()
                    except ValueError:
                        comp_date = date.today()
                else:
                    comp_date = date.today()

            book = Book(
                title=title,
                author=author,
                series=row.get('Series'),
                series_number=row.get('Series Number'),
                genre=row.get('Genre'),
                tags=row.get('Tags'),
                status=status,
                total_pages=int(row.get('Total Pages') or 0),
                current_page=int(row.get('Current Page') or 0),
                rating=int(row.get('Rating') or 0),
                completion_date=comp_date,
                notes=row.get('Notes'),
                cover_image=row.get('Cover Image'),
                user_id=current_user.id
            )
            db.session.add(book)
            count += 1
        db.session.commit()
        
        if skipped > 0:
            flash(f'Successfully imported {count} books! (Skipped {skipped} duplicates)', 'success')
        else:
            flash(f'Successfully imported {count} books!', 'success')
            
    except Exception as e:
        flash(f'Error importing CSV: Make sure headers match exactly. ({str(e)})', 'danger')
        db.session.rollback()
    return redirect(url_for('index'))

@app.route('/api/random_book')
@login_required
def random_book():
    books = Book.query.filter_by(status='Want to Read', user_id=current_user.id).all()
    if not books: return jsonify({'success': False, 'error': 'No books found in your "Want to Read" list.'})
    picked = random.choice(books)
    return jsonify({'success': True, 'book': {'id': picked.id, 'title': picked.title, 'author': picked.author, 'cover_image': picked.cover_image or ''}})

@app.route('/api/fetch_book', methods=['POST'])
def fetch_book():
    data = request.get_json()
    try:
        response = requests.get(f'https://openlibrary.org/search.json?q={data.get("query")}&limit=1')
        response.raise_for_status()
        doc = response.json().get('docs', [{}])[0]
        if not doc: return {'success': False, 'error': 'No book found.'}
        
        return {'success': True, 'data': {
            'title': doc.get('title', ''),
            'author': ', '.join(doc.get('author_name', [])),
            'total_pages': doc.get('number_of_pages_median') or doc.get('number_of_pages') or '',
            'genre': doc.get('subject', [''])[0].split(',')[0][:50] if doc.get('subject') else '',
            'cover_image': f"https://covers.openlibrary.org/b/id/{doc.get('cover_i')}-L.jpg" if doc.get('cover_i') else ''
        }}
    except Exception as e:
        return {'success': False, 'error': str(e)}

if __name__ == '__main__':
    app.run(debug=True)