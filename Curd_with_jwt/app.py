from flask import Flask,request,jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy import String,Integer,ForeignKey,CheckConstraint,Enum
import jwt
from functools import wraps
from datetime import datetime,timedelta
import enum
import re
# import rsa
# publicKey, privateKey =rsa.newkeys(256)



app=Flask(__name__)
app.config['SECRET_KEY']='This is my secret key'
app.config['SQLALCHEMY_DATABASE_URI']='postgresql://postgres:Admin123@localhost:5432/Addtocart'

db=SQLAlchemy(app)

 
Gender =['male','female','others']

class Customer(db.Model):
    cust_id:Mapped[int]=mapped_column(primary_key=True)
    customer_name:Mapped[str]=mapped_column(String(100),unique=True,nullable=False)
    customer_age:Mapped[int] =mapped_column(CheckConstraint('customer_age>18 AND customer_age<75'))
    customer_gender=db.Column(db.String(6))
    customer_email= db.Column(db.String(50),unique=True,nullable=False)
    customer_password:Mapped[str] =mapped_column(String(300),nullable=False)
    
class Cart(db.Model):
    order_id:Mapped[int] =mapped_column(primary_key=True)
    product_name:Mapped[str]=mapped_column(unique=True,nullable=False)
    quantity:Mapped[int]=mapped_column(CheckConstraint('quantity >0 AND quantity <10'))
    customer_access:Mapped[int] =mapped_column(ForeignKey('customer.cust_id'))

with app.app_context():
    db.create_all()

def token_required(f):
    @wraps(f)
    def decorater(*args, **kwargs):
        token=None
        if 'Authorization' in request.headers:
           token = request.headers['Authorization']
        if token is None:
            return jsonify({"message":"token is missing!!!"})
        else:
            try:
                token =token.split(" ")
                if token[0] == 'Bearer':
                    token =token[1]
                    data= jwt.decode(token,app.config['SECRET_KEY'],algorithms=['HS256'])
                else:
                    raise Exception("No Bearer keyword before token")
            except Exception as E:
                return jsonify({"message": "Invalid token","Error":str(E)})
            
            return f(data['id'],*args,**kwargs)
    return decorater


def validate_name(name):
    name_list = name.split(" ")
    if (len(name_list)==2 and name_list[0].isalpha()==True and name_list[1].isalpha()==True) or (len(name_list)==3 and name_list[0].isalpha()==True and name_list[1].isalpha()==True and name_list[2].isalpha()==True):
        return True
    else:
        return False

def validate_email(email):
    email =email.lower()
    if not re.match(r'^[a-z0-9]+@[a-z]+\.[a-z]{2,3}$',email):
        return False
    else:
        return True

def validate_password(Password):
    if not re.match(r'^(?=.*[0-9])(?=.*[a-z])(?=.*[A-Z])(?=.*[_!@#$%])(?!.* ).{8,16}$',Password):
        return False
    else:
        return True
    
product_list =['wheat','rice','jawar','moong','bajra','black-pepper','table-salt','milk','chocolate','chips','coconut']


@app.route('/register',methods=['POST'])
def register():
    data =request.json
    if data is None:
        return jsonify({
            "message": "No data in JSON"
        })
    elif Customer.query.filter_by(customer_email=data['customer-email']).first():
        return jsonify({"Message": "User already Exists"})
    else:
        if not validate_name(data['customer-name']):
            return jsonify({"Message":"Invalid Name"})
        elif not data['customer-gender'].lower() in Gender:
            return jsonify({"Message":"Invalid gender"})
        elif not validate_email(data['customer-email']):
            return jsonify({"Message":"Invalid email"})
        elif not validate_password(data['customer-password']):
            return jsonify({"message":"Entered password is not as per conditions"},{"conditions":"Password must contain one digit from 1 to 9, one lowercase letter, one uppercase letter, one underscore, no space and it must be 8-16 characters long. Usage of any other special character other than underscore is optional."})
        else:
            # new_customer =Customer(customer_name=data['customer-name'],customer_age=data['customer-age'],customer_gender=data['customer-gender'],customer_email=data['customer-email'],customer_password=rsa.encrypt(data["customer-password"].encode(),publicKey))
            new_customer =Customer(customer_name=data['customer-name'],customer_age=data['customer-age'],customer_gender=data['customer-gender'],customer_email=data['customer-email'],customer_password=data["customer-password"])
            db.session.add(new_customer)
            db.session.commit()
            return jsonify({
                "message":"Record added successfully"
            })
@app.route('/updateCustomer',methods=['PUT'])
@token_required
def updateCustomer(getid):
    if getid is None:
        return jsonify({"message":"no customer at id found"})
    else:
        data=Customer.query.get(getid)
        updateCustomer=request.json
        if not validate_name(updateCustomer['customer-name']):
            return jsonify({"Message":"Invalid Name"})
        elif not updateCustomer['customer-gender'].lower() in Gender:
            return jsonify({"Message":"Invalid gender"})
        elif not validate_password(updateCustomer['customer-password']):
            return jsonify({"message":"Entered password is not as per conditions"},{"conditions":"Password must contain one digit from 1 to 9, one lowercase letter, one uppercase letter, one underscore, no space and it must be 8-16 characters long. Usage of any other special character other than underscore is optional."})
        else:
            data.customer_name=updateCustomer['customer-name']
            data.customer_age=updateCustomer['customer-age']
            data.customer_gender=updateCustomer['customer-gender']
            data.customer_password=updateCustomer['customer-password']
            db.session.commit()
            return jsonify({"message":"Customer record updated successfully"})
        
    

@app.route('/login',methods=['POST'])
def login():
    data=request.json
    if data is None:
        return jsonify({"message":"No credentials provided"})
    customer=Customer.query.filter_by(customer_email=data['user-mail']).first()
    try:
        # if customer and rsa.decrypt(bytes(customer.customer_password, 'utf-8'),privateKey).decode() == data['password']:
        if customer and customer.customer_password == data['password']:
            access_token =jwt.encode({'id':customer.cust_id,"exp":datetime.utcnow()  + timedelta(minutes=15)},app.config['SECRET_KEY'],algorithm='HS256')
            return jsonify({"token": access_token,"expire_time":datetime.now()  + timedelta(minutes=15)})
    except Exception as E:
        return jsonify({"Error-message":str(E),"cust_id":customer.cust_id})
    return jsonify({"message":"Invalid Credentials"})


@app.route('/insertCart',methods=['POST'])
@token_required
def insertCart(getid):
    if getid is None:
        return jsonify({"message":"no id found"})
    else:
        data=request.json
        if data is None:
            return jsonify({"Message":"please enter data for insertion"})
        else:
            if data['product-name'].lower() in product_list:
                new_order =Cart(product_name=data['product-name'].lower(),quantity=data['quantity'],customer_access=getid)
                db.session.add(new_order)
                db.session.commit()
                return jsonify({"message":"order added to cart successfully"})
            else:
                return jsonify({"message":"Product not in available product list","product_list":product_list})
 
@app.route('/updateCart',methods=['PUT'])
@token_required
def updateCart(getid):
    id =request.json['id']
    if getid is None:
        return jsonify({"message":"no id found"})
    else:
        data= Cart.query.get(id)
        if data is None:
            return jsonify({"message": f"no record found at id {id}"})
        if data.customer_access == getid:
            updatedata=request.json
            if updatedata is None:
                return jsonify({"Message":"please enter data for insertion"})
            else:
                if updatedata['product-name'].lower() in product_list:
                    data.product_name=updatedata['product-name'].lower()
                    data.quantity =updatedata['quantity']
                    data.customer_access=getid
                    db.session.commit()
                    return jsonify({"message":"order updated to cart successfully"}) 
                else:
                    return jsonify({"message":"Product not in available product list","product_list":product_list})
        else:
            return jsonify("unauthrized customer")  
        
@app.route('/deleteCart',methods=['DELETE'])
@token_required
def deleteorder(getid):
    id=request.json['id']
    if getid is None:
        return jsonify({"message":"no id found"})
    else:
        data= Cart.query.get(id)
        if data is None:
            return jsonify({"message": f"no record found at id {id}"})
        else:
            if data.customer_access == getid:
                db.session.delete(data)
                db.session.commit()
                return jsonify({"message":f"order deleted at {id} in cart successfully"})  
            else:
                return jsonify("unauthrized customer") 
         

@app.route('/getorder',methods=['GET'])
@token_required
def getorder(getid):
    id=request.form['id']
    if getid is None:
        return jsonify({"message":"no id found"})
    else:
        data= Cart.query.get(id)
        if data.customer_access == getid:
            if data is None:
                return jsonify({"message": f"no record found at id {id}"})
            else:
                order ={
                    "order_id":data.order_id,
                    "product_Name":data.product_name,
                    "Quantity": data.quantity
                }
                return jsonify({"order":order})   
        else:
            return jsonify("unauthrized customer")

@app.route('/showCart',methods=['GET'])
@token_required
def showcart(getid):
    if getid is None:
        return jsonify({"message":"no id found"})
    else:
        cart_data =db.session.query(Cart).filter(Cart.customer_access == getid).all()
        cart_data_list =[
            {
                "order_id":data.order_id,
                "product_Name":data.product_name,
                "Quantity": data.quantity
            } for data in cart_data
        ]

        return jsonify({"cart_orders":cart_data_list})
       



if __name__ == '__main__':
    app.run(debug=True)