"use strict";

module.exports = {
  env: {
    browser: true,
    commonjs: true,
    es2021: true,
  },
  extends: "eslint:all",
  overrides: [
    {
      env: {
        node: true,
      },
      files: [".eslintrc.{js,cjs}"],
      parserOptions: {
        sourceType: "script",
      },
    },
    {
      extends: ["plugin:cypress/recommended"],
      files: ["cypress/e2e/**/*.{cy,spec}.{js,ts,jsx,tsx}", "cypress/support/**/*.{js,ts,jsx,tsx}"],
      rules: {
        // expect() expression will be marked as errors otherwise.
        "no-unused-expressions": ["off"],
        // Can't enforce camelCase since it conflicts with some python stuff
        camelcase: ["error", { properties: "never" }],
      },
    },
  ],
  parserOptions: {
    ecmaVersion: "latest",
  },
  rules: {
    // Don't force capitalized comments
    "capitalized-comments": ["off"],
    // Only force func names if needed
    "func-names": ["error", "as-needed"],
    // Allow both function declarations and expressions
    "func-style": "off",
    // Exclude some commonly used iterators
    "id-length": ["error", { exceptions: ["i", "j", "k"] }],
    // Disable max-params
    "max-params": "off",
    // Disable max-statements
    "max-statements": "off",
    "max-lines-per-function": ["off"],
    // Enforce separate lines for multiline comments
    "multiline-comment-style": ["error", "separate-lines"],
    // Allow use of "continue"
    "no-continue": "off",
    // Allow magic numbers
    "no-magic-numbers": "off",
    // Disable no-shadow because of upstream bug
    // Allow negated conditions
    "no-negated-condition": "off",
    // https://github.com/typescript-eslint/tslint-to-eslint-config/issues/856
    "no-shadow": "off",
    // Force separate var declaration
    "one-var": ["error", "never"],
    // Disable sorting rules
    "sort-imports": "off",
    "sort-keys": "off",
    "sort-vars": "off",
  },
};
