from app.database.session import SessionLocal
from app.tools.search_hcp import search_hcp

db = SessionLocal()

try:

    result = search_hcp(
        db=db,
        doctor_name="Rajesh",
    )

    print(result)

finally:
    db.close()