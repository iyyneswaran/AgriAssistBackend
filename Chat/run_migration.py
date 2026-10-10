import asyncio
from app.db.session import engine
from sqlalchemy import text

async def run():
    async with engine.begin() as conn:
        with open("app/notifications/migrations/001_create_notification_tables.sql", "r") as f:
            sql = f.read()
        
        # Split by semicolon and execute each statement
        statements = sql.split(";")
        for stmt in statements:
            if stmt.strip():
                try:
                    await conn.execute(text(stmt.strip()))
                    print(f"Successfully executed: {stmt.strip()[:50]}...")
                except Exception as e:
                    print(f"Error executing statement: {stmt.strip()[:50]}... \n{e}")

    print("Migration complete!")

if __name__ == "__main__":
    asyncio.run(run())
