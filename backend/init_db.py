from app.main import Base, engine
if __name__=="__main__":
    Base.metadata.create_all(engine)
    print("Database tables created. Development setup only; use Alembic migrations for production.")
