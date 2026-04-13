const https = require("https");
const jose = require("node-jose");

let jwksCache = {
  keystore: null,
  fetchedAt: 0,
};

function fetchJson(url) {
  return new Promise((resolve, reject) => {
    https
      .get(url, (response) => {
        if (response.statusCode !== 200) {
          reject(new Error(`JWKS request failed with status ${response.statusCode}`));
          response.resume();
          return;
        }

        let body = "";
        response.setEncoding("utf8");
        response.on("data", (chunk) => {
          body += chunk;
        });
        response.on("end", () => {
          try {
            resolve(JSON.parse(body));
          } catch (error) {
            reject(error);
          }
        });
      })
      .on("error", reject);
  });
}

async function getKeyStore(jwksUrl) {
  const cacheAgeMs = 60 * 60 * 1000;
  const cacheIsFresh =
    jwksCache.keystore && Date.now() - jwksCache.fetchedAt < cacheAgeMs;

  if (cacheIsFresh) {
    return jwksCache.keystore;
  }

  const jwks = await fetchJson(jwksUrl);
  jwksCache = {
    keystore: await jose.JWK.asKeyStore(jwks),
    fetchedAt: Date.now(),
  };

  return jwksCache.keystore;
}

async function verifyCognitoJwt(jwt) {
  const region = process.env.AWS_REGION;
  const userPoolId = process.env.userpoolid;

  if (!region || !userPoolId) {
    throw new Error("AWS_REGION and userpoolid must be set");
  }

  const issuer = `https://cognito-idp.${region}.amazonaws.com/${userPoolId}`;
  const jwksUrl = `${issuer}/.well-known/jwks.json`;
  const keystore = await getKeyStore(jwksUrl);

  const result = await jose.JWS.createVerify(keystore).verify(jwt);
  const claims = JSON.parse(result.payload.toString("utf8"));

  if (claims.iss !== issuer) {
    throw new Error("bad issuer");
  }

  return claims;
}

module.exports = { verifyCognitoJwt };
