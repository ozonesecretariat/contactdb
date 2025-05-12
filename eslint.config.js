import globals from "globals";
import pluginVue from "eslint-plugin-vue";
import { defineConfigWithVueTs, vueTsConfigs } from "@vue/eslint-config-typescript";
import pluginCypress from "eslint-plugin-cypress/flat";
import prettierSkipFormatting from "@vue/eslint-config-prettier/skip-formatting";
import pluginJs from "@eslint/js";
import pluginPrettier from "eslint-config-prettier";
import pluginQuasar from "@quasar/app-vite/eslint";

export default defineConfigWithVueTs([
  {
    name: "app/files-to-lint",
    files: ["**/*.{ts,mts,tsx,js,mjs,cjs}"],
  },
  {
    name: "app/files-to-ignore",
    ignores: ["**/dist/**", "**/dist-ssr/**", "**/coverage/**", "**/node_modules/**", "**/.fs/**", "**/.venv/**"],
  },
  pluginQuasar.configs.recommended(),
  pluginJs.configs.all,
  pluginVue.configs["flat/recommended"],
  {
    files: ["**/*.ts", "**/*.vue"],
    rules: {
      "@typescript-eslint/consistent-type-imports": ["error", { prefer: "type-imports" }],
    },
  },
  // https://github.com/vuejs/eslint-config-typescript
  vueTsConfigs.recommendedTypeChecked,
  {
    ...pluginCypress.configs.recommended,
    files: ["cypress/e2e/**/*.{cy,spec}.{js,ts,jsx,tsx}", "cypress/support/**/*.{js,ts,jsx,tsx}"],
    rules: {
      // expect() expression will be marked as errors otherwise.
      "@typescript-eslint/no-unused-expressions": ["off"],
      "no-unused-expressions": ["off"],
      // Can't enforce camelCase since it conflicts with some python stuff
      camelcase: ["error", { properties: "never" }],
    },
  },
  {
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",

      globals: {
        ...globals.browser,
        ...globals.node, // SSR, Electron, config files
        process: "readonly", // process.env.*
        ga: "readonly", // Google Analytics
        cordova: "readonly",
        Capacitor: "readonly",
        chrome: "readonly", // BEX related
        browser: "readonly", // BEX related
      },
    },

    // add your custom rules here
    rules: {
      // Make component names consistent
      "vue/component-name-in-template-casing": ["error", "kebab-case", { registeredComponentsOnly: false }],
      // Allow promises not being waited on always.
      "@typescript-eslint/no-floating-promises": "off",
      // Don't force capitalized comments
      "capitalized-comments": "off",
      // Allow class methods that could be static
      "class-methods-use-this": "off",
      // Only force func names if needed
      "func-names": ["error", "as-needed"],
      // Allow both function declarations and expressions
      "func-style": "off",
      // Allow short id names
      "id-length": "off",
      // Disable max-params
      "max-params": "off",
      // Disable max-statements
      "max-statements": "off",
      "max-lines": "off",
      "max-lines-per-function": "off",
      // Enforce separate lines for multiline comments
      "multiline-comment-style": ["error", "separate-lines"],
      // Allow use of "continue"
      "no-continue": "off",
      // Allow inline comments,
      "no-inline-comments": "off",
      // Allow magic numbers
      "no-magic-numbers": "off",
      // Allow negated conditions
      "no-negated-condition": "off",
      // The @typescript-eslint/no-unused-vars will catch any such errors without
      // any false positives, so disable this rule.
      "no-useless-assignment": "off",
      // Allow using function before defining them
      "no-use-before-define": ["error", { functions: false }],
      // Allow underscore dangle
      "no-underscore-dangle": "off",
      // Allow ternary
      "no-ternary": "off",
      // Allow warning comments
      "no-warning-comments": "off",
      // Force separate var declaration
      "one-var": ["error", "never"],
      // Disable destructing preference
      "prefer-destructuring": "off",
      // Disable sorting rules
      "sort-imports": "off",
      "sort-keys": "off",
      "sort-vars": "off",
    },
  },
  prettierSkipFormatting,
  pluginPrettier,
]);
