from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
from pymongo.errors import OperationFailure


app = Flask(__name__)
CORS(app)


# ket noi database
def get_mongo_connection(account: str, password: str):
    uri = f"mongodb://{account}:{password}@localhost:27017/cuoiky?authSource=cuoiky"
    client = MongoClient(uri)
    db = client["cuoiky"]
    return db

def get_role():

    account = request.args.get('account')
    password = request.args.get('password')
    db = get_mongo_connection(account, password)
    sach_collection = db["tai_khoan"]

    try:
        tai_khoan = sach_collection.find_one({"_id": account})  # Ẩn _id
        return tai_khoan['role']
    except Exception as e:
        return jsonify({'error': str(e)}), 500



# lấy tất cả sách

@app.route('/get-roles', methods=['GET'])
def get_roles():
    account = request.args.get('account')
    password = request.args.get('password')
    db = get_mongo_connection(account, password)

    try:
        # Sử dụng lệnh command để lấy danh sách roles
        return jsonify(db.command("rolesInfo").get("roles", []))

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/sach', methods=['GET'])
def get_books():
    account = request.args.get('account')
    password = request.args.get('password')
    db = get_mongo_connection(account, password)

    query = db["sach"].find()
    
    try:
        books = list(query)  # Ẩn _id
        return jsonify(books)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Lây danh sách Sach theo thể loại
@app.route('/sach/<type_id>', methods=['GET'])
def get_books_by_tyope(type_id):
    account = request.args.get('account')
    password = request.args.get('password')
    db = get_mongo_connection(account, password)

    query = db["sach"].find({"maTheLoai":type_id})
    
    try:
        books = list(query)  # Ẩn _id
        return jsonify(books)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Lay tat ca tai khoan
@app.route('/taikhoan', methods=['GET'])
def get_accounts():
    account = request.args.get('account')
    password = request.args.get('password')
    db = get_mongo_connection(account, password)
    
    query = db["tai_khoan"].find({})

    try:
        if get_role() == "khach_hang":

            return "unautheticate", 403 
        
        books = list(query)  # Ẩn _id
        return jsonify(books)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
# xem tai khoan ca nhanh
@app.route('/xem-tai-khoan', methods=['GET'])
def get_account():
    account = request.args.get('account')
    password = request.args.get('password')

    if not account or not password:
        return jsonify({'error': 'Thiếu account hoặc password'}), 400

    try:
        db = get_mongo_connection(account, password)
        query = db["tai_khoan"].find_one({"_id": account})


        # Tìm tài khoản theo số điện thoại
        tai_khoan_data = query

        if tai_khoan_data:
            return jsonify(tai_khoan_data)
        else:
            return jsonify({'error': 'Không tìm thấy tài khoản này'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    
# lay tat ca phieu muon
@app.route('/phieumuon', methods=['GET'])
def ds_phieu_muon():
    account = request.args.get('account')
    password = request.args.get('password')
    db = get_mongo_connection(account, password)

    try:
        if get_role() == "khach_hang":
            return "unauthenticate", 403

        result = db["phieu_muon"].aggregate([
            {
                "$lookup": {
                    "from": "chi_tiet_phieu_muon",
                    "localField": "_id",
                    "foreignField": "maPhieuMuon",
                    "as": "chiTietPhieu"
                }
            },
            {
                "$unwind": "$chiTietPhieu"  # chuyển từ array thành object
            }
        ])

        books = list(result)
        return jsonify(books)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/phieumuon/<id>', methods=['GET'])
def phieu_muon(id):
    account = request.args.get('account')
    password = request.args.get('password')
    db = get_mongo_connection(account, password)

    try:
        if get_role() == "khach_hang":
            return "unauthenticate", 403

        result = db["phieu_muon"].aggregate([
            {
                "$match": {
                    "_id": id
                }
            },
            {
                "$lookup": {
                    "from": "chi_tiet_phieu_muon",
                    "localField": "_id",
                    "foreignField": "maPhieuMuon",
                    "as": "chiTietPhieu"
                }
            },
            {
                "$unwind": "$chiTietPhieu"  # chuyển từ array thành object
            }
        ])

        result_list = list(result)
        if result_list:
            return jsonify(result_list[0])
        else:
            return jsonify({"message": "Không tìm thấy phiếu mượn"}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/xem-phieu-muon-kh/<ma_tai_khoan>', methods=['GET'])
def xem_phieu_muo_KH(ma_tai_khoan):
    account = request.args.get('account')
    password = request.args.get('password')
    db = get_mongo_connection(account, password)

    try:
        result = db["phieu_muon"].aggregate([
            { "$match": { "maTaiKhoan": ma_tai_khoan } },
            {
                "$lookup": {
                    "from": "chi_tiet_phieu_muon",
                    "localField": "_id",
                    "foreignField": "maPhieuMuon",
                    "as": "chiTietPhieuMuon"
                }
            },
            { "$unwind": "$chiTietPhieuMuon" }  # nếu chắc chắn mỗi phiếu chỉ có 1 chi tiết
        ])

        data = list(result)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# xem phieu muon ca nhan
@app.route('/xem-phieu-muon', methods=['GET'])
def xem_phieu_muon():
    account = request.args.get('account')
    password = request.args.get('password')
    db = get_mongo_connection(account, password)

    try:
        result = db["phieu_muon"].aggregate([
            { "$match": { "maTaiKhoan": account } },
            {
                "$lookup": {
                    "from": "chi_tiet_phieu_muon",
                    "localField": "_id",
                    "foreignField": "maPhieuMuon",
                    "as": "chiTietPhieuMuon"
                }
            },
            { "$unwind": "$chiTietPhieuMuon" }
        ])

        data = list(result)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


    
# them sach
@app.route('/them-sach', methods=['POST'])
def add_book():

    account = request.args.get('account')
    password = request.args.get('password')

    # du lieu JSON
    book_data = request.get_json()

    # kiem tra
    if not book_data:
        return jsonify({'error': 'data invalid!'}), 400

    # Kết nối đến MongoDB
    try:
        db = get_mongo_connection(account, password)

        # Chèn sách vào MongoDB
        result = db["sach"].insert_one(book_data)

        # Trả về thông báo thành công cùng với _id của sách mới
        return jsonify({'message': 'Sách đã được thêm thành công', 'bookId': result.inserted_id}), 201

    except Exception as e:
        # Xử lý lỗi
        return jsonify({'error': str(e)}), 500

@app.route('/cap-nhat-sach/<string:book_id>', methods=['PUT'])
def update_book(book_id):
    account = request.args.get('account')
    password = request.args.get('password')

    book_data = request.get_json()

    if not book_data:
        return jsonify({'error': 'Dữ liệu sách không hợp lệ'}), 400

    # Kết nối đến MongoDB
    try:
        db = get_mongo_connection(account, password)

        result = db["sach"].update_one(
            {"_id": book_id},  # Điều kiện tìm sách
            {"$set": book_data}  # Cập nhật dữ liệu
        )

        # Kiểm tra nếu không có sách nào được cập nhật
        if result.matched_count == 0:
            return jsonify({'message': 'Không tìm thấy sách để cập nhật'}), 404

        # Trả về thông báo thành công
        return jsonify({'message': 'Sách đã được cập nhật thành công'}), 200

    except Exception as e:
        # Xử lý lỗi
        return jsonify({'error': str(e)}), 500
    

    

@app.route('/xoa-sach/<book_id>', methods=['DELETE'])
def delete_book(book_id):
    account = request.args.get('account')
    password = request.args.get('password')

    try:
        db = get_mongo_connection(account, password)

        # Tìm và xóa sách theo book_id
        result = db["sach"].delete_one({"_id": book_id})

        # Kiểm tra nếu sách có tồn tại và bị xóa
        if result.deleted_count == 1:
            return jsonify({"message": "Sách đã được xóa thành công"}), 200
        else:
            return jsonify({"error": "Không tìm thấy sách với ID này"}), 404

    except Exception as e:
        # Xử lý lỗi
        return jsonify({'error': str(e)}), 500

@app.route('/cap-nhat-the-loai/<string:id>', methods=['PUT'])
def update_type(id):
    account = request.args.get('account')
    password = request.args.get('password')

    data = request.get_json()

    if not data:
        return jsonify({'error': 'Dữ liệu sách không hợp lệ'}), 400

    # Kết nối đến MongoDB
    try:
        db = get_mongo_connection(account, password)

        result = db["the_loai"].update_one(
            {"_id": id},  # Điều kiện tìm sách
            {"$set": data}  # Cập nhật dữ liệu
        )

        # Kiểm tra nếu không có sách nào được cập nhật
        if result.matched_count == 0:
            return jsonify({'message': 'Không tìm thấy sách để cập nhật'}), 404

        # Trả về thông báo thành công
        return jsonify({'message': 'Sách đã được cập nhật thành công'}), 200

    except Exception as e:
        # Xử lý lỗi
        return jsonify({'error': str(e)}), 500

@app.route('/xoa-the-loai/<id>', methods=['DELETE'])
def delete_type(id):
    account = request.args.get('account')
    password = request.args.get('password')

    # Kết nối đến MongoDB
    try:
        db = get_mongo_connection(account, password)

        # Tìm và xóa sách theo id
        result = db["the_loai"].delete_one({"_id": id})

        # Kiểm tra nếu sách có tồn tại và bị xóa
        if result.deleted_count == 1:
            return jsonify({"message": "Sách đã được xóa thành công"}), 200
        else:
            return jsonify({"error": "Không tìm thấy sách với ID này"}), 404

    except Exception as e:
        # Xử lý lỗi
        return jsonify({'error': str(e)}), 500


@app.route('/them-the-loai', methods=['POST'])
def them_the_loai():

    account = request.args.get('account')
    password = request.args.get('password')

    # du lieu JSON
    data = request.get_json()

    # kiem tra
    if not data:
        return jsonify({'error': 'data invalid!'}), 400

    # Kết nối đến MongoDB
    try:
        db = get_mongo_connection(account, password)

        # Chèn sách vào MongoDB
        result = db["the_loai"].insert_one(data)

        # Trả về thông báo thành công cùng với _id của sách mới
        return jsonify({'message': 'Thêm thành công', 'bookId': result.inserted_id}), 201

    except Exception as e:
        # Xử lý lỗi
        return jsonify({'error': str(e)}), 500

from datetime import datetime


@app.route('/them-taikhoan', methods=['POST'])
def add_account():
    account = request.args.get('account')
    password = request.args.get('password')

    account_data = request.get_json()

    # Kiểm tra nếu thiếu dữ liệu tài khoản
    if not account_data:
        return jsonify({'error': 'Dữ liệu tài khoản không hợp lệ'}), 400

    # Xử lý trường 'ngaySinh', chuyển đổi từ chuỗi thành Date
    if 'ngaySinh' in account_data:
        try:
            # Chuyển đổi 'ngaySinh' từ chuỗi (YYYY-MM-DD) sang kiểu Date
            account_data['ngaySinh'] = datetime.strptime(account_data['ngaySinh'], "%Y-%m-%d")
        except ValueError:
            return jsonify({'error': 'Ngày sinh không hợp lệ. Vui lòng nhập theo định dạng YYYY-MM-DD'}), 400

    # Tạo _id kiểu string (ví dụ: TK001, TK002, ...)
    account_data['_id'] = "TK" + str(int(datetime.now().timestamp()))  # Tạo _id duy nhất bằng cách dùng timestamp

    # Kết nối đến MongoDB
    try:
        db = get_mongo_connection(account, password)

        # Chèn tài khoản vào MongoDB
        db["tai_khoan"].insert_one(account_data)

        try:
            create_user(account_data['_id'], account_data['matKhau'], account_data['role'], account)
        except Exception as e:
            return "loi"
        return jsonify({'message': 'Tài khoản đã được thêm thành công', 'accountId': account_data['_id']}), 201

    except Exception as e:
        # Xử lý lỗi
        return jsonify({'error': str(e)}), 500



def create_user(username, password, role, creater):

    uri = f"mongodb://admin1:admin1@localhost:27017/cuoiky?authSource=cuoiky"
    client = MongoClient(uri)
    db = client["cuoiky"]

    try:
        role1 = db.command("usersInfo", {"user": creater, "db": "cuoiky"}).get("users", [])[0].get("roles", [])[0].get("role", None)
        if(role1 == role):
            return "unautheticate", 403 
        db.command({
            "createUser": username,
            "pwd": password,
            "roles": [
                {
                    "role": role,
                    "db": "cuoiky"
                }
            ]
        })
    except Exception as e:
        print(f"Đã có lỗi xảy ra: {str(e)}")

    


@app.route('/xoa-taikhoan/<id>', methods=['DELETE'])
def delete_account(id):
    account = request.args.get('account')
    password = request.args.get('password')


    try:
        # Kết nối tới MongoDB
        db = get_mongo_connection(account, password)

        # Xóa tài khoản theo _id
        result = db["tai_khoan"].delete_one({"_id": id})

        # Kiểm tra nếu không tìm thấy tài khoản
        if result.deleted_count == 0:
            return jsonify({'error': 'Không tìm thấy tài khoản cần xóa'}), 404

        try:
            delete_user(account)
        except Exception as e:
            # Log lỗi chi tiết
            return jsonify({'error': f'Lỗi khi xóa người dùng: {str(e)}'}), 500

        # Nếu xóa thành công
        return jsonify({'message': 'Tài khoản đã được xóa thành công'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def delete_user(username):
    uri = "mongodb://admin1:admin1@localhost:27017/cuoiky?authSource=cuoiky"
    client = MongoClient(uri)
    db = client["cuoiky"]

    try:
        # Xóa người dùng trong MongoDB authentication system
        db.command({
            "dropUser": username
        })
    except Exception as e:
        # Log lỗi chi tiết
        print(f"Error when deleting user: {str(e)}")
        raise Exception("Failed to delete user from MongoDB authentication system.")



if __name__ == '__main__':
    app.run(debug=True)
