def create_medspacy_demo_db(drop_existing=True):
    import os
    if drop_existing and os.path.exists("medspacy_demo.db"):
        print("File medspacy_demo.db already exists")
        return
    
    with open("./discharge_summary.txt") as f:
        text = f.read()

    import sqlite3 as s3

    texts = [
        text,
        "There is no evidence of pneumonia."
    ]

    conn = s3.connect("medspacy_demo.db")

    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS texts;")
    cursor.execute("CREATE TABLE texts (text_id INTEGER PRIMARY KEY, text NOT NULL);")

    for text in texts:
        cursor.execute("INSERT INTO texts (text) VALUES (?)", (text,))
    conn.commit()
    conn.close()
    print("Created file medspacy_demo.db")