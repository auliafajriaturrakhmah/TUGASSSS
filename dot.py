cursor.execute("SELECT * FROM rumah123_housing_data WHERE price_idr <= %s AND location LIKE %s LIMIT 10", (harga,daerah,))
        row_headers1 = [x[0] for x in cursor.description]
        records = cursor.fetchall()
        total_rumah = len(records)
        cursor.close()