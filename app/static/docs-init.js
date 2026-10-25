"use strict";
window.addEventListener("DOMContentLoaded", function () {
  window.ui = SwaggerUIBundle({
    url: "/openapi.json",
    dom_id: "#swagger-ui",
    deepLinking: false,
    persistAuthorization: false,
    validatorUrl: null,
    supportedSubmitMethods: ["get", "post"],
    displayRequestDuration: true,
    presets: [SwaggerUIBundle.presets.apis],
    layout: "BaseLayout"
  });
});
