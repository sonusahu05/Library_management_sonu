from flask import Flask , request , jsonify , render_template 
from models import *
from views import *
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from datetime import date
import requests
import json
import bcrypt


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://admin:sonusahu@banking.ccsivnqsc7t6.us-east-1.rds.amazonaws.com/library'
db.init_app(app)

app.config['JWT_SECRET_KEY'] = '8f3d5e2bfa504e8494bdeca76f7309b9'
jwt = JWTManager(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/rent', methods=['POST'])
@jwt_required()
def rent():
    current_user = get_jwt_identity()
    data = request.get_json()
    title = data['title']
    user = User.query.filter_by(username=current_user).first()
    book = Book.query.filter_by(title=title).first()
    if user and book:
        if book.availability and book.count > 0:
            rent = Rent(user_id=user.user_id, book_id=book.book_id, rent_date=datetime.datetime.now(), due_date=datetime.datetime.now() - datetime.timedelta(days=7))
            book.count -= 1
            if book.count == 0:
                book.availability = False
            db.session.add(rent)
            db.session.commit()
            return jsonify({'message': 'Book rented successfully!',
                            'book_id': book.book_id,
                            'title': book.title,})
        else:
            earliest_rent = Rent.query.filter_by(book_id=book.book_id).order_by(Rent.due_date.asc()).first()
            if earliest_rent:
                due_date = earliest_rent.due_date
                return jsonify({'message': 'Book not available!', 'next_availibility': due_date})
            else:
                return jsonify({'message': 'Book not available!', 'due_date': None})
    else:
        return jsonify({'message': 'Book or user not found!'})
    
@app.route('/my_books', methods=['POST'])
@jwt_required()
def my_books():
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()
    if user:
        rents = Rent.query.filter_by(user_id=user.user_id).all()
        rent_list = []
        for rent in rents:
            book = Book.query.filter_by(book_id=rent.book_id).first()
            rent_data = {
                'book_id': book.book_id,
                'title': book.title,
                'author': book.author,
                'publication_date': str(book.publication_date),
                'isbn': book.isbn,
                'rent_date': str(rent.rent_date),
                'due_date': str(rent.due_date)
            }
            rent_list.append(rent_data)
        return jsonify(rent_list)
    else:
        return jsonify({'message': 'User not found!'})


@app.route('/not_returned', methods=['POST'])
@jwt_required()
def not_returned():
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()
    if user and user.is_admin:
        rents = Rent.query.filter(Rent.due_date < datetime.datetime.now()).all()
        rent_list = []
        for rent in rents:
            book = Book.query.filter_by(book_id=rent.book_id).first()
            user = User.query.filter_by(user_id=rent.user_id).first()
            rent_data = {
                'book_id': book.book_id,
                'title': book.title,
                'author': book.author,
                'publication_date': str(book.publication_date),
                'isbn': book.isbn,
                'rent_date': str(rent.rent_date),
                'due_date': str(rent.due_date),
                'username': user.username
            }
            rent_list.append(rent_data)
        return jsonify(rent_list)
    else:
        return jsonify({'message': 'User not found!'})
    

@app.route('/return', methods=['POST'])
@jwt_required()
def return_book():
    current_user = get_jwt_identity()
    data = request.get_json()
    book_id = data['book_id']
    user = User.query.filter_by(username=current_user).first()
    book = Book.query.filter_by(book_id=book_id).first()
    if user and book:
        rent = Rent.query.filter_by(user_id=user.user_id, book_id=book.book_id).first()
        if rent:
            db.session.delete(rent)
            book.count += 1
            if book.count > 0:
                book.availability = True
            db.session.commit()
            return jsonify({'message': 'Book returned successfully!'})
        else:
            return jsonify({'message': 'Book not rented!'})
    else:
        return jsonify({'message': 'Book or user not found!'})

@app.route('/increase_book_count', methods=['PUT'])
@jwt_required()
def increase_book_count():
    current_user = get_jwt_identity()
    data = request.get_json()
    book_id = data['book_id']
    count=data['count']
    user = User.query.filter_by(username=current_user).first()
    book = Book.query.filter_by(book_id=book_id).first()
    if user and user.is_admin and book:
        book.count += count
        db.session.commit()
        return jsonify({'message': 'Book count increased successfully!'})
    else:
        return jsonify({'message': 'Book or user not found!'})


@app.route('/books', methods=['GET'])
def books():
    books = Book.query.all()
    
    book_list = []
    for book in books:
        book_data = {
            'book_id': book.book_id,
            'title': book.title,
            'author': book.author,
            'publication_date': str(book.publication_date),
            'isbn': book.isbn,
            'availability': book.availability,
            'count': book.count
        }
        book_list.append(book_data)

    return jsonify(book_list)



@app.route('/add_book', methods=['POST'])
@jwt_required()
def add_book():
    current_user = get_jwt_identity()
    data = request.get_json()
    title = data['title']
    author = data['author']
    publication_date = data['publication_date']
    isbn = data['isbn']
    availability = data['availability']
    count = data['count']
    user=User.query.filter_by(username=current_user).first()
    if user and user.is_admin :
        book = Book(title=title, author=author, publication_date=publication_date, isbn=isbn, availability=availability, count=count)
        db.session.add(book)
        db.session.commit()
        return jsonify( {
                        "message": "Book added successfully",
                        "book_id": book.book_id,
                        })
    else:
        return "User not authorized to add book"

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data['username']
    password = data['password']
    email = data['email']
    first_name = data['first_name']
    last_name = data['last_name']
    is_admin = data['is_admin']
    salt = bcrypt.gensalt()  # Generate a salt
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)

    user = User(username=username, password=hashed_password, email=email, first_name=first_name, last_name=last_name, is_admin=is_admin)
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'New user created!',
                    'username': user.username,
                    'status': 'success',
                    'success code': '200'})


@app.route('/delete_book', methods=['DELETE'])
@jwt_required()
def delete_book():
    current_user = get_jwt_identity()
    data = request.get_json()
    book_id = data['book_id']
    user=User.query.filter_by(username=current_user).first()
    if user and user.is_admin :
        book = Book.query.filter_by(book_id=book_id).first()
        db.session.delete(book)
        db.session.commit()
        return jsonify({'message': 'Book deleted successfully!'
                        ,
                        'status': 'success',
                        'success code': '200',
                        'book id': book.book_id,})
    else:
        return jsonify({'message': 'User not authorized to delete book!'})


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']
    user = User.query.filter_by(username=username).first()
    if verify_credentials(username, password):
        access_token = create_access_token(identity=username)
        return jsonify({'token': access_token,
                        'status': 'success',
                        'success code': '200',
                        'user id ': user.user_id,})
    else:
        return jsonify({
                        "status": "Incorrect username/password provided. Please retry",
                        "status_code": 401
                        })

@app.route('/check_auth' , methods=['POST'])
@jwt_required()
def check_auth():
    current_user = get_jwt_identity()
    data=request.get_json()
    username = data['username']
    if current_user == username:
        return jsonify({'message': 'Authorized'})
    else:
        return jsonify({'message': 'Unauthorized'})

@app.route('/create_tables')
def create_tables():
    db.create_all()
    return "Tables created"

if __name__ == '__main__':
    app.run(debug=True)