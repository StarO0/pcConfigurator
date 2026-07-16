import psycopg2

def main():
    try:
        conn = psycopg2.connect("postgresql://postgres:password@127.0.0.1:5432/postgres")
        print("Connected with postgres/password")
        conn.close()
    except Exception as e:
        print("postgres/password failed:", e)

    try:
        conn = psycopg2.connect("postgresql://postgres:postgres@127.0.0.1:5432/postgres")
        print("Connected with postgres/postgres")
        conn.close()
    except Exception as e:
        print("postgres/postgres failed:", e)

    try:
        conn = psycopg2.connect("postgresql://pcbuilder:pcbuilder@127.0.0.1:5432/pcbuilder")
        print("Connected with pcbuilder/pcbuilder")
        conn.close()
    except Exception as e:
        print("pcbuilder/pcbuilder failed:", e)

if __name__ == "__main__":
    main()
