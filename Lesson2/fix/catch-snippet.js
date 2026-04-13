.catch((error) => {
  console.log("JWT verify failed:", error);
  return callback(null, resp(401, { status: "err", msg: "invalid token" }));
});
