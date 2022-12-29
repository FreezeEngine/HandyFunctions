class DBEntry:
    pass

class DBWorker:
    def __init__(self, db_name):
        self._db_name = db_name
        self.connection = sqlite3.connect(f'{db_name}.db', check_same_thread=False)
        self.cursor = self.connection.cursor()
        self.check_table_entity()

    def check_table_entity(self):
        if len(self.cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{self._db_name}'").fetchall()) == 0:
            self.cursor.execute(
                "CREATE TABLE subscribers (username text,id int, expires_in int, present real, pre_notified bool, "
                "notified bool, is_admin bool)")
            self.connection.commit()

    def add_subscriber(self, subscriber):
        # username text,id real, expires_in real, present real, pre_notified bool, notified bool, is_admin bool
        if len(self.cursor.execute("SELECT * FROM subscribers WHERE id = " + str(subscriber.id)).fetchall()) > 0:
            return
        self.cursor.execute("INSERT INTO subscribers VALUES ("
                            "'" + str(subscriber.username) + "',"
                            + str(subscriber.id) + ","
                            + str(subscriber.expires_in) + ","
                            + str(subscriber.present) + ","
                            + str(subscriber.notified).lower() + ","
                            + str(subscriber.notified2).lower() + "," + str(subscriber.is_admin).lower() + ")")
        self.connection.commit()
        self.ping_worker.subscribers = self.get_subscribers()

    def update_subscriber(self, subscriber):
        self.cursor.execute("UPDATE subscribers SET "
                            "username = \"" + subscriber.username + "\""
                                                                    ", id = " + str(subscriber.id) +
                            ", expires_in = " + str(subscriber.expires_in) +
                            ", present = " + str(subscriber.present) +
                            ", pre_notified = " + str(subscriber.notified) +
                            ", notified = " + str(subscriber.notified) +
                            ", is_admin = " + str(subscriber.is_admin) + " WHERE id = " + str(subscriber.id))
        self.connection.commit()
        self.ping_worker.subscribers = self.get_subscribers()

    def delete_subscriber(self, id: int):
        self.cursor.execute("DELETE FROM subscribers WHERE id = " + str(id))
        self.connection.commit()
        self.ping_worker.subscribers = self.get_subscribers()

    def get_subscriber_by_id(self, id: int):
        raw_sub = self.cursor.execute("SELECT * FROM subscribers WHERE id = " + str(id)).fetchall()
        if len(raw_sub) > 0:
            #return Subscriber(ping_worker=self.ping_worker, from_db=raw_sub[0])
            pass
        return None

    def get_subscribers(self):
        raw_subs = self.cursor.execute("SELECT * FROM subscribers").fetchall()
        actual_subs = []
        for sub in raw_subs:
            #actual_subs.append(Subscriber(ping_worker=self.ping_worker, from_db=sub))
            pass
        return actual_subs

    def delete_data(self):
        self.cursor.execute("DROP TABLE subscribers")
        self.check_table_entity()
        self.connection.commit()
        self.ping_worker.subscribers = self.get_subscribers()