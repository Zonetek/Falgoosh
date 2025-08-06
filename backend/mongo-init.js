db = db.getSiblingDB("falgoosh");
db.createUser({
  user: "falgoosh",
  pwd: "V3ryStRoNgP@ssw0rd!",
  roles: [
    {
      role: "readWrite",
      db: "falgoosh"
    }
  ]
});
