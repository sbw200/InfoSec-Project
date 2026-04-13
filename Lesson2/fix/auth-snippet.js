const { verifyCognitoJwt } = require("./jwt-verification");

var authHeader = headers.Authorization || headers.authorization || "";
var jwt = authHeader.replace(/^Bearer\s+/i, "").trim();

if (!jwt) {
  return callback(
    null,
    resp(401, { status: "err", msg: "missing authorization" })
  );
}

verifyCognitoJwt(jwt).then((claims) => {
  var user = claims.username || claims["cognito:username"] || claims.sub;

  // Continue with the normal business logic using the verified user identity.
});
