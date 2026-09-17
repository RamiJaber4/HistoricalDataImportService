from queue_manager import queue
from db_manager import db
from pydantic import BaseModel
import json

import logging

logger = logging.getLogger(__name__)




async def process_queue():
    while True:

        track_id, data , filename= await queue.get()
        valid_counter, invalid_counter,total_rows =0,0,0
        valid_data = []
        tracked_valid_data= []
        invalid_data = []

        try:
            for item in data:
                total_rows+=1
                row_number = item["row_number"]
                row = item["data"]
                
                recipient = row.get("recipient_name")
                address = row.get("address")
                status = row.get("status")
                
                errors = []
                if not recipient:
                    errors.append({"field": "recipient_name", "message": "required field missing"})
                if not address:
                    errors.append({"field": "address", "message": "required field missing"})
                if not status:
                    errors.append({"field": "status", "message": "required field missing"})

                if errors:
                    invalid_counter+=1

                    invalid_data.append({
                        "track_id": track_id,
                        "row_number": row_number,
                        "raw_row": row,
                        "errors": errors
                    })

                else:
                    valid_counter+=1
                    tracked_valid_data.append({
                        "track_id": track_id,
                        "row": row
                    })
                    valid_data.append({"row":row})

            # Insert all valid rows at once
            if valid_data:
                db.upload_valid_data(valid_data)

            # Insert all invalid rows at once
            if invalid_data:
                db.upload_invalid_data(invalid_data)

            db.upload_imports(track_id, valid_counter, invalid_counter, total_rows, filename)
        except Exception as e:
            print(f"Error processing file {track_id}: {e}")

        finally:
            queue.task_done()