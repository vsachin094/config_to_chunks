from typing import Any, Dict, List, Optional

from pymongo import MongoClient

DEFAULT_DB = "net_config"

class MongoStore:
    def __init__(self, mongo_uri: str, mongo_db: str = DEFAULT_DB, dry_run: bool = False):
        self.dry_run = dry_run
        self.client = None
        self.db = None
        if not dry_run:
            self.client = MongoClient(mongo_uri)
            self.db = self.client[mongo_db]

    def close(self):
        if self.client:
            self.client.close()

    def collection(self, name: str):
        if self.dry_run:
            return None
        return self.db[name]

    def insert_one(self, collection_name: str, doc: Dict[str, Any]):
        if self.dry_run:
            print(f"[DRY-RUN] insert_one into {collection_name}")
            return
        self.collection(collection_name).insert_one(doc)

    def insert_many(self, collection_name: str, docs: List[Dict[str, Any]]):
        if self.dry_run:
            print(f"[DRY-RUN] insert_many into {collection_name} count={len(docs)}")
            return
        if docs:
            self.collection(collection_name).insert_many(docs, ordered=False)

    def update_one(self, collection_name: str, filt: Dict[str, Any], update: Dict[str, Any], upsert: bool = False):
        if self.dry_run:
            print(f"[DRY-RUN] update_one {collection_name} filter={filt}")
            return
        self.collection(collection_name).update_one(filt, update, upsert=upsert)

    def delete_one(self, collection_name: str, filt: Dict[str, Any]):
        if self.dry_run:
            print(f"[DRY-RUN] delete_one from {collection_name} filter={filt}")
            return
        self.collection(collection_name).delete_one(filt)

    def delete_many(self, collection_name: str, filt: Dict[str, Any]):
        if self.dry_run:
            print(f"[DRY-RUN] delete_many from {collection_name} filter={filt}")
            return
        self.collection(collection_name).delete_many(filt)

    def upsert(self, collection_name: str, filt: Dict[str, Any], fields: Dict[str, Any]):
        update = {"$set": fields}
        self.update_one(collection_name, filt, update, upsert=True)
