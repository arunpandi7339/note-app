from flask import Flask,request,jsonify
from pymongo import MongoClient
import jwt
from datetime import datetime,timedelta
from flask_cors import CORS
import uuid
from functools import wraps
from werkzeug.security import generate_password_hash,check_password_hash


SECRET_KEY = "4ac1b779a56862b74b1b2cc1b87d90d6f99a5b70d83534c20400d8fd3837e29f7a4894fc"

# Flask   ----------->
app = Flask(__name__)
CORS(app)

# batabase connection  =============>
database = MongoClient("mongodb+srv://arunpandi9794:arun_17_05@cluster0.q1ixhxq.mongodb.net/?appName=Cluster0")
try:
    conect = database.admin.command("ping")
    print("data base conectet successfullyyyy")
except Exception as error :
    print(error)


# file set  ==========>

note = database['note']
note_user =note["note_users"]
notes = note['user_notes']


# Token authorization -------------------------------------------------------------------->
def token_authorization(f):
    @wraps(f)
    def date_decode(*i,**j):

        token = None

        auth_header = request.headers.get("Authorization")

        # if auth_header:
        #     token = auth_header.split(" ")[1]

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

        if not token :
            return jsonify({"msg":"token not found"}), 401
        
        try:
            user = jwt.decode(token , SECRET_KEY ,algorithms=["HS256"])
            user_id = user["user_id"]
            
        except jwt.ExpiredSignatureError :
            return jsonify({"msg":"Token expired. Try again "}), 401
        
        except jwt.InvalidTokenError :
            return jsonify({"msg":'Invalid Token'}), 401
        
        return f(user_id ,*i,**j)
    return date_decode

# API route  ---------------------------------------------------------------------------------------->
@app.route("/")
def demo():
    return jsonify({"msg":"page is live"})


#  user id creation --------------------------------------------------------------------------------->
@app.route("/register" , methods = ['POST'])
def user_creation():

    data = request.get_json()
    if not data:
        return jsonify({"msg": "invalid request"})
    
    if not data.get("username"):
        return jsonify({"msg": "username required"})
    
    if not data.get("email") or not data.get("password"):
        return jsonify({"msg": "email & password required"})

    existing_user = note_user.find_one({"email": data.get("email")})
    if existing_user:
        return jsonify({"msg": "email already exists"})

    password = data.get("password")

    create = note_user.insert_one({
        "user_id":str(uuid.uuid4()),
        "username":data.get("username"),
        "email":data.get("email"),
        "password":generate_password_hash(password),
        "create_time":datetime.now(),
        "update_time":datetime.now()
    })
    if not create.inserted_id:
        return jsonify({"msg": "creation failed"})
    
    return jsonify({"msg":'user_id creation successfullyyy...'})


# user login ----------------------------------------------------------------------------------->
@app.route("/login" , methods = ["POST"])
def user_login():

    token = None
    data = request.get_json()
    if not data:
        return jsonify({"msg": "invalid request"})

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"msg": "email & password required"})

    user = note_user.find_one({"email":email})

    if not user or not check_password_hash(user["password"],password) :
        return jsonify({"msg":'email or password not found'}),401
    
    token_data = {
        "user_id":user["user_id"],
        "exp":datetime.now() + timedelta( hours=1)
    }

    token = jwt.encode(token_data, SECRET_KEY, algorithm="HS256")

    return jsonify({
        "token":token,
        "username":user["username"],
        "user_id":user["user_id"]
        }),200


# profile  ------------------------------------------------------------------------------------------>
@app.route("/profile" ,methods = ["GET"])
@token_authorization
def user_detail(user_id):

    user = note_user.find_one({"user_id":user_id},{"_id":0,"password":0})

    if not user:
        return jsonify({"msg":"user not found"})
    
    return jsonify(user)


# user id update ------------------------------------------------------------------------------------>
@app.route("/user/update", methods=["PUT"])
@token_authorization
def user_id_update(user_id):
    data = request.get_json()

    password = data.get("password")
    user = note_user.find_one({"user_id":user_id},{"_id":0})

    if not user :
        return jsonify({"msg":"user not found"})
    
    uptade = note_user.update_one(
        {"user_id": user_id},
        {"$set": {
                "username": data.get("username", user["username"]),
                "email": data.get("email", user["email"]),
                "password": generate_password_hash(password) if password else user["password"],
                "update_time": datetime.now()
            }}
    )

    if uptade.modified_count == 0:
        return jsonify({"msg": "no changes made"})

    return jsonify({"msg":"user updated successfully"})


# user delete ------------------------------------------------------------------------------>
@app.route("/user/delete" , methods = ["DELETE"])
@token_authorization
def user_delete(user_id):

    notes.delete_many({"user_id":user_id})

    user = note_user.delete_one({"user_id":user_id})
    if user.deleted_count == 0:
        return jsonify({"msg": "user not found"})
    
    return jsonify({"msg":'user deleted successefully..'})
# ===========================================================================================================================================
# =========================================================     Note     ====================================================================

# note create ------------------------------------------------------------------------------>
@app.route("/note/create" , methods = ['POST'])
@token_authorization
def notes_creation(user_id):
    data = request.get_json()
    if not data:
        return jsonify({"msg": "invalid request"})

    if not data.get("note_title"):
        return jsonify({"msg": "title required"})

    if not data.get("notes_content"):
        return jsonify({"msg": "content required"})

    create = notes.insert_one({
        "note_id":str(uuid.uuid4()),
        "user_id":user_id,
        "note_title":data.get("note_title"),
        "notes_content":data.get("notes_content"),
        "create_time":datetime.now(),
        "update_time":datetime.now()
    })
    if not create.inserted_id:
        return jsonify({"msg": "creation failed"})
    
    return jsonify({"msg":'notes creation successfullyyy...'})


# user notes  ------------------------------------------------------------------------------------------>
@app.route("/notes/data", methods=["GET"])
@token_authorization
def user_notes(user_id):

    user_notes = list(notes.find({"user_id": user_id}, {"_id": 0}))

    return jsonify(user_notes)


# note id update ------------------------------------------------------------------------------------>
@app.route("/note/update", methods=["PUT"])
@token_authorization
def note_id_update(user_id):
    data = request.get_json()
    if not data:
        return jsonify({"msg": "invalid request"})

    elif not data.get("note_title") and not data.get("notes_content"):
        return jsonify({"msg": "nothing to update"}), 400

    note_id = data.get("note_id")
    if not note_id:
        return jsonify({"msg": "note_id not found"})
    
    note = notes.find_one({"note_id":note_id,"user_id": user_id},{"_id":0})
    if not note :
        return jsonify({"msg":"note not found"})
    
    uptade = notes.update_one(
        {"note_id":note_id},
        {"$set": {
                "user_id": user_id,
                "note_title": data.get("note_title",note["note_title"]),
                "notes_content": data.get("notes_content", note["notes_content"]),
                "create_time": note["create_time"],
                "update_time": datetime.now()
            }}
    )

    if uptade.modified_count == 0 :
        return jsonify({"msg": "no changes made"})

    return jsonify({"msg":"note updated successfully"})


# user delete ------------------------------------------------------------------------------>
@app.route("/note/delete" , methods = ["DELETE"])
@token_authorization
def note_delete(user_id):

    data = request.get_json()
    if not data:
        return jsonify({"msg": "invalid request"})

    note_delete = notes.delete_one({"note_id":data.get("note_id"),"user_id": user_id})
    if note_delete.deleted_count == 0:
        return jsonify({"msg": "notes not found"})
    
    return jsonify({"msg":'note deleted successefully..'})


if __name__ == "__main__":
    app.run(debug=True)


