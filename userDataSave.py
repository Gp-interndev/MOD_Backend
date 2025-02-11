from flask import Flask, request, jsonify
import psycopg2
from datetime import datetime
from flask_cors import CORS


app = Flask(__name__)

CORS(app) 

# Database Configuration
DB_HOST = "iwmsgis.pmc.gov.in"
DB_NAME = "MOD"
DB_USER = "postgres"
DB_PASS = "pmc992101"

def get_db_connection():
    """Establish connection to PostgreSQL"""
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

@app.route('/save_user', methods=['POST'])
def save_user():
    """API endpoint to insert user data into PostgreSQL"""
    try:
        data = request.json  # Get JSON input from request
        
        # Extract data from JSON payload
        name = data.get("name")
        mobilenumber = data.get("mobilenumber")
        nameoncertificate = data.get("nameoncertificate")
        gstnumber = data.get("gstnumber") if data.get("gstnumber") else None
        pannumber = data.get("pannumber") if data.get("pannumber") else None
        siteadress = data.get("siteadress")
        gutnumber = data.get("gutnumber") 
        district = data.get("district")
        taluka = data.get("taluka")
        village = data.get("village")
        pincode = data.get("pincode") if data.get("pincode") else None
        correspondanceadress = data.get("correspondanceadress")
        # outwardnumber = data.get("outwardnumber")
        date = datetime.now()  # Store current timestamp

        if not all([name, nameoncertificate, gutnumber, district, taluka, village]):
            return jsonify({"error": "Missing required fields"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # SQL Query to Insert Data
        insert_query = """
        INSERT INTO public.userdata 
        (name, mobilenumber, nameoncertificate, gstnumber, pannumber, siteadress, gutnumber, 
         district, taluka, village, pincode, correspondanceadress,  date) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING outwardnumber
        """
        cursor.execute(insert_query, (name, mobilenumber, nameoncertificate, gstnumber, pannumber, 
                                      siteadress, gutnumber, district, taluka, village, pincode, 
                                      correspondanceadress,  date))

        outwardnumber = cursor.fetchone()[0]
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"message": "User data saved successfully!",
                        "outwardnumber": outwardnumber})

    except psycopg2.Error as e:
        return jsonify({"error": str(e)}), 500
    

@app.route('/get_user/<string:outwardnumber>', methods=['GET'])
def get_user_by_outwardnumber(outwardnumber):
    """API endpoint to retrieve a single user by outwardnumber"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Query with explicit column selection to avoid incorrect mapping
        query = """SELECT outwardnumber, name, mobilenumber, nameoncertificate, gstnumber, 
                   pannumber, siteadress, gutnumber, district, taluka, village, 
                   pincode, correspondanceadress, date FROM userdata WHERE outwardnumber = %s"""
        cursor.execute(query, (outwardnumber,))
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user:
            # Define column names explicitly in the correct order
            columns = ["outwardnumber", "name", "mobilenumber", "nameoncertificate", "gstnumber", 
                       "pannumber", "siteadress", "gutnumber", "district", "taluka", "village", 
                       "pincode", "correspondanceadress", "date"]
 
            user_data = dict(zip(columns, user))  # Convert tuple to dictionary

            return jsonify({"user": user_data}), 200
        else:
            return jsonify({"message": "User not found"}), 404

    except psycopg2.Error as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
