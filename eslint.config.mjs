import js from "@eslint/js";
import globals from "globals";
import jsdoc from "eslint-plugin-jsdoc";

export default [
  js.configs.recommended,
  {
    files: ['pyfahviewer/static/*.js'],
    languageOptions: {
      ecmaVersion: 9,
      globals: {
        ...globals.browser,
      }
    },
    plugins: {
      jsdoc: jsdoc
    },
    rules: {
      "no-console": ["off"],
      curly: ["error", "all"],
      "default-case": ["error"],
      "no-eval": ["error"],
      "no-multi-spaces": [
        "warn",
        {
          ignoreEOLComments: true,
          exceptions: {
            Property: true,
            VariableDeclarator: true,
            ImportDeclaration: true
          }
        }
      ],
      "no-shadow": ["error"],
      "no-undefined": ["error"],

      "array-bracket-spacing": ["warn", "never"],
      "block-spacing": ["warn", "always"],
      "brace-style": ["warn", "1tbs"],
      camelcase: ["warn", {properties: "always"}],
      "comma-spacing": [
        "warn",
        {
          before: false,
          after: true
        }
      ],
      "comma-style": ["warn", "last"],
      indent: ["warn", 2, {SwitchCase: 1}],
      "new-cap": [
        "warn",
        {
          newIsCap: true,
          capIsNew: true,
          properties: false
        }
      ],
      "no-mixed-spaces-and-tabs": ["warn", "smart-tabs"],
      "no-multiple-empty-lines": ["warn"],
      "no-nested-ternary": ["warn"],
      "no-spaced-func": ["warn"],
      "no-trailing-spaces": ["warn"],
      semi: ["warn", "always"],
      "space-in-parens": ["warn", "never"],
      "space-infix-ops": ["warn"],
      "spaced-comment": [
        "warn",
        "always",
        {
          block:
          {
            exceptions: ["*"]
          }
        }
      ],
      "jsdoc/require-jsdoc": [
        "error",
        {
          require: {
            FunctionDeclaration: true,
            MethodDefinition: true,
            ClassDeclaration: false
          }
        }
      ],
      "jsdoc/require-returns": ["error"],
      "jsdoc/require-returns-type": ["error"],
      "jsdoc/require-returns-description": ["error"],
      "jsdoc/require-returns-check": ["error"],
      "jsdoc/require-param": ["error"],
      "jsdoc/require-param-description": ["error"],
      "jsdoc/require-param-type": ["error"],
      "jsdoc/check-param-names": ["error"],
      "jsdoc/valid-types": ["error"],
      "jsdoc/require-param-name": ["error"],
    }
  }
];
