import asyncio
import asyncpg

async def main():
    try:
        sys_conn = await asyncpg.connect(user="postgres", password="password", host="127.0.0.1", database="postgres")
        print("Connected as postgres:password to postgres db")
        await sys_conn.close()
    except Exception as e:
        print("Error with postgres/password:", e)
        
    try:
        sys_conn = await asyncpg.connect(user="postgres", password="postgres", host="127.0.0.1", database="postgres")
        print("Connected as postgres:postgres to postgres db")
        await sys_conn.close()
    except Exception as e:
        print("Error with postgres/postgres:", e)
        
    try:
        sys_conn = await asyncpg.connect(user="postgres", password="", host="127.0.0.1", database="postgres")
        print("Connected as postgres:'' to postgres db")
        await sys_conn.close()
    except Exception as e:
        print("Error with postgres/empty:", e)

if __name__ == "__main__":
    asyncio.run(main())
